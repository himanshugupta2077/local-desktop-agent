"""
agent.py
========

Flow:

Screenshot
    ↓
OmniParser CLI
    ↓
elements.json
    ↓
Gemini Vision
    ↓
Planner
    ↓
Executor

Single-action version.
"""

import json
import time
import subprocess
from pathlib import Path

from PIL import Image

from screenshot import capture_screen
from planner import plan_next_action
from executor import execute
from vision import analyze_screenshot

from debug_stats import snapshot

GOAL = input("Goal: ")


def parse_screen(image_path: str):
    """
    Run OmniParser CLI and return parsed elements.
    """

    subprocess.run(
        [
            "python",
            "omniparse_cli.py",
            image_path,
        ],
        check=True,
    )

    runs_dir = Path(
        "omniparser_runs"
    )

    latest_run = max(
        runs_dir.iterdir(),
        key=lambda p: p.stat().st_mtime,
    )

    json_file = (
        latest_run
        / "elements.json"
    )

    elements = json.loads(
        json_file.read_text(
            encoding="utf-8"
        )
    )

    return elements


def main():

    # snapshot("before_run")

    ARM_DELAY = 5

    print(
        "\n[1/5] Capturing screenshot..."
    )

    print(
        f"\nStarting in "
        f"{ARM_DELAY} seconds..."
    )

    for i in range(
        ARM_DELAY,
        0,
        -1,
    ):
        print(f"{i}...")
        time.sleep(1)

    print("Capturing now...")

    screenshot_path = (
        capture_screen()
    )

    img = Image.open(
        screenshot_path
    )

    print(
        f"\nScreenshot Size: "
        f"{img.size[0]}x{img.size[1]}"
    )

    print(
        "\n[2/5] Parsing screen...\n"
    )

    elements = parse_screen(
        screenshot_path
    )

    print(
        f"Found "
        f"{len(elements)} elements"
    )

    # snapshot("after_omniparser")

    print(
        "\n[3/5] Running Gemini vision...\n"
    )

    vision_analysis = (
        analyze_screenshot(
            screenshot_path
        )
    )

    print(
        "\n=== GEMINI VISION ==="
    )
    print(vision_analysis)
    print(
        "=====================\n"
    )

    print(
        "\n[4/5] Planning action..."
    )

    action = plan_next_action(
        goal=GOAL,
        elements=elements,
        vision_analysis=vision_analysis,
    )

    print(
        "\nPlanner Output:"
    )

    print(
        json.dumps(
            action,
            indent=2,
        )
    )

    print(
        "\n[5/5] Executing action..."
    )

    execute(
        action=action,
        elements=elements,
    )

    print("\nDone.")

    # snapshot("after_run")


if __name__ == "__main__":
    main()