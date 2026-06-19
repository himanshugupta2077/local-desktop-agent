# OmniParser CLI — Usage Guide

This turns the original one-shot `omniparser.py` script into a small CLI
tool with three run modes (single image, watch, serve), a config file, and
no hardcoded paths. It's a drop-in replacement: copy these files into your
existing OmniParser repo root (next to your `util/` and `weights/` folders)
and `python omniparser.py ...` still works the way you'd expect.

## 1. Project layout

```
OmniParser/                      <- your existing repo root
├── util/                        <- already there (unchanged)
├── weights/                     <- already there (unchanged)
├── omniparser.py                <- thin wrapper, keeps the old invocation style
├── omniparser_cli/
│   ├── __init__.py
│   ├── config.py                <- defaults + config file + CLI-flag merging
│   ├── core.py                  <- OmniParserEngine: model loading + parse()
│   ├── watcher.py                <- polling loop for --watch
│   ├── server.py                <- stdlib HTTP server for --serve
│   └── cli.py                   <- argparse entrypoint
└── config.example.yaml          <- starter config, copy & edit
```

Nothing else from your repo needs to change. `omniparser_cli/core.py` imports
`util.utils` exactly like the original script did, so it still has to be run
from the repo root (or with the repo root on `PYTHONPATH`).

## 2. The three modes

Pick exactly one per run:

| Flag | What it does |
|---|---|
| `--image PATH` | Parse a single screenshot, print JSON (or write it with `--output`), exit. |
| `--watch` | Poll a directory forever, parsing each new screenshot as it lands. |
| `--serve` | Run an HTTP server other processes (e.g. your LLM planner) can call. |

### Single image

```bash
python omniparser.py --image screenshot.png
python omniparser.py --image screenshot.png --output elements.json
python omniparser.py --image screenshot.png --no-pretty   # compact JSON, good for piping
```

### Watch mode

```bash
# one-off: process whatever's already in the folder, then exit
python omniparser.py --watch --watch-dir ./screenshots --output ./output --once

# long-running: keep watching, polling every 1.5s
python omniparser.py --watch --watch-dir ./screenshots --output ./output --interval 1.5

# also move each screenshot into ./processed once it's been parsed
python omniparser.py --watch --watch-dir ./screenshots --output ./output --move-processed ./processed
```

How it decides a file is "ready": it polls the directory, and only parses a
file once its size has stayed identical across two consecutive polls (so a
screenshot tool that's still writing the PNG doesn't get parsed half-written).
With `--once` there's only a single pass, so anything already sitting in the
folder is treated as complete.

It also keeps a small state file (`./.omniparser_state.json` by default, see
`watch.state_file` in the config) recording which files+mtimes it has already
processed, so restarting the watcher doesn't reprocess everything. Each
output JSON is written to `<output_dir>/<screenshot_name>.json`.

### Serve mode

```bash
python omniparser.py --serve --host 127.0.0.1 --port 8765
```

Then, from your planner process:

```bash
# parse a screenshot already on disk
curl "http://127.0.0.1:8765/parse?path=/abs/path/to/screenshot.png"

# or POST the raw image bytes directly
curl -X POST -H "Content-Type: image/png" --data-binary @screenshot.png \
     http://127.0.0.1:8765/parse

curl http://127.0.0.1:8765/health
# {"status": "ok", "models_loaded": true}
```

This is a plain `http.server`-based server with no framework dependency —
it's meant for trusted local/internal use (same machine or LAN), not as a
public-facing API. There's no auth, and the 25MB upload cap is just a
sanity limit, not a security control.

Both `--watch` and `--serve` load the YOLO/caption models once at startup
(instead of per-screenshot, like the original script effectively did every
invocation) and fail fast with a clear error if the model paths are wrong —
you don't find out only after the first screenshot comes in.

## 3. Configuration — three layers, no hardcoded paths

Resolution order (later wins):

1. **Built-in defaults** (`omniparser_cli/config.py`)
2. **Config file** (`--config path.yaml` or `.json`)
3. **CLI flags**

Generate a starter config to edit:

```bash
python omniparser.py --init-config config.yaml
# or: python omniparser.py --init-config config.json   (if you don't have PyYAML installed)
```

Example `config.yaml`:

```yaml
model:
  yolo_model_path: weights/icon_detect/model.pt
  caption_model_name: florence2
  caption_model_path: weights/icon_caption_florence
ocr:
  paragraph: false
  text_threshold: 0.9
  use_paddleocr: true
yolo:
  box_threshold: 0.05
  iou_threshold: 0.1
  img_size: 640
postprocess:
  dedup_iou: 0.6
watch:
  directory: ./screenshots
  pattern: '*.png'
  interval: 2.0
  output_dir: ./output
  state_file: ./.omniparser_state.json
  move_processed_to: null
  stable_checks: 2
server:
  host: 127.0.0.1
  port: 8765
output:
  pretty: true
log_level: INFO
```

Use it:

```bash
python omniparser.py --config config.yaml --watch
```

Any CLI flag you also pass overrides that one value from the file — you
don't need to duplicate the whole file just to change one threshold:

```bash
python omniparser.py --config config.yaml --watch --interval 5 --box-threshold 0.1
```

## 4. Full flag reference

Run `python omniparser.py --help` for the authoritative list (it's generated
from the actual argparse definitions, so it can't drift out of date). Summary:

**Modes:** `--image PATH`, `--watch`, `--serve` (pick exactly one)

**Config:** `--config PATH`, `--init-config PATH`, `--log-level {DEBUG,INFO,WARNING,ERROR}`

**`--image` mode:** `--output PATH` (file to write JSON to; default stdout)

**`--watch` mode:** `--watch-dir DIR`, `--pattern GLOB`, `--interval SECONDS`,
`--output DIR` (where JSON results land), `--move-processed DIR`, `--once`

**`--serve` mode:** `--host HOST`, `--port PORT`

**Model/inference overrides:** `--yolo-model PATH`, `--caption-model-name NAME`,
`--caption-model-path PATH`, `--box-threshold F`, `--iou-threshold F`,
`--img-size N`, `--ocr-text-threshold F`, `--dedup-iou F`,
`--paddleocr` / `--no-paddleocr`, `--pretty` / `--no-pretty`

## 5. Running it long-term

For `--watch` or `--serve` as a background service, a simple systemd unit
works well since both modes just run forever in the foreground:

```ini
[Unit]
Description=OmniParser watch mode
After=network.target

[Service]
WorkingDirectory=/path/to/OmniParser
ExecStart=/path/to/venv/bin/python omniparser.py --config /path/to/config.yaml --watch
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

For a one-shot cron/CI sweep instead of a long-running service, use `--once`:

```cron
*/5 * * * * cd /path/to/OmniParser && python omniparser.py --watch --once --config config.yaml
```

## 6. Troubleshooting

- **"YOLO model weights not found at ..."** / **"Caption model not found at ..."**
  — the path in your config/flags is wrong, or you're not running from the
  repo root. Check `model.yolo_model_path` / `model.caption_model_path`.
- **"Config file '...' is YAML but PyYAML is not installed"** — either
  `pip install pyyaml`, or write your config as `.json` instead.
- **Watch mode never processes a file** — check `--pattern` actually matches
  the extension your screenshot tool writes (default is `*.png`), and that
  the file isn't being continuously rewritten (the stability check needs two
  polls with an unchanged size).
- **Server `/parse` is slow on the very first request** — it shouldn't be:
  models are loaded eagerly at startup for `--watch`/`--serve`. If it's slow
  every time, the bottleneck is model inference itself, not loading.
