"""
planner.py
==========

Planner stage of the desktop agent.

Pipeline:

Screenshot
    ↓
OmniParser
    ↓
Elements JSON
    ↓
Gemini Vision Analysis
    ↓
Planner (Gemma3:4b)
    ↓
Action JSON

Responsibilities:
- Receive user goal
- Receive OmniParser elements
- Receive Gemini screen analysis
- Ask Gemma what to do next
- Return a structured action

No mouse/keyboard execution here.
"""

from __future__ import annotations

import json
import re
from typing import Any

import ollama


MODEL = "gemma3:4b"


SYSTEM_PROMPT = """
You are a desktop agent planner.

Your job is ONLY to choose ONE action.

Available actions:

1. left_click

{
  "action":"left_click",
  "target_id":123,
  "reason":"..."
}

--------------------------------------------------

2. right_click

{
  "action":"right_click",
  "target_id":123,
  "reason":"..."
}

--------------------------------------------------

3. double_click

{
  "action":"double_click",
  "target_id":123,
  "reason":"..."
}

--------------------------------------------------

4. middle_click

{
  "action":"middle_click",
  "target_id":123,
  "reason":"..."
}

--------------------------------------------------

5. move_mouse

{
  "action":"move_mouse",
  "target_id":123,
  "reason":"..."
}

--------------------------------------------------

6. type

{
  "action":"type",
  "text":"hello world",
  "reason":"..."
}

Do NOT include target_id.

--------------------------------------------------

7. keypress

{
  "action":"keypress",
  "key":"enter",
  "reason":"..."
}

Examples:

enter
tab
escape
backspace
delete
up
down
left
right

--------------------------------------------------

8. hotkey

{
  "action":"hotkey",
  "keys":["ctrl","l"],
  "reason":"..."
}

Examples:

["ctrl","c"]
["ctrl","v"]
["ctrl","a"]
["ctrl","l"]
["alt","tab"]

--------------------------------------------------

9. scroll_up

{
  "action":"scroll_up",
  "amount":500,
  "reason":"..."
}

--------------------------------------------------

10. scroll_down

{
  "action":"scroll_down",
  "amount":500,
  "reason":"..."
}

--------------------------------------------------

11. done

{
  "action":"done",
  "reason":"goal completed"
}

Rules:

- Return JSON only.
- No markdown.
- No explanations outside JSON.
- Pick exactly ONE action.
- Use only IDs that exist.
- Never invent IDs.
- Never invent elements.
- If a keyboard-only action can satisfy the goal, prefer it.
"""


class PlannerError(Exception):
    pass


def _extract_json(text: str) -> dict:

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if not match:
        raise PlannerError(
            f"Could not find JSON in model output:\n{text}"
        )

    try:
        return json.loads(
            match.group()
        )
    except Exception as e:
        raise PlannerError(
            f"Invalid JSON returned by model:\n{text}"
        ) from e


