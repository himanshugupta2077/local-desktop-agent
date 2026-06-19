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

Your job is ONLY to choose an action.

Available actions:

1. click
{
  "action":"click",
  "target_id":,
  "reason":"..."
}

2. type
{
  "action":"type",
  "target_id":,
  "text":"hello world",
  "reason":"..."
}

3. keypress
{
  "action":"keypress",
  "key":"enter",
  "reason":"..."
}

4. scroll
{
  "action":"scroll",
  "direction":"down",
  "reason":"..."
}

5. done
{
  "action":"done",
  "reason":"goal completed"
}

Rules:
- Return JSON only.
- No markdown.
- No explanations outside JSON.
- Pick exactly ONE action.
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

Example 1:
{{
  "action":"click",
  "target_id":,
  "reason":"..."
}}

Example 2:
{{
  "action":"type",
  "target_id":,
  "text":"hello world",
  "reason":"..."
}}

Example 3:
{{
  "action":"keypress",
  "key":"enter",
  "reason":"..."
}}

Example 4:
{{
  "action":"scroll",
  "direction":"down",
  "reason":"..."
}}

Example 5:
{{
  "action":"done",
  "reason":"goal completed"
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