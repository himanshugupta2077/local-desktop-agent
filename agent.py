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
Planner
    ↓
Executor

Single-action version.
"""

import json
import subprocess
from pathlib import Path

from screenshot import capture_screen
from planner import plan_next_action
from executor import execute

from PIL import Image

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

    runs_dir = Path("omniparser_runs")

    latest_run = max(
        runs_dir.iterdir(),
        key=lambda p: p.stat().st_mtime
    )

    json_file = latest_run / "elements.json"

    elements = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    return elements


def main():

    print("\n[1/4] Capturing screenshot...")
    screenshot_path = capture_screen()

    img = Image.open(screenshot_path)

    # print("\nScreenshot Size:")
    # print(img.size)

    print("[2/4] Parsing screen...")
    elements = parse_screen(screenshot_path)

    print(f"Found {len(elements)} elements")

    # print("\nDetected Elements:")
    # print("-" * 80)

    # for elem in elements:

    #     element_id = elem.get("id", "?")
    #     element_type = elem.get("type", "unknown")
    #     element_name = elem.get("name", "")

        # print(
        #     f"[{element_id:>3}] "
        #     f"{element_type:<10} "
        #     f"{element_name}"
        # )

    # print("-" * 80)

    print("\n[3/4] Planning action...")

    action = plan_next_action(
        goal=GOAL,
        elements=elements,
    )

    print("\nPlanner Output:")
    print(json.dumps(action, indent=2))

    print("\n[4/4] Executing action...")

    execute(
        action=action,
        elements=elements,
    )

    print("\nDone.")


if __name__ == "__main__":
    main()