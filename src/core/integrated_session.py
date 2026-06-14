from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


RFID_READ_COLUMNS = [
    "session_id",
    "trial_id",
    "tag_id",
    "antenna",
    "rssi",
    "phase",
    "frequency",
    "reader_timestamp",
    "host_wall_time_ns",
    "host_perf_counter_ns",
    "event_type",
]

RFID_EVENT_COLUMNS = [
    "session_id",
    "trial_id",
    "event_type",
    "host_wall_time_ns",
    "host_perf_counter_ns",
    "notes",
]


def slugify(value: str, default: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or default


def build_recording_name(subject_id: str, action: str, trial_id: str) -> str:
    return "_".join(
        [
            slugify(subject_id, "subject"),
            slugify(action, "action"),
            slugify(trial_id, "trial"),
        ]
    )


@dataclass
class IntegratedSessionFiles:
    session_id: str
    session_dir: Path
    rfid_dir: Path
    rfid_reads_path: Path
    rfid_events_path: Path
    meta_path: Path


def create_integrated_session_files(output_dir: str | Path, now: datetime | None = None) -> IntegratedSessionFiles:
    root = Path(output_dir) / "RAPT_dataset"
    date_text = (now or datetime.now()).strftime("%Y_%m_%d")
    root.mkdir(parents=True, exist_ok=True)

    idx = 1
    while True:
        session_id = f"session_{date_text}_{idx:03d}"
        session_dir = root / session_id
        if not session_dir.exists():
            break
        idx += 1

    rfid_dir = session_dir / "rfid"
    rfid_dir.mkdir(parents=True, exist_ok=False)
    return IntegratedSessionFiles(
        session_id=session_id,
        session_dir=session_dir,
        rfid_dir=rfid_dir,
        rfid_reads_path=rfid_dir / "rfid_reads.csv",
        rfid_events_path=rfid_dir / "rfid_events.csv",
        meta_path=session_dir / "session_meta.json",
    )


class RfidCsvWriter:
    def __init__(self, reads_path: str | Path, events_path: str | Path) -> None:
        self.reads_path = Path(reads_path)
        self.events_path = Path(events_path)
        self._reads_file = self.reads_path.open("w", newline="", encoding="utf-8")
        self._events_file = self.events_path.open("w", newline="", encoding="utf-8")
        self._reads_writer = csv.DictWriter(self._reads_file, fieldnames=RFID_READ_COLUMNS)
        self._events_writer = csv.DictWriter(self._events_file, fieldnames=RFID_EVENT_COLUMNS)
        self._reads_writer.writeheader()
        self._events_writer.writeheader()

    def write_read(
        self,
        session_id: str,
        trial_id: str,
        item: dict[str, Any],
        host_wall_time_ns: int,
        host_perf_counter_ns: int,
        event_type: str = "read",
    ) -> None:
        self._reads_writer.writerow(
            {
                "session_id": session_id,
                "trial_id": trial_id,
                "tag_id": item.get("epc", ""),
                "antenna": item.get("ant", ""),
                "rssi": item.get("rssi", item.get("intensity", "")),
                "phase": item.get("phase", ""),
                "frequency": item.get("frequency", ""),
                "reader_timestamp": item.get("reader_timestamp", item.get("ts", "")),
                "host_wall_time_ns": host_wall_time_ns,
                "host_perf_counter_ns": host_perf_counter_ns,
                "event_type": event_type,
            }
        )
        self._reads_file.flush()

    def write_event(
        self,
        session_id: str,
        trial_id: str,
        event_type: str,
        notes: str = "",
        host_wall_time_ns: int | None = None,
        host_perf_counter_ns: int | None = None,
    ) -> dict[str, Any]:
        event = {
            "session_id": session_id,
            "trial_id": trial_id,
            "event_type": event_type,
            "host_wall_time_ns": host_wall_time_ns if host_wall_time_ns is not None else time.time_ns(),
            "host_perf_counter_ns": host_perf_counter_ns if host_perf_counter_ns is not None else time.perf_counter_ns(),
            "notes": notes,
        }
        self._events_writer.writerow(event)
        self.flush()
        return event

    def flush(self) -> None:
        self._reads_file.flush()
        self._events_file.flush()

    def close(self) -> None:
        self._reads_file.close()
        self._events_file.close()


def write_session_meta(meta_path: str | Path, metadata: dict[str, Any]) -> None:
    path = Path(meta_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)


class IntegratedSessionController:
    """Small testable coordinator for session files, SkellyCam calls, and metadata."""

    def __init__(
        self,
        config: Any,
        skellycam_client: Any,
        writer_factory: Callable[[Path, Path], Any] = RfidCsvWriter,
    ) -> None:
        self.config = config
        self.skellycam_client = skellycam_client
        self.writer_factory = writer_factory
        self.files: IntegratedSessionFiles | None = None
        self.writer: Any = None
        self.metadata: dict[str, Any] = {}

    def prepare(self, subject_id: str, action: str, trial_id: str, notes: str = "") -> IntegratedSessionFiles:
        self.files = create_integrated_session_files(self.config.output_dir)
        recording_name = build_recording_name(subject_id, action, trial_id)
        self.writer = self.writer_factory(self.files.rfid_reads_path, self.files.rfid_events_path)
        self.metadata = {
            "session_id": self.files.session_id,
            "trial_id": trial_id,
            "subject_id": subject_id,
            "action": action,
            "notes": notes,
            "recording_name": recording_name,
            "session_dir": str(self.files.session_dir),
            "skellycam_base_url": self.config.skellycam_base_url,
            "skellycam_recording_directory": self.config.skellycam_recording_dir,
            "rfid_reads_path": str(self.files.rfid_reads_path),
            "rfid_events_path": str(self.files.rfid_events_path),
            "sync_protocol": "Manual sync markers: sync_start and sync_end.",
            "sync_events": [],
        }
        return self.files

    def start_skellycam(self) -> dict[str, Any]:
        result = self.skellycam_client.start_recording(
            self.config.skellycam_base_url,
            self.metadata["recording_name"],
            self.config.skellycam_recording_dir,
        )
        self.metadata["skellycam_start"] = result
        return result

    def stop_skellycam(self) -> dict[str, Any]:
        result = self.skellycam_client.stop_recording(self.config.skellycam_base_url)
        self.metadata["skellycam_stop"] = result
        return result

    def write_event(self, event_type: str, notes: str = "") -> dict[str, Any]:
        if not self.files or not self.writer:
            raise RuntimeError("Session is not prepared")
        event = self.writer.write_event(self.files.session_id, self.metadata["trial_id"], event_type, notes)
        self.metadata.setdefault("sync_events", []).append(event)
        return event

    def finish(self) -> dict[str, Any]:
        if not self.files:
            raise RuntimeError("Session is not prepared")
        if self.writer:
            self.writer.close()
        write_session_meta(self.files.meta_path, self.metadata)
        return self.metadata
