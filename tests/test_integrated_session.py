from __future__ import annotations

import csv
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.integrated_session import IntegratedSessionController


class FakeConfig:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir
        self.skellycam_base_url = "http://fake-skellycam"
        self.skellycam_recording_dir = r"H:\lib\Skellycam_recording"


class FakeSkellyCamClient:
    def start_recording(self, base_url, recording_name, recording_directory, mic_device_index=-1):
        return {
            "base_url": base_url,
            "recording_name": recording_name,
            "recording_directory": recording_directory,
            "mic_device_index": mic_device_index,
            "response_text": "started",
            "before_perf_counter_ns": 1,
            "after_perf_counter_ns": 3,
            "midpoint_perf_counter_ns": 2,
        }

    def stop_recording(self, base_url):
        return {
            "base_url": base_url,
            "response_text": "stopped",
            "before_perf_counter_ns": 4,
            "after_perf_counter_ns": 6,
            "midpoint_perf_counter_ns": 5,
        }


class FakeRfidRowWriter:
    def __init__(self, reads_path, events_path):
        self.reads_path = reads_path
        self.events_path = events_path
        self.reads = []
        self.events = []
        self.closed = False

    def write_read(self, session_id, trial_id, item, host_wall_time_ns, host_perf_counter_ns, event_type="read"):
        self.reads.append((session_id, trial_id, item, host_wall_time_ns, host_perf_counter_ns, event_type))

    def write_event(self, session_id, trial_id, event_type, notes="", host_wall_time_ns=None, host_perf_counter_ns=None):
        event = {
            "session_id": session_id,
            "trial_id": trial_id,
            "event_type": event_type,
            "host_wall_time_ns": host_wall_time_ns or 10,
            "host_perf_counter_ns": host_perf_counter_ns or 20,
            "notes": notes,
        }
        self.events.append(event)
        return event

    def close(self):
        self.closed = True


class IntegratedSessionTests(unittest.TestCase):
    def test_session_files_events_and_metadata_without_hardware(self):
        temp_root = ROOT / ".tmp_tests"
        temp_root.mkdir(exist_ok=True)
        tmp = temp_root / f"integrated_session_{uuid.uuid4().hex}"
        tmp.mkdir()
        try:
            controller = IntegratedSessionController(FakeConfig(str(tmp)), FakeSkellyCamClient())
            files = controller.prepare("sub001", "squat", "trial001", "notes")

            controller.writer.write_read(
                files.session_id,
                "trial001",
                {"epc": "E200001", "ant": 1, "rssi": -42.5, "ts": 123.456},
                host_wall_time_ns=1000,
                host_perf_counter_ns=2000,
            )
            controller.write_event("sync_start", "first marker")
            controller.start_skellycam()
            controller.stop_skellycam()
            metadata = controller.finish()

            self.assertTrue(files.session_dir.exists())
            self.assertTrue(files.rfid_reads_path.exists())
            self.assertTrue(files.rfid_events_path.exists())
            self.assertTrue(files.meta_path.exists())
            self.assertEqual(metadata["recording_name"], "sub001_squat_trial001")

            with files.rfid_reads_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(rows[0]["tag_id"], "E200001")
            self.assertEqual(rows[0]["host_wall_time_ns"], "1000")

            with files.rfid_events_path.open("r", encoding="utf-8", newline="") as f:
                events = list(csv.DictReader(f))
            self.assertEqual(events[0]["event_type"], "sync_start")

            with files.meta_path.open("r", encoding="utf-8") as f:
                saved_meta = json.load(f)
            self.assertEqual(saved_meta["skellycam_start"]["response_text"], "started")
            self.assertEqual(saved_meta["skellycam_stop"]["response_text"], "stopped")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_controller_accepts_fake_rfid_row_writer(self):
        temp_root = ROOT / ".tmp_tests"
        temp_root.mkdir(exist_ok=True)
        tmp = temp_root / f"integrated_session_{uuid.uuid4().hex}"
        tmp.mkdir()
        try:
            controller = IntegratedSessionController(
                FakeConfig(str(tmp)),
                FakeSkellyCamClient(),
                writer_factory=FakeRfidRowWriter,
            )
            files = controller.prepare("sub002", "walk", "trial002")
            event = controller.write_event("sync_end")
            metadata = controller.finish()

            self.assertTrue(files.session_dir.exists())
            self.assertEqual(event["event_type"], "sync_end")
            self.assertTrue(controller.writer.closed)
            self.assertEqual(metadata["recording_name"], "sub002_walk_trial002")
            self.assertTrue(files.meta_path.exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
