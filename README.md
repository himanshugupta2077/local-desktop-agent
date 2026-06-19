# Local Desktop Agent

A fully local desktop-use AI agent that interacts with a computer using only screenshots, mouse movements, and keyboard input.

The project is designed to mimic how a human uses a computer:

```text
See Screen
↓
Understand UI
↓
Reason About Goal
↓
Move Mouse / Press Keys
↓
Observe Result
```

No browser APIs, accessibility APIs, or application-specific integrations are used.

The agent operates entirely from visual information.

---

# Features

* Local execution
* Screenshot-based perception
* OmniParser-powered UI detection
* Gemma3 reasoning engine
* Mouse automation using PyAutoGUI
* Modular architecture
* Works on Arch Linux + KDE Plasma Wayland
* No cloud dependency

---

# Hardware Used

```text
CPU: Intel i7-12700H
GPU: RTX 3060 Mobile (6GB VRAM)
RAM: 16GB
OS: Arch Linux
Desktop: KDE Plasma Wayland
```

---

# Models Used

## Reasoning

```text
gemma3:4b
```

via Ollama.

## UI Understanding

```text
Microsoft OmniParser
```

running through the official Gradio server.

---

# Architecture

```text
User Goal
    ↓
agent.py
    ↓
screenshot.py
    ↓
omniparse_cli.py
    ↓
OmniParser Server
    ↓
elements.json
    ↓
planner.py
    ↓
Action JSON
    ↓
executor.py
    ↓
Desktop
```

---

# Repository Structure

```text
.
├── agent.py
├── planner.py
├── executor.py
├── screenshot.py
├── omniparse_cli.py
├── omniparser_runs/
└── README.md
```

---

# Component Overview

## agent.py

Main orchestrator.

Responsibilities:

* Accept user goal
* Capture screenshot
* Parse UI elements
* Request next action from planner
* Execute action

Flow:

```text
Goal
↓
Screenshot
↓
Parse
↓
Plan
↓
Execute
```

---

## screenshot.py

Captures the current desktop.

Uses KDE Spectacle through DBus.

Output:

```text
~/Pictures/Screenshots/
```

Example:

```bash
qdbus6 org.kde.Spectacle / org.kde.Spectacle.FullScreen false
```

---

## omniparse_cli.py

Client for OmniParser.

Responsibilities:

* Connect to local OmniParser server
* Submit screenshot
* Parse results
* Generate structured UI elements

Output:

```json
{
  "id": 45,
  "name": "Firefox browser.",
  "type": "icon",
  "pixel_center": [201,1414]
}
```

Generated files:

```text
omniparser_runs/
├── labeled.webp
├── parsed_elements.txt
├── elements.json
└── input.png
```

---

## planner.py

Reasoning layer.

Uses:

```text
gemma3:4b
```

Input:

```text
Goal:
Click Back

Available Elements:

[12] Back
[11] Forward
```

Output:

```json
{
  "action": "click",
  "target_id": 12
}
```

Planner never executes actions.

It only decides what action should be taken next.

---

## executor.py

Action execution layer.

Current supported actions:

```text
click
keypress
hotkey
type
```

Example:

```json
{
  "action": "click",
  "target_id": 45
}
```

↓

```python
pyautogui.moveTo(201, 1414)
pyautogui.click()
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourname/local-desktop-agent.git
cd local-desktop-agent
```

---

## Create Environment

```bash
conda create -n omni python=3.12
conda activate omni
```

---

## Install Dependencies

```bash
pip install ollama
pip install pyautogui
pip install pillow
pip install gradio_client
```

Install any additional dependencies required by OmniParser.

---

# OmniParser Setup

Clone and setup Microsoft OmniParser.

Verify the server starts:

```bash
python gradio_demo.py
```

Expected:

```text
Running on local URL:
http://127.0.0.1:7861
```

---

# Ollama Setup

Verify Ollama is running:

```bash
curl http://127.0.0.1:11434/api/tags
```

Expected response:

```json
{
  "models": [...]
}
```

Pull Gemma:

```bash
ollama pull gemma3:4b
```

---

# Running

Terminal 1:

```bash
conda activate omni
python gradio_demo.py
```

Terminal 2:

