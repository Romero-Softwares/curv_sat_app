"""Testes das preferências e exclusão mútua da sincronização."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import license_service


class LicenseServiceTests(unittest.TestCase):
    def test_automatic_sync_preference_is_local_and_persistent(self):
        with TemporaryDirectory() as directory:
            license_file = Path(directory) / "licenca.json"
            with patch("license_service._license_file", return_value=license_file):
                self.assertFalse(license_service.is_automatic_data_sync_enabled())
                license_service.set_automatic_data_sync_enabled(True)
                self.assertTrue(license_service.is_automatic_data_sync_enabled())
                self.assertTrue(json.loads(license_file.read_text(encoding="utf-8"))["automatic_data_sync"])

                license_service.set_automatic_data_sync_enabled(False)
                self.assertFalse(license_service.is_automatic_data_sync_enabled())

    def test_second_concurrent_sync_returns_busy(self):
        acquired = license_service._system_data_sync_lock.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            result = license_service.sync_active_system_data()
        finally:
            license_service._system_data_sync_lock.release()
        self.assertEqual(result["result"], "busy")


if __name__ == "__main__":
    unittest.main()
