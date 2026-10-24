"""Testes da comparação e leitura do manifesto de atualizações."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from curvsat.services import updates as update_service
from curvsat.security.release_signing import sign_manifest


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class UpdateServiceTests(unittest.TestCase):
    def test_compares_semantic_versions(self):
        self.assertTrue(update_service.is_newer_version("1.2.0", "1.1.9"))
        self.assertTrue(update_service.is_newer_version("2.0.0", "1.99.99"))
        self.assertFalse(update_service.is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(update_service.is_newer_version("1.0.0-beta", "1.0.0"))
        self.assertTrue(update_service.is_newer_version("1.0.0", "1.0.0-beta"))

    @patch("curvsat.services.updates.urlopen")
    def test_returns_update_when_manifest_has_newer_version(self, mocked_urlopen):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        manifest = sign_manifest({
            "app": "CurvSat", "version": "1.1.0", "release_notes": "Melhorias de estabilidade.",
            "download_url": "https://updates.example.com/curvsat-1.1.0.exe",
        }, __import__("pathlib").Path(__file__), private_key)
        mocked_urlopen.return_value = _Response(manifest)

        with patch.object(update_service, "RELEASE_MANIFEST_PUBLIC_KEY", __import__("base64").urlsafe_b64encode(public_key).decode("ascii").rstrip("=")):
            update = update_service.check_for_update(current_version="1.0.0")

        self.assertIsNotNone(update)
        self.assertEqual(update.version, "1.1.0")
        self.assertEqual(update.download_url, "https://updates.example.com/curvsat-1.1.0.exe")
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 4.0)

    @patch("curvsat.services.updates.urlopen")
    def test_ignores_invalid_or_current_manifest(self, mocked_urlopen):
        mocked_urlopen.return_value = _Response({"app": "CurvSat", "version": "1.0.0"})
        self.assertIsNone(update_service.check_for_update(current_version="1.0.0"))

        mocked_urlopen.return_value = _Response({"app": "Outro", "version": "2.0.0"})
        self.assertIsNone(update_service.check_for_update(current_version="1.0.0"))

    @patch("curvsat.services.updates.urlopen")
    def test_ignores_manifest_with_modified_signed_content(self, mocked_urlopen):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        manifest = sign_manifest({
            "app": "CurvSat", "version": "1.1.0", "release_notes": "Original",
            "download_url": "https://updates.example.com/curvsat-1.1.0.exe",
        }, __import__("pathlib").Path(__file__), private_key)
        manifest["version"] = "9.9.9"
        mocked_urlopen.return_value = _Response(manifest)

        with patch.object(update_service, "RELEASE_MANIFEST_PUBLIC_KEY", __import__("base64").urlsafe_b64encode(public_key).decode("ascii").rstrip("=")):
            self.assertIsNone(update_service.check_for_update(current_version="1.0.0"))

    @patch("curvsat.services.updates.urlopen", side_effect=OSError("offline"))
    def test_network_failure_does_not_interrupt_application(self, _mocked_urlopen):
        self.assertIsNone(update_service.check_for_update())


if __name__ == "__main__":
    unittest.main()
