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
Planner (Gemma3:4b)
    ↓
Action JSON
    ↓
Executor (future)

Responsibilities:
- Receive user goal
- Receive OmniParser elements
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

Use when the goal requires clicking an element.

--------------------------------------------------

2. right_click

{
  "action":"right_click",
  "target_id":123,
  "reason":"..."
}

Use when the goal explicitly requires a context menu.

--------------------------------------------------

3. double_click

{
  "action":"double_click",
  "target_id":123,
  "reason":"..."
}

Use when opening files, folders, or desktop icons.

--------------------------------------------------

4. middle_click

{
  "action":"middle_click",
  "target_id":123,
  "reason":"..."
}

Use only if explicitly required.

--------------------------------------------------

5. type

{
  "action":"type",
  "text":"hello world",
  "reason":"..."
}

Use when text should be typed.

Do NOT include target_id.

--------------------------------------------------

6. keypress

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

7. hotkey

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

8. scroll_up

{
  "action":"scroll_up",
  "amount":500,
  "reason":"..."
}

--------------------------------------------------

9. scroll_down

{
  "action":"scroll_down",
  "amount":500,
  "reason":"..."
}

--------------------------------------------------

10. done

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
    """
    Extract JSON object from model response.
    """

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise PlannerError(
            f"Could not find JSON in model output:\n{text}"
        )

    try:
        return json.loads(match.group())
    except Exception as e:
        raise PlannerError(
            f"Invalid JSON returned by model:\n{text}"
        ) from e


def _build_prompt(goal: str, elements: list[dict]) -> str:
    """
    Convert OmniParser output into planner prompt.
    """

    lines = []

    for elem in elements:
        lines.append(
            f"[{elem['id']}] "
            f"{elem['type']} | "
            f"{elem['name']}"
        )

    element_text = "\n".join(lines)

    return f"""
You are a desktop agent planner.

Goal:
{goal}

Available Elements:

{element_text}

Rules:

- Choose exactly ONE action.
- Use only IDs that exist in the element list.
- Match the goal against the available elements.
- Never invent elements.
- Never invent IDs.
- Return JSON only.

Examples:

{{
  "action":"left_click",
  "target_id":12,
  "reason":"Firefox matches the goal"
}}

{{
  "action":"right_click",
  "target_id":7,
  "reason":"Open context menu"
}}

{{
  "action":"double_click",
  "target_id":4,
  "reason":"Open folder"
}}

{{
  "action":"type",
  "text":"hello world",
  "reason":"Type requested text"
}}

{{
  "action":"keypress",
  "key":"enter",
  "reason":"Submit form"
}}

{{
  "action":"hotkey",
  "keys":["ctrl","l"],
  "reason":"Focus address bar"
}}

{{
  "action":"scroll_down",
  "amount":500,
  "reason":"Need to move page down"
}}

{{
  "action":"scroll_up",
  "amount":500,
  "reason":"Need to move page up"
}}

{{
  "action":"done",
  "reason":"Goal completed"
}}
"""


def plan_next_action(
    goal: str,
    elements: list[dict],
) -> dict[str, Any]:
    """
    Main planner API.

    Example:

    action = plan_next_action(
        goal="Click Google Images",
        elements=elements
    )
    """

    prompt = _build_prompt(
        goal=goal,
        elements=elements,
    )

    # print("\n========== PROMPT ==========")
    # print(prompt)
    # print("============================\n")
    
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

    content = response["message"]["content"]

    action = _extract_json(content)

    return action


if __name__ == "__main__":

    sample_elements = [
        {
            "id": 1,
            "name": "Search Box",
            "type": "input",
        },
        {
            "id": 2,
            "name": "Google Images",
            "type": "link",
        },
        {
            "id": 3,
            "name": "Search Button",
            "type": "button",
        },
    ]

    goal = "Click Google Images"

    action = plan_next_action(
        goal=goal,
        elements=sample_elements,
    )

    print(json.dumps(action, indent=2))