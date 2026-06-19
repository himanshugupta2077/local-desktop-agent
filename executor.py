import pyautogui

pyautogui.FAILSAFE = False


def _find_target(target_id, elements):

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
        return None

    pixel_center = target.get("pixel_center")

    if not pixel_center:
        print("ERROR: pixel_center missing")
        return None

    return target


def _move_to_target(target):

    x, y = target["pixel_center"]

    print(f"\nMoving mouse to: {x}, {y}")

    pyautogui.moveTo(
        x,
        y,
        duration=0.5,
    )

    return x, y


def execute(action, elements):

    print("\n=== EXECUTOR ===")
    print(action)

    action_type = action.get("action")

    # ------------------------
    # LEFT CLICK
    # ------------------------

    if action_type == "left_click":

        target = _find_target(
            action.get("target_id"),
            elements,
        )

        if not target:
            return

        x, y = _move_to_target(target)

        pyautogui.click(
            x=x,
            y=y,
            button="left",
        )

    # ------------------------
    # RIGHT CLICK
    # ------------------------

    elif action_type == "right_click":

        target = _find_target(
            action.get("target_id"),
            elements,
        )

        if not target:
            return

        x, y = _move_to_target(target)

        pyautogui.click(
            x=x,
            y=y,
            button="right",
        )

    # ------------------------
    # DOUBLE CLICK
    # ------------------------

    elif action_type == "double_click":

        target = _find_target(
            action.get("target_id"),
            elements,
        )

        if not target:
            return

        x, y = _move_to_target(target)

        pyautogui.doubleClick(
            x=x,
            y=y,
            button="left",
        )

    # ------------------------
    # MIDDLE CLICK
    # ------------------------

    elif action_type == "middle_click":

        target = _find_target(
            action.get("target_id"),
            elements,
        )

        if not target:
            return

        x, y = _move_to_target(target)

        pyautogui.click(
            x=x,
            y=y,
            button="middle",
        )

    # ------------------------
    # MOVE MOUSE
    # ------------------------

    elif action_type == "move_mouse":

        target = _find_target(
            action.get("target_id"),
            elements,
        )

        if not target:
            return

        _move_to_target(target)

    # ------------------------
    # DRAG
    # ------------------------

    elif action_type == "drag":

        start_x = action.get("start_x")
        start_y = action.get("start_y")

        end_x = action.get("end_x")
        end_y = action.get("end_y")

        duration = action.get(
            "duration",
            0.5,
        )

        print(
            f"Dragging from "
            f"({start_x},{start_y}) "
            f"to "
            f"({end_x},{end_y})"
        )

        pyautogui.moveTo(
            start_x,
            start_y,
            duration=0.2,
        )

        pyautogui.dragTo(
            end_x,
            end_y,
            duration=duration,
            button="left",
        )

    # ------------------------
    # SCROLL DOWN
    # ------------------------

    elif action_type == "scroll_down":

        amount = action.get(
            "amount",
            500,
        )

        print(
            f"Scrolling down "
            f"({amount})"
        )

        pyautogui.scroll(
            -abs(amount)
        )

    # ------------------------
    # SCROLL UP
    # ------------------------

    elif action_type == "scroll_up":

        amount = action.get(
            "amount",
            500,
        )

        print(
            f"Scrolling up "
            f"({amount})"
        )

        pyautogui.scroll(
            abs(amount)
        )

    # ------------------------
    # TYPE
    # ------------------------

    elif action_type == "type":

        text = action.get(
            "text",
            "",
        )

        print(f"Typing: {text}")

        pyautogui.write(
            text,
            interval=0.02,
        )

    # ------------------------
    # KEYPRESS
    # ------------------------

    elif action_type == "keypress":

        key = action.get("key")

        print(
            f"Pressing key: {key}"
        )

        pyautogui.press(key)

    # ------------------------
    # HOTKEY
    # ------------------------

    elif action_type == "hotkey":

        keys = action.get(
            "keys",
            [],
        )

        print(
            f"Pressing hotkey: {keys}"
        )

        pyautogui.hotkey(*keys)

    # ------------------------
    # DONE
    # ------------------------

    elif action_type == "done":

        print(
            action.get(
                "reason",
                "Task complete."
            )
        )

    else:

        print(
            f"Unknown action type: "
            f"{action_type}"
        )