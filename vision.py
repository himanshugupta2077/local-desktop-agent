import os

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

VISION_PROMPT = """
You are the vision system of a desktop AI agent.

Analyze the screenshot.

Describe:

- Visible applications
- Visible windows
- Important buttons
- Important UI controls
- Taskbar applications
- Browser tabs if visible
- Search boxes if visible
- Anything relevant to desktop navigation

Keep the response concise.

Do not invent information.

Return plain text only.
"""


def analyze_screenshot(
    screenshot_path: str,
) -> str:

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set"
        )

    client = genai.Client(
        api_key=api_key
    )

    with open(
        screenshot_path,
        "rb",
    ) as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png",
            ),
            VISION_PROMPT,
        ],
    )

    if not response.text:
        return ""

    return response.text.strip()


if __name__ == "__main__":

    screenshot_path = "screenshot.png"

    result = analyze_screenshot(
        screenshot_path
    )

    print(result)