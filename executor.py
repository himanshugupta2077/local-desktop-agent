import pyautogui

# TEMPORARY FOR DEBUGGING
# Disable corner failsafe while testing.
# Remove later if desired.
pyautogui.FAILSAFE = False


def execute(action, elements):

    print("\n=== EXECUTOR ===")
    print("Action:")
    print(action)

    action_type = action.get("action")

    if action_type == "click":

        target_id = action.get("target_id")

        target = next(
            (
                e
                for e in elements
                if e["id"] == target_id
            ),
            None,
        )

        if target is None:
            print(f"ERROR: target_id {target_id} not found")
            return

        print("\nTarget Element:")
        print(target)

        pixel_center = target.get("pixel_center")

        if not pixel_center:
            print("ERROR: pixel_center missing")
            return

        x, y = pixel_center

        screen_w, screen_h = pyautogui.size()

        print("\nScreen Size:")
        print(f"{screen_w} x {screen_h}")

        print("\nTarget Coordinates:")
        print(f"x={x}, y={y}")

        if x < 0 or x > screen_w:
            print("WARNING: x outside screen bounds")

        if y < 0 or y > screen_h:
            print("WARNING: y outside screen bounds")

        current_x, current_y = pyautogui.position()

        print("\nCurrent Mouse Position:")
        print(f"{current_x}, {current_y}")

        print("\nMoving mouse...")

        pyautogui.moveTo(
            x,
            y,
            duration=0.5,
        )

        pyautogui.moveTo(x, y, duration=1)

        real_x, real_y = pyautogui.position()

        print(f"Requested: {x}, {y}")
        print(f"Actual:    {real_x}, {real_y}")

        print("Clicking...")

        pyautogui.click(
            x,
            y,
        )

        print("Done.")

    elif action_type == "keypress":

        key = action.get("key")

        print(f"Pressing key: {key}")

        pyautogui.press(key)

    elif action_type == "hotkey":

        keys = action.get("keys", [])

        print(f"Pressing hotkey: {keys}")

        pyautogui.hotkey(*keys)

    elif action_type == "type":

        text = action.get("text", "")

        print(f"Typing: {text}")

        pyautogui.write(
            text,
            interval=0.02,
        )

    else:

        print(
            f"Unknown action type: "
            f"{action_type}"
        )


if __name__ == "__main__":

    test_action = {
        "action": "click",
        "target_id": 1,
    }

    test_elements = [
        {
            "id": 1,
            "pixel_center": [500, 500],
            "name": "Test Button",
            "type": "button",
        }
    ]

    execute(
        test_action,
        test_elements,
    )