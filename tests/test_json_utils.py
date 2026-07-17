#!/usr/bin/env python3
"""Offline tests for Tracer's JSON serialization helpers."""

import dataclasses
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.json_utils import load_json, save_json, serialize_json


@dataclasses.dataclass
class ExampleRecord:
    name: str
    count: int


class JsonUtilsTest(unittest.TestCase):
    def test_serializes_supported_objects(self):
        timestamp = datetime(2025, 5, 20, 12, 0, tzinfo=timezone.utc)
        payload = {
            "record": ExampleRecord(name="step", count=2),
            "created_at": timestamp,
        }

        decoded = json.loads(serialize_json(payload))

        self.assertEqual(decoded["record"], {"name": "step", "count": 2})
        self.assertEqual(decoded["created_at"], timestamp.isoformat())

    def test_save_and_load_round_trip(self):
        payload = {"status": "review_required", "steps": ["open", "observe"]}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "result.json"
            save_json(payload, str(output_path))
            self.assertEqual(load_json(str(output_path)), payload)


if __name__ == "__main__":
    unittest.main()
