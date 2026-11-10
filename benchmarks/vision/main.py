#!/usr/bin/env python3
"""
Vision Model Benchmark — Ollama
Tests: T1 raw speed, T2 real-world workload, T3 accuracy/reasoning
Hardware: Intel i7-12700H + RTX 3060 Mobile 6 GB + 16 GB RAM
"""

import csv
import time
import subprocess
import requests
import ollama
from pathlib import Path

# ─── CONFIG ────────────────────────────────────────────────────────────────────

MODELS = [
    "qwen2.5vl:3b",
    "qwen3-vl:4b",
    "gemma3:4b",
    "qwen3-vl:8b",
    "Qwen3.5:9B",
    "gemma4:31b",
]

# Test 1 – Raw Inference Speed
# Same image, same prompt, N runs; first run after cold-start is warm-up
TEST1_IMAGE  = "1.png"
TEST1_PROMPT = "Describe this image in one paragraph."
TEST1_RUNS   = 5          # warm-up is run 0; runs 1-4 are timed

# Test 2 – Real-World Vision Workload
TEST2_IMAGES = ["terminal.png", "browser.png", "email.png", "dashboard.png"]
TEST2_PROMPT = "Describe what is happening on this screen."

# Test 3 – Accuracy + Reasoning (you score each response 1-10)
TEST3_TASKS = [
    ("invoice.png", "in one paragraph print only most imp things"),
    ("chart.png",   "Explain what this graph shows in 1 para."),
    ("network.png", "Describe the network architecture shown in 1 para."),
    ("ui.png",      "Identify and list the UI elements visible in 1 para."),
]

