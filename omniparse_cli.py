#!/usr/bin/env python3
"""
omniparse_cli.py

Simple CLI to send an image to a running OmniParser gradio server (/process
endpoint), then save the labeled output image and parsed screen elements
into a timestamped output directory.

Usage:
    python omniparse_cli.py path/to/image.png
    python omniparse_cli.py path/to/image.png --server http://127.0.0.1:7861
    python omniparse_cli.py path/to/image.png --box-threshold 0.05 --iou-threshold 0.1 --imgsz 640 --no-paddleocr
"""

import argparse
import ast
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from gradio_client import Client, handle_file
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(description="OmniParser CLI client")
    parser.add_argument("image", help="Path to the input image")
    parser.add_argument("--server", default="http://127.0.0.1:7861",
                         help="OmniParser gradio server URL (default: http://127.0.0.1:7861)")
    parser.add_argument("--output-dir", default="omniparser_runs",
                         help="Base directory under which timestamped run folders are created (default: omniparser_runs)")
    parser.add_argument("--box-threshold", type=float, default=0.05)
    parser.add_argument("--iou-threshold", type=float, default=0.1)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--no-paddleocr", action="store_true",
                         help="Disable PaddleOCR (use_paddleocr=False)")
    return parser.parse_args()


def parse_elements(parsed_text, image_width, image_height):
    """
    Parse OmniParser's raw text output (lines like:
        icon 0: {'type': 'icon', 'bbox': [x1, y1, x2, y2], 'content': 'Back', ...}
    ) into a list of structured dicts with id, name, type, bbox, center,
    and pixel_center (bbox/center are normalized 0-1; pixel_center is in
    actual image pixels).
    """
    elements = []
    line_pattern = re.compile(r"^icon\s+(\d+):\s*(.*)$")

    for line in parsed_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        match = line_pattern.match(line)
        if not match:
            continue

        idx_str, payload_str = match.groups()

        try:
            data = ast.literal_eval(payload_str)
        except (ValueError, SyntaxError):
            # Fall back to raw string if it isn't a parseable literal
            data = {"content": payload_str, "type": "unknown", "bbox": []}

        if not isinstance(data, dict):
            data = {"content": str(data), "type": "unknown", "bbox": []}

        bbox = data.get("bbox", []) or []
        center = None
        pixel_center = None

        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            center = [round(cx, 4), round(cy, 4)]
            pixel_center = [round(cx * image_width), round(cy * image_height)]

        elements.append({
            "id": int(idx_str),
            "name": data.get("content", "") or "",
            "type": data.get("type", "unknown"),
            "bbox": list(bbox),
            "center": center,
            "pixel_center": pixel_center,
        })

    return elements


def main():
    args = parse_args()

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.is_file():
        print(f"Error: image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.output_dir).expanduser().resolve() / f"{timestamp}_{image_path.stem}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[+] Connecting to OmniParser server at {args.server}")
    client = Client(args.server)

    print(f"[+] Submitting image: {image_path}")
    result = client.predict(
        image_input=handle_file(str(image_path)),
        box_threshold=args.box_threshold,
        iou_threshold=args.iou_threshold,
        use_paddleocr=not args.no_paddleocr,
        imgsz=args.imgsz,
        api_name="/process",
    )

    output_image_path, parsed_text = result

    # Save the labeled output image
    out_image_dest = run_dir / f"labeled{Path(output_image_path).suffix or '.png'}"
    shutil.copy(output_image_path, out_image_dest)

    # Save the parsed screen elements text (raw)
    out_text_dest = run_dir / "parsed_elements.txt"
    out_text_dest.write_text(parsed_text, encoding="utf-8")

    # Parse into structured JSON (id, name, type, bbox, center, pixel_center)
    with Image.open(image_path) as img:
        image_width, image_height = img.size

    elements = parse_elements(parsed_text, image_width, image_height)
    out_json_dest = run_dir / "elements.json"
    out_json_dest.write_text(json.dumps(elements, indent=2), encoding="utf-8")

    # Keep a copy of the original input image for reference
    shutil.copy(image_path, run_dir / f"input{image_path.suffix}")

    print(f"[+] Done. Results saved to: {run_dir}")
    print(f"    - Labeled image: {out_image_dest}")
    print(f"    - Parsed elements (raw): {out_text_dest}")
    print(f"    - Parsed elements (json): {out_json_dest}")


if __name__ == "__main__":
    main()