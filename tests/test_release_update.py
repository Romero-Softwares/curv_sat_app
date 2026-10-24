"""Testes do preparo dos arquivos de publicação."""

from __future__ import annotations

import unittest

from curvsat.tools import release_update


class ReleaseUpdateTests(unittest.TestCase):
    def test_renderizacao_atualiza_metadados_do_executavel(self):
        version = "1.0.5"
        executable_name = f"{release_update.ARTIFACT_PREFIX}-{version}"
        rendered = release_update.render_release_files(
            version,
            "Teste dos metadados do executável.",
            f"https://updates.example/{executable_name}.exe",
        )
        version_info = rendered[release_update.VERSION_INFO_FILE]

        self.assertIn("filevers=(1, 0, 5, 0)", version_info)
        self.assertIn("prodvers=(1, 0, 5, 0)", version_info)
        self.assertIn("StringStruct('FileVersion', '1.0.5')", version_info)
        self.assertIn("StringStruct('ProductVersion', '1.0.5')", version_info)
        self.assertIn("StringStruct('OriginalFilename', 'ASCC-System-1.0.5.exe')", version_info)
        self.assertIn("StringStruct('CompanyName',", version_info)
        self.assertIn("StringStruct('FileDescription',", version_info)
        self.assertIn("StringStruct('LegalCopyright',", version_info)
        self.assertIn("StringStruct('ProductName',", version_info)


if __name__ == "__main__":
    unittest.main()