```bash
conda activate omni
python agent.py
```

Enter a goal:

```text
Goal: Click Back
```

---

# Example Flow

Goal:

```text
Click Back
```

OmniParser:

```text
[12] Back
```

Planner:

```json
{
  "action":"click",
  "target_id":12
}
```

Executor:

```text
Move Mouse
↓
Click
```

Result:

```text
Browser navigates back
```

---

# Current Status

Working:

* Screenshot capture
* OmniParser integration
* UI element extraction
* Goal-based planning
* Mouse movement
* Mouse clicking
* Coordinate mapping

In Progress:

* Keyboard shortcuts
* Multi-step planning
* Agent feedback loop
* Task completion detection
* Memory
* Reflection
* Autonomous execution

---

# Known Limitations

## UI Semantics

Some controls may not be labeled accurately.

Example:

```text
+
```

may become:

```text
Add
```

instead of:

```text
New Tab
```

This can reduce planner accuracy.

---

## Display Scaling

KDE display scaling affects coordinate accuracy.

Current tested configuration:

```text
Display Scale = 100%
```

Using 105% scaling caused click offsets.

---

## Resource Usage

OmniParser can consume significant RAM.

Recommended:

```text
16 GB RAM minimum
32 GB swapfile
```

Current test machine:

```text
16 GB RAM
32 GB swap enabled
```

---

# Future Roadmap

## Phase 1

Single-step actions

```text
Goal
↓
Action
↓
Execute
```

Status: Complete

---

## Phase 2

Feedback loop

```text
Goal
↓
Action
↓
Execute
↓
Observe
↓
Repeat
```

Status: Planned

---

## Phase 3

Vision-enhanced reasoning

Combine:

```text
Screenshot
+
OmniParser Elements
+
Goal
```

using a vision-language model.

Potential models:

```text
qwen3-vl:4b
qwen3-vl:8b
qwen2.5vl:3b
```

---

# Dependencies

This project is built on top of several open-source projects and models.

## Core Components

### Microsoft OmniParser

UI element detection and screen understanding.

Repository: https://github.com/microsoft/OmniParser

Used for:

* OCR
* Icon detection
* UI element localization
* Bounding box extraction

---

### Ollama

Local model serving framework.

Website: https://ollama.com
Repository: https://github.com/ollama/ollama

Used for:

* Running Gemma locally
* Running Qwen locally
* Model inference API

---

### Gemma 3

Reasoning model used by the planner.

Model: https://ollama.com/library/gemma3

Used for:

* Goal interpretation
* Action selection
* Next-step planning

---

### PyAutoGUI

Mouse and keyboard automation.

Repository: https://github.com/asweigart/pyautogui

Used for:

* Mouse movement
* Mouse clicks
* Keyboard input
* Hotkeys

---

### Gradio Client

Communication with the OmniParser server.

Repository: https://github.com/gradio-app/gradio

Used for:

* Calling OmniParser endpoints
* Receiving parsed UI results

---

## Attribution

This project would not be possible without the work of:

* Microsoft OmniParser
* Ollama
* Google DeepMind (Gemma)
* Alibaba Qwen Team
* PyAutoGUI
* Gradio
* Pillow

Please review the licenses of all dependencies before redistribution or commercial use.

# Notice

This repository is not affiliated with or endorsed by Microsoft.

UI understanding capabilities are provided through Microsoft OmniParser, which is distributed under its own license and maintained separately by its authors.


# License

## Project Code

Unless otherwise stated, the original source code in this repository is licensed under the PolyForm Noncommercial License 1.0.0.

You may:

* Use the software for personal, educational, and research purposes
* Modify the software
* Share the software and modifications

You may not:

* Use the software commercially
* Provide the software as a service
* Integrate the software into commercial products
* Use the software for client work or internal business operations

Commercial licensing is available separately from the author.

---

## Third-Party Dependencies

This project depends on Microsoft OmniParser and other third-party software.

Third-party components remain licensed under their respective licenses and are not relicensed by this repository.

Microsoft OmniParser is distributed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

Users are responsible for reviewing and complying with all applicable third-party license terms.

---

## Attribution

If you use this project, please provide attribution to:

* This repository
* Microsoft OmniParser
* Any other third-party projects required by your distribution
