"""Testes do merge local usado pela sincroniza\u00e7\u00e3o entre computadores."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reports import BancoDadosPN, criar_dados_relatorio


class DataSyncTests(unittest.TestCase):
    def test_import_keeps_newer_local_record_and_applies_remote_tombstone(self):
        with TemporaryDirectory() as directory:
            banco = BancoDadosPN(Path(directory) / "dados.db")
            banco.salvar({"Peça / PN": "PN-LOCAL", "Observações": "local"})
            exported = banco.exportar_para_sincronizacao()

            result = banco.importar_da_sincronizacao([
                {"pn": "PN-LOCAL", "serial_number": "", "data": {"Peça / PN": "PN-LOCAL"},
                 "curve": None, "updated_at": "2000-01-01T00:00:00", "deleted": False},
                {"pn": "PN-REMOTO", "serial_number": "", "data": {"Peça / PN": "PN-REMOTO"},
                 "curve": {"tempos": [1, 2, 3, 4]}, "updated_at": "2099-01-01T00:00:00", "deleted": False},
            ], [])
            self.assertEqual(result["records"], 1)
            self.assertEqual(banco.obter("PN-LOCAL")["Observações"], "local")
            self.assertIsNotNone(banco.obter("PN-REMOTO"))

            self.assertTrue(banco.remover("PN-REMOTO"))
            tombstone = next(record for record in banco.exportar_para_sincronizacao()["records"] if record["pn"] == "PN-REMOTO")
            self.assertTrue(tombstone["deleted"])
            self.assertIsInstance(tombstone["updated_at"], str)

    def test_import_does_not_count_records_that_are_already_current(self):
        with TemporaryDirectory() as directory:
            banco = BancoDadosPN(Path(directory) / "dados.db")
            dados = criar_dados_relatorio()
            dados[next(chave for chave in dados if "PN" in chave)] = "PN-ATUAL"
            banco.salvar(dados)
            records = banco.exportar_para_sincronizacao()["records"]

            self.assertEqual(banco.importar_da_sincronizacao(records, [])["records"], 0)

            self.assertTrue(banco.remover("PN-ATUAL"))
            tombstone = banco.exportar_para_sincronizacao()["records"]
            self.assertEqual(banco.importar_da_sincronizacao(tombstone, [])["records"], 0)

    def test_import_preserves_reports_and_renames_number_collision(self):
        with TemporaryDirectory() as directory:
            banco = BancoDadosPN(Path(directory) / "dados.db")

            def render(number, _issued):
                return f"<html>{number}</html>"

            banco.emitir_relatorio("REL", "PN-1", "", render)
            result = banco.importar_da_sincronizacao([], [{
                "numero": "REL-001-26", "prefixo": "REL", "ano": 2026, "sequencia": 1,
                "emitido_em": "2026-01-01T10:00", "pn": "PN-2", "serial_number": "",
                "conteudo_html": "<html>remoto</html>", "sha256": "a" * 64,
                "criado_em": "2026-01-01T10:00:00",
            }])
            self.assertEqual(result["reports"], 1)
            numbers = [report["numero"] for report in banco.buscar_relatorios_emitidos()]
            self.assertIn("REL-001-26-AAAAAA", numbers)

    def test_report_deletion_is_exported_and_applied_as_tombstone(self):
        with TemporaryDirectory() as directory:
            origem = BancoDadosPN(Path(directory) / "origem.db")
            destino = BancoDadosPN(Path(directory) / "destino.db")

            origem.emitir_relatorio("REL", "PN-1", "", lambda number, _issued: f"<html>{number}</html>")
            primeiro_envio = origem.exportar_para_sincronizacao()["reports"]
            self.assertEqual(destino.importar_da_sincronizacao([], primeiro_envio)["reports"], 1)

            relatorio = origem.buscar_relatorios_emitidos()[0]
            removido = origem.remover_relatorio_emitido(relatorio["id"])
            self.assertEqual(removido["numero"], relatorio["numero"])
            tombstone = origem.exportar_para_sincronizacao()["reports"][0]
            self.assertTrue(tombstone["deleted"])

            self.assertEqual(destino.importar_da_sincronizacao([], [tombstone])["reports"], 1)
            self.assertEqual(destino.buscar_relatorios_emitidos(), [])


if __name__ == "__main__":
    unittest.main()