OLLAMA_URL   = "http://localhost:11434"
RESULTS_CSV  = "benchmark_results.csv"

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def vram_mb() -> int:
    """Return current GPU VRAM usage in MB (nvidia-smi)."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        return int(r.stdout.strip())
    except Exception:
        return -1


def unload_all():
    """Evict every model in MODELS from VRAM before loading the next one."""
    for m in MODELS:
        try:
            requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": m, "keep_alive": 0},
                timeout=10,
            )
        except Exception:
            pass
    time.sleep(2)   # give Ollama a moment to release VRAM


def chat(model: str, image_path: str, prompt: str) -> tuple[str, float]:
    """Single vision inference → (response_text, elapsed_seconds)."""
    t0 = time.time()
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt, "images": [image_path]}],
    )
    return resp["message"]["content"], time.time() - t0


def ask_score(label: str) -> int:
    """Prompt the user for a 1-10 quality score."""
    while True:
        try:
            v = int(input(f"  Score for {label} (1-10): ").strip())
            if 1 <= v <= 10:
                return v
        except (ValueError, KeyboardInterrupt):
            print("  Enter a number between 1 and 10.")


def divider(char="─", width=70):
    print(char * width)

# ─── PER-MODEL BENCHMARK ───────────────────────────────────────────────────────

def benchmark_model(model: str) -> dict:
    res = {"model": model}

    # ── Cold start ─────────────────────────────────────────────────────────
    divider("═")
    print(f"  MODEL : {model}")
    divider("═")
    vram_before = vram_mb()
    print(f"  VRAM before load : {vram_before} MB")
    print("  [cold start] timing first inference (model load + inference) …")

    _, cold = chat(model, TEST1_IMAGE, TEST1_PROMPT)   # loads model from disk
    res["cold_start_s"] = round(cold, 2)
    vram_after = vram_mb()
    res["vram_loaded_mb"] = vram_after
    print(f"  cold start  : {cold:.2f}s")
    print(f"  VRAM loaded : {vram_after} MB  (delta {vram_after - vram_before} MB)")

    # ── Test 1 – Raw Speed ─────────────────────────────────────────────────
    print(f"\n  TEST 1 – Raw Inference Speed  ({TEST1_RUNS} runs + warm-up)")
    divider()
    t1_times = []
    for i in range(TEST1_RUNS):
        _, t = chat(model, TEST1_IMAGE, TEST1_PROMPT)
        label = "warm-up" if i == 0 else f"run {i:>2}"
        print(f"    {label} : {t:.2f}s")
        if i > 0:
            t1_times.append(t)

    res["t1_avg_s"] = round(sum(t1_times) / len(t1_times), 2)
    res["t1_min_s"] = round(min(t1_times), 2)
    res["t1_max_s"] = round(max(t1_times), 2)
    print(f"  → avg {res['t1_avg_s']}s  |  min {res['t1_min_s']}s  |  max {res['t1_max_s']}s")

    # ── Test 2 – Real-World Workload ───────────────────────────────────────
    print(f"\n  TEST 2 – Real-World Vision Workload")
    divider()
    t2_times = []
    for img in TEST2_IMAGES:
        if not Path(img).exists():
            print(f"    {img:<20} SKIPPED (file not found)")
            continue
        _, t = chat(model, img, TEST2_PROMPT)
        t2_times.append(t)
        print(f"    {img:<20} {t:.2f}s")

    if t2_times:
        res["t2_avg_s"]   = round(sum(t2_times) / len(t2_times), 2)
        res["t2_images_n"] = len(t2_times)
        print(f"  → avg {res['t2_avg_s']}s  over {len(t2_times)} image(s)")
    else:
        res["t2_avg_s"]    = None
        res["t2_images_n"] = 0
        print("  → no images found, test skipped")

    # ── Test 3 – Accuracy + Reasoning ─────────────────────────────────────
    print(f"\n  TEST 3 – Accuracy & Reasoning (score each response 1-10)")
    divider()
    t3_scores = []
    t3_times  = []

    for img, prompt in TEST3_TASKS:
        if not Path(img).exists():
            print(f"  [{img}]  SKIPPED (file not found)\n")
            continue

        text, t = chat(model, img, prompt)
        t3_times.append(t)

        print(f"\n  [{img}]  ({t:.2f}s)")
        divider("-", 60)
        print(text)
        divider("-", 60)

        score = ask_score(img)
        t3_scores.append(score)

    if t3_scores:
        res["t3_avg_score"]  = round(sum(t3_scores) / len(t3_scores), 1)
        res["t3_avg_lat_s"]  = round(sum(t3_times)  / len(t3_times),  2)
        res["t3_tasks_n"]    = len(t3_scores)
        print(f"\n  → avg score {res['t3_avg_score']}/10  |  avg latency {res['t3_avg_lat_s']}s")
    else:
        res["t3_avg_score"] = None
        res["t3_avg_lat_s"] = None
        res["t3_tasks_n"]   = 0

    res["vram_peak_mb"] = vram_mb()
    print(f"\n  VRAM peak : {res['vram_peak_mb']} MB")

    # Unload before next model
    print("  Unloading model …")
    unload_all()
    print()
    return res

# ─── SUMMARY TABLE + CSV ───────────────────────────────────────────────────────

def print_summary(all_results: list[dict]):
    divider("═")
    print("  BENCHMARK SUMMARY")
    divider("═")

    col = {"model": 20, "cold": 10, "t1": 8, "t2": 8, "t3lat": 8, "vram": 9, "score": 9}
    hdr = (
        f"  {'Model':<{col['model']}}"
        f"{'Cold':>{col['cold']}}"
        f"{'T1 Avg':>{col['t1']}}"
        f"{'T2 Avg':>{col['t2']}}"
        f"{'T3 Lat':>{col['t3lat']}}"
        f"{'VRAM MB':>{col['vram']}}"
        f"{'T3 Score':>{col['score']}}"
    )
    print(hdr)
    divider()

    def f(v, unit="s"):
        return f"{v}{unit}" if v is not None else "N/A"

    for r in all_results:
        if "error" in r:
            print(f"  {r['model']:<{col['model']}}  ERROR: {r['error']}")
            continue
        print(
            f"  {r['model']:<{col['model']}}"
            f"{f(r.get('cold_start_s')):>{col['cold']}}"
            f"{f(r.get('t1_avg_s')):>{col['t1']}}"
            f"{f(r.get('t2_avg_s')):>{col['t2']}}"
            f"{f(r.get('t3_avg_lat_s')):>{col['t3lat']}}"
            f"{str(r.get('vram_peak_mb', 'N/A')):>{col['vram']}}"
            f"{f(r.get('t3_avg_score'), '/10'):>{col['score']}}"
        )
    divider("═")


def save_csv(all_results: list[dict]):
    if not all_results:
        return
    keys = [k for k in all_results[0].keys()]
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_results)
    print(f"\n  Results saved → {RESULTS_CSV}")

# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n  Vision Model Benchmark — Ollama")
    print(f"  Models to test: {', '.join(MODELS)}\n")

    all_results = []

    for model in MODELS:
        unload_all()   # clean slate before each model
        try:
            r = benchmark_model(model)
            all_results.append(r)
        except Exception as e:
            print(f"  ERROR running {model}: {e}\n")
            all_results.append({"model": model, "error": str(e)})

    print_summary(all_results)
    save_csv(all_results)


if __name__ == "__main__":
    main()