def _build_prompt(
    goal: str,
    elements: list[dict],
    vision_analysis: str,
) -> str:

    BAD_WORDS = [
        "diamond",
        "ribbon",
        "pentagon",
        "toggle",
        "toggleoggle",
        "paragraphics",
        "bamboo",
        "rounded rectangle",
        "purple leaf",
        "purple flower",
        "3d modeling",
        "currency",
        "speaker",
        "grass",
    ]

    filtered_elements = []

    for elem in elements:

        name = str(
            elem.get("name", "")
        ).strip()

        if not name:
            continue

        if len(name) < 2:
            continue

        if len(name) > 100:
            continue

        lower = name.lower()

        if any(
            bad in lower
            for bad in BAD_WORDS
        ):
            continue

        filtered_elements.append(elem)

    MAX_ELEMENTS = 40

    filtered_elements = filtered_elements[
        :MAX_ELEMENTS
    ]

    print(
        f"\nPlanner received "
        f"{len(elements)} elements"
    )

    print(
        f"Planner using "
        f"{len(filtered_elements)} elements"
    )

    lines = []

    for elem in filtered_elements:

        elem_id = elem.get("id")

        elem_type = elem.get(
            "type",
            "unknown"
        )

        elem_name = elem.get(
            "name",
            ""
        )

        pixel_center = elem.get(
            "pixel_center",
            None,
        )

        lines.append(
            f"[{elem_id}] "
            f"{elem_type} | "
            f"{elem_name} | "
            f"center={pixel_center}"
        )

    element_text = "\n".join(lines)

    return f"""
You are a desktop agent planner.

Goal:

{goal}

Gemini Vision Analysis:

{vision_analysis}

Available Elements:

{element_text}

Important:

- Use BOTH the Gemini vision analysis and the OmniParser elements.
- Gemini analysis is usually more reliable than element labels.
- OmniParser labels may be incorrect.
- If multiple elements have similar names, use the Gemini analysis to identify the correct one.
- Use only IDs that exist.
- Never invent IDs.
- Never invent elements.
- Prefer matching visible UI controls.
- Choose exactly ONE action.

Available Actions:

LEFT CLICK

{{
  "action":"left_click",
  "target_id":123,
  "reason":"..."
}}

RIGHT CLICK

{{
  "action":"right_click",
  "target_id":123,
  "reason":"..."
}}

DOUBLE CLICK

{{
  "action":"double_click",
  "target_id":123,
  "reason":"..."
}}

MIDDLE CLICK

{{
  "action":"middle_click",
  "target_id":123,
  "reason":"..."
}}

MOVE MOUSE

{{
  "action":"move_mouse",
  "target_id":123,
  "reason":"..."
}}

TYPE

{{
  "action":"type",
  "text":"hello world",
  "reason":"..."
}}

KEYPRESS

{{
  "action":"keypress",
  "key":"enter",
  "reason":"..."
}}

HOTKEY

{{
  "action":"hotkey",
  "keys":["ctrl","l"],
  "reason":"..."
}}

SCROLL DOWN

{{
  "action":"scroll_down",
  "amount":500,
  "reason":"..."
}}

SCROLL UP

{{
  "action":"scroll_up",
  "amount":500,
  "reason":"..."
}}

DONE

{{
  "action":"done",
  "reason":"task complete"
}}

Rules:

1. Return ONLY JSON.
2. Do not use markdown.
3. Do not explain outside JSON.
4. Use only IDs that exist.
5. Never invent IDs.
6. Never invent elements.
7. If the goal clearly requires typing, use "type".
8. If the goal clearly requires a keyboard shortcut, use "hotkey".
9. If the goal clearly requires scrolling, use "scroll_up" or "scroll_down".
10. If the goal is already complete, return "done".
11. Prefer clicking a matching visible UI element when one exists.
"""


def plan_next_action(
    goal: str,
    elements: list[dict],
    vision_analysis: str,
) -> dict[str, Any]:

    prompt = _build_prompt(
        goal=goal,
        elements=elements,
        vision_analysis=vision_analysis,
    )

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        options={
            "temperature": 0,
        },
    )

    content = response[
        "message"
    ]["content"]

    print("\n=== RAW MODEL OUTPUT ===")
    print(content)
    print("========================\n")

    action = _extract_json(
        content
    )

    return action


if __name__ == "__main__":

    sample_elements = [
        {
            "id": 1,
            "name": "Firefox browser",
            "type": "icon",
            "pixel_center": [201, 1414],
        },
        {
            "id": 2,
            "name": "Google Chrome",
            "type": "icon",
            "pixel_center": [260, 1414],
        },
    ]

    vision_analysis = """
Visible applications:
- Firefox taskbar icon
- Google Chrome taskbar icon
- Terminal window

Firefox icon is visible on the taskbar.
"""

    goal = "Click Firefox"

    action = plan_next_action(
        goal=goal,
        elements=sample_elements,
        vision_analysis=vision_analysis,
    )

    print(
        json.dumps(
            action,
            indent=2,
        )
    )