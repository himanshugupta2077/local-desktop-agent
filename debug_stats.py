import json
import os
import subprocess
from datetime import datetime

import psutil


LOG_FILE = "debug_stats.jsonl"


def gpu_stats():

    try:

        result = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()

        used, total, util = result.split(",")

        return {
            "gpu_mem_used_mb": int(used),
            "gpu_mem_total_mb": int(total),
            "gpu_util_percent": int(util),
        }

    except Exception as e:

        return {
            "gpu_error": str(e)
        }


def process_memory():

    rows = []

    for proc in psutil.process_iter(
        [
            "pid",
            "name",
            "memory_info",
        ]
    ):

        try:

            rss_mb = (
                proc.info["memory_info"].rss
                / 1024
                / 1024
            )

            if rss_mb < 50:
                continue

            rows.append(
                {
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "rss_mb": round(
                        rss_mb,
                        1,
                    ),
                }
            )

        except Exception:
            pass

    rows.sort(
        key=lambda x: x["rss_mb"],
        reverse=True,
    )

    return rows[:15]


def snapshot(label=""):

    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    data = {
        "timestamp": datetime.now().isoformat(),
        "label": label,

        "ram_total_gb": round(
            vm.total / 1024**3,
            2,
        ),

        "ram_used_gb": round(
            vm.used / 1024**3,
            2,
        ),

        "ram_percent": vm.percent,

        "swap_total_gb": round(
            swap.total / 1024**3,
            2,
        ),

        "swap_used_gb": round(
            swap.used / 1024**3,
            2,
        ),

        "swap_percent": swap.percent,

        "processes": process_memory(),
    }

    data.update(
        gpu_stats()
    )

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as f:

        f.write(
            json.dumps(data)
        )

        f.write("\n")

    print(
        json.dumps(
            data,
            indent=2,
        )
    )