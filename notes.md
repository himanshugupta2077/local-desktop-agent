## Current Goal

Build a fully local desktop-use agent that operates a computer similarly to a human:

```text
See Screen
↓
Understand UI
↓
Reason About Goal
↓
Take Action
↓
Observe Result
↓
Repeat
```

No browser APIs.
No accessibility APIs.
No direct application integrations.

Only:

```text
Pixels
+
Mouse
+
Keyboard
```

---

## Current Architecture

```text
┌──────────────────────────────┐
│ User Goal                    │
│ "Open Firefox"               │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ screenshot.py                │
│ KDE Screenshot Capture       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ omniparse_cli.py             │
│ Calls OmniParser Server      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ OmniParser                   │
│ OCR + Icon Detection         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ elements.json                │
│ Structured UI Elements       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ planner.py                   │
│ Gemma3:4B                    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ JSON Action                  │
│ click / type / keypress      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ executor.py                  │
│ PyAutoGUI                    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Desktop                      │
└──────────────────────────────┘
```

---

## What Is Working

### Screenshot Capture

```text
KDE Wayland
↓
qdbus6 Spectacle
↓
PNG Screenshot
```

Working.

---

### UI Parsing

```text
Screenshot
↓
OmniParser
↓
elements.json
```

Working.

Example:

```json
{
  "id": 45,
  "name": "Firefox browser.",
  "pixel_center": [201,1414]
}
```

---

### Reasoning

```text
Goal:
Click Back

↓

Planner:
target_id = 12
```

Working.

---

### Mouse Control

```text
target_id
↓
pixel_center
↓
PyAutoGUI
↓
Mouse Movement
↓
Click
```

Working.

Scaling issue resolved by changing KDE from 105% to 100%.

---

## Current Completion Status

```text
Screenshot Capture        ██████████ 100%
UI Detection             ████████░░  80%
Planner                  ███████░░░  70%
Mouse Execution          ██████████ 100%
Keyboard Execution       ███░░░░░░░  30%
Feedback Loop            ░░░░░░░░░░   0%
Memory                   ░░░░░░░░░░   0%
Task Planning            ░░░░░░░░░░   0%
```

---

# Biggest Current Weakness

OmniParser output quality.

Example:

Good:

```text
Back
Forward
Firefox Browser
Google Chrome
WhatsApp
```

Bad:

```text
M0,0L9,0 4.5,5z
Diamond
Subscript
Ribbonbon
Image
```

These are noise.

---

# Desired OmniParser Output

Current:

```json
{
  "id":45,
  "name":"Firefox browser."
}
```

Desired:

```json
{
  "id":45,
  "name":"Firefox",
  "type":"taskbar_app",
  "confidence":0.94
}
```

---

# Immediate Improvement #1

Element Filtering

Before sending to Gemma:

Remove:

```python
if name.startswith("M0,"):
    skip

if len(name.strip()) < 2:
    skip

if name.lower() in {
    "image",
    "diamond",
    "subscript"
}:
    skip
```

This alone may remove 30-50% of useless elements.

---

# Immediate Improvement #2

Merge Duplicate Elements

Current:

```text
Firefox browser.
Firefox browser.
Firefox browser.
```

Desired:

```text
Firefox browser.
```

Only send unique entries.

---

# Immediate Improvement #3

Better Planner Input

Current:

```text
73 elements
```

Desired:

```text
Taskbar:
- Firefox
- Chrome
- WhatsApp

Browser Controls:
- Back
- Forward
- Reload

Page:
- Gmail
- Compose
```

Gemma performs much better on structured information.

---

# Biggest Future Problem

The "+" button problem.

Example:

Browser:

```text
[ + ]
```

OmniParser may return:

```text
Add
```

or

```text
New
```

or

```text
Image
```

The planner has no way to know:

```text
+
means
new tab
```

---

# Long-Term Solution

Add Screenshot Context To Planner.

Current:

```text
Goal
+
Element List
```

Future:

```text
Goal
+
Element List
+
Screenshot Crop
```

Architecture:

```text
Screenshot
↓
OmniParser
↓
Element List

Screenshot
↓
Gemma Vision

Combined
↓
Planner
```

This is how modern computer-use systems work.

---

# Recommended Next Milestones

### Milestone 1

Keyboard Actions

Support:

```json
{
  "action":"hotkey",
  "keys":["ctrl","t"]
}
```

Examples:

```text
Open New Tab
Ctrl+T

Focus Address Bar
Ctrl+L

Close Tab
Ctrl+W
```

---

### Milestone 2

Feedback Loop

```text
Screenshot
↓
Plan
↓
Execute
↓
Screenshot
↓
Plan
↓
Execute
```

First real agent.

---

### Milestone 3

Task Completion

Example:

```text
Goal:
Open Firefox
```

Loop:

```text
Find Firefox
↓
Click Firefox
↓
New Screenshot
↓
Firefox Visible?
↓
Yes
↓
Done
```

---

### Milestone 4

Vision-Based Reasoning

Replace:

```text
Gemma3:4B
```

with a vision model such as:

* Gemma 3 Vision
* Qwen2.5-VL
* Qwen3-VL

Then planner receives:

```text
Screenshot
+
UI Elements
+
Goal
```

instead of only UI elements.

That is likely the biggest future accuracy improvement because it solves ambiguous controls like "+" where OCR labels alone are insufficient.
