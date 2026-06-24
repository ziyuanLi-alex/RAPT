from __future__ import annotations

import time
from typing import Any

import requests


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _timed_request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    before_ns = time.perf_counter_ns()
    response = requests.request(method, url, timeout=10, **kwargs)
    after_ns = time.perf_counter_ns()
    response.raise_for_status()
    return {
        "url": url,
        "status_code": response.status_code,
        "response_text": response.text,
        "before_perf_counter_ns": before_ns,
        "after_perf_counter_ns": after_ns,
        "midpoint_perf_counter_ns": (before_ns + after_ns) // 2,
    }


def check_health(base_url: str) -> dict[str, Any]:
    """Check the SkellyCam HTTP service."""
    return _timed_request("GET", _url(base_url, "/health"))


def start_recording(
    base_url: str,
    recording_name: str,
    recording_directory: str,
    mic_device_index: int = -1,
) -> dict[str, Any]:
    """Start a SkellyCam recording and return HTTP response plus timing metadata."""
    payload = {
        "recording_name": recording_name,
        "recording_directory": recording_directory,
        "mic_device_index": mic_device_index,
    }
    result = _timed_request("POST", _url(base_url, "/skellycam/camera/group/all/record/start"), json=payload)
    result["request_payload"] = payload
    return result


def stop_recording(base_url: str) -> dict[str, Any]:
    """Stop the current SkellyCam recording and return HTTP response plus timing metadata."""
    return _timed_request("GET", _url(base_url, "/skellycam/camera/group/all/record/stop"))
