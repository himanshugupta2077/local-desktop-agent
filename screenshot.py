"""
screenshot.py
=============

Capture the current desktop and save it as screenshot.png

Arch Linux:
- X11: works with pyautogui
- Wayland: use grim instead
"""

from pathlib import Path
import subprocess
import time


def capture_screen():

    subprocess.run(
        [
            "qdbus6",
            "org.kde.Spectacle",
            "/",
            "org.kde.Spectacle.FullScreen",
            "false",
        ],
        check=True,
    )

    time.sleep(1)

    screenshots_dir = Path.home() / "Pictures" / "Screenshots"

    latest = max(
        screenshots_dir.glob("Screenshot_*.png"),
        key=lambda p: p.stat().st_mtime,
    )

    return str(latest)


if __name__ == "__main__":
    print(capture_screen())