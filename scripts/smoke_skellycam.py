from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core import skellycam_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test SkellyCam HTTP control.")
    parser.add_argument("--base-url", default="http://localhost:53117")
    parser.add_argument("--recording-dir", default=r"H:\lib\Skellycam_recording")
    parser.add_argument("--recording-name", default=f"rapt_smoke_{time.strftime('%Y%m%d_%H%M%S')}")
    args = parser.parse_args()

    recording_dir = Path(args.recording_dir)
    if not recording_dir.exists():
        print(f"Recording directory does not exist: {recording_dir}", file=sys.stderr)
        return 2

    print("Checking SkellyCam health...")
    health = skellycam_client.check_health(args.base_url)
    print(f"health: {health}")

    print(f"Starting recording: {args.recording_name}")
    start = skellycam_client.start_recording(
        args.base_url,
        args.recording_name,
        str(recording_dir),
        mic_device_index=-1,
    )
    print(f"start: {start}")

    time.sleep(2)

    print("Stopping recording...")
    stop = skellycam_client.stop_recording(args.base_url)
    print(f"stop: {stop}")
    print("Smoke test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
