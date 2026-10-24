"""Testes da assinatura local dos artefatos de atualização."""

from __future__ import annotations

import base64
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from curvsat.security.release_signing import sign_manifest, verify_artifact, verify_manifest


class ReleaseSigningTests(unittest.TestCase):
    def test_rejects_tampered_manifest_or_artifact(self):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        public_key_b64 = base64.urlsafe_b64encode(public_key).decode("ascii").rstrip("=")
        with TemporaryDirectory() as directory:
            artifact = Path(directory) / "ASCC-System-9.9.9.exe"
            artifact.write_bytes(b"curvsat-release")
            manifest = sign_manifest({
                "app": "CurvSat",
                "version": "9.9.9",
                "release_notes": "Teste",
                "download_url": "https://updates.example/ASCC-System-9.9.9.exe",
            }, artifact, private_key)

            self.assertTrue(verify_manifest(manifest, public_key_b64))
            self.assertTrue(verify_artifact(artifact, manifest))

            artifact.write_bytes(b"alterado")
            self.assertFalse(verify_artifact(artifact, manifest))
            manifest["version"] = "9.9.10"
            self.assertFalse(verify_manifest(manifest, public_key_b64))


if __name__ == "__main__":
    unittest.main()
