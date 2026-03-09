"""
Watch the training job (prepare_training_data.py) and automatically run
prepare_kaggle_upload.py when all files have been processed.

Usage:
  python scripts/watch_and_merge.py

The script polls the training log and the output JSONL every 30 seconds.
When no new entries appear for >90 seconds AND no python process is writing
to civil_cases.jsonl, it declares the run finished and runs the merge.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

settings = get_settings()

CIVIL_CASES_JSONL = settings.TRAINING_DIR / "civil_cases.jsonl"
LOG_FILE = Path(__file__).parent.parent.parent.parent.parent / "training_run_err.log"
# Fall back: look next to the repo root
if not LOG_FILE.exists():
    # Try common locations
    for candidate in [
        Path("f:/CivilModel_Backend new/training_run_err.log"),
        settings.BASE_DIR.parent.parent / "training_run_err.log",
    ]:
        if candidate.exists():
            LOG_FILE = candidate
            break

POLL_INTERVAL = 30      # seconds between checks
IDLE_THRESHOLD = 90     # seconds of no growth → declare done


def count_entries(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return sum(1 for l in path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip())
    except Exception:
        return 0


def last_log_line(log_path: Path) -> str:
    if not log_path.exists():
        return ""
    try:
        lines = [l for l in log_path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        return lines[-1] if lines else ""
    except Exception:
        return ""


def run_merge() -> None:
    print("\n" + "=" * 60)
    print("Training complete! Running Kaggle upload preparation...")
    print("=" * 60 + "\n")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "prepare_kaggle_upload.py")],
        cwd=str(settings.BASE_DIR),
    )
    if result.returncode == 0:
        print("\nDone! Your dataset is ready in data/training/kaggle_upload/")
    else:
        print("\nMerge script exited with errors — check above output.")


def main() -> None:
    print("Watching training job...")
    print(f"  JSONL : {CIVIL_CASES_JSONL}")
    print(f"  Log   : {LOG_FILE}")
    print(f"  Polling every {POLL_INTERVAL}s, idle threshold {IDLE_THRESHOLD}s\n")

    last_count = count_entries(CIVIL_CASES_JSONL)
    last_growth_time = time.monotonic()

    while True:
        time.sleep(POLL_INTERVAL)
        current_count = count_entries(CIVIL_CASES_JSONL)
        log_tail = last_log_line(LOG_FILE)
        now = time.monotonic()

        if current_count > last_count:
            delta = current_count - last_count
            print(f"[{time.strftime('%H:%M:%S')}] Progress: {current_count} entries (+{delta}) | {log_tail[-80:]}")
            last_count = current_count
            last_growth_time = now
        else:
            idle_secs = int(now - last_growth_time)
            print(f"[{time.strftime('%H:%M:%S')}] No growth for {idle_secs}s | entries={current_count}")

            # Check if log says "Summary" or "Done" (end markers)
            finished_markers = ["summary", "wrote", "all done", "complete", "finished", "no files to process"]
            if any(m in log_tail.lower() for m in finished_markers):
                print("  -> Log shows completion marker. Running merge.")
                run_merge()
                return

            if idle_secs >= IDLE_THRESHOLD:
                print(f"  -> No growth for {idle_secs}s — assuming training finished.")
                run_merge()
                return


if __name__ == "__main__":
    main()
