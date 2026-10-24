"""Testes de integração do emissor local de chaves de ativação."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from curvsat.services.license import _parse_activation_code


GENERATOR_FILE = PROJECT_DIR / "license_generator.py"
INSTALLATION_KEY = "CSAT-ABCDE-FGHIJ-KLMNO-PQRST-UVWXY"


class LicenseGeneratorTests(unittest.TestCase):
    def test_generates_activation_file_from_another_working_directory(self):
        """O duplo clique não pode depender da pasta atual do processo."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "activation.txt"
            process = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR_FILE),
                    INSTALLATION_KEY,
                    "Empresa de Teste",
                    "--output",
                    str(output_file),
                ],
                cwd=temp_dir,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(process.returncode, 0, process.stderr)
            saved = output_file.read_text(encoding="utf-8")
            activation_code = saved.strip().splitlines()[-1]
            self.assertTrue(activation_code.startswith("CSAT-A1."))
            payload = _parse_activation_code(activation_code)
            self.assertEqual(payload["organization"], "Empresa de Teste")
            self.assertNotIn("installation_key", payload)


if __name__ == "__main__":
    unittest.main()
