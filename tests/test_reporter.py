"""Tests for netsentry.reporter."""

import csv
import json
import os
import tempfile
import unittest

from netsentry import reporter


SAMPLE = [
    {"ip": "192.168.1.1", "hostname": "router", "status": "online"},
    {"ip": "192.168.1.5", "hostname": "phone", "status": "online"},
]


class TestSaveJson(unittest.TestCase):
    def test_json_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            reporter.save_json(SAMPLE, path, network="192.168.1.0/24")
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["network"], "192.168.1.0/24")
        self.assertEqual(len(data["devices"]), 2)
        self.assertEqual(data["devices"][0]["ip"], "192.168.1.1")

    def test_empty_devices(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.json")
            reporter.save_json([], path)
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["devices"], [])


class TestSaveCsv(unittest.TestCase):
    def test_csv_headers_and_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            reporter.save_csv(SAMPLE, path)
            with open(path, "r", encoding="utf-8", newline="") as fh:
                reader = csv.reader(fh)
                rows = list(reader)

        self.assertEqual(rows[0], ["ip", "hostname", "status"])
        self.assertEqual(rows[1], ["192.168.1.1", "router", "online"])
        self.assertEqual(rows[2], ["192.168.1.5", "phone", "online"])

    def test_empty_csv_has_only_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "empty.csv")
            reporter.save_csv([], path)
            with open(path, "r", encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh))
        self.assertEqual(rows, [["ip", "hostname", "status"]])


class TestPrintResults(unittest.TestCase):
    def test_handles_empty(self):
        reporter.print_results([], network="192.168.1.0/24")


if __name__ == "__main__":
    unittest.main()
