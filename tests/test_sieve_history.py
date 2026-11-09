import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from curvsat.services.sieve_history import HistoricoAnalisesPeneiras, formatar_data_historico


def _resultado(conforme=True):
    return {
        "designacao": "S230",
        "tipo_amostra": "nova",
        "massa_total_g": 100.0,
        "massa_conforme": True,
        "criterios_normativos_aplicaveis": True,
        "conforme": conforme,
        "midia_em_uso_conforme": None,
        "linhas": [],
    }


class HistoricoAnalisesPeneirasTests(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.historico = HistoricoAnalisesPeneiras(Path(self.diretorio.name) / "analises.db")

    def tearDown(self):
        self.diretorio.cleanup()

    def test_salva_codigo_automatico_e_localiza_por_codigo(self):
        salvo = self.historico.salvar(_resultado(), {18: 0, "fundo": 3}, data_analise=datetime(2026, 11, 7, 14, 30))

        self.assertEqual(salvo["codigo"], "P000001")
        encontrados = self.historico.buscar(codigo="000001")
        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0]["situacao"], "conforme")
        self.assertEqual(encontrados[0]["massas"]["fundo"], 3)

    def test_filtra_por_data_e_nao_conforme(self):
        self.historico.salvar(_resultado(), {}, codigo="LOTE-01", data_analise=datetime(2026, 11, 7, 8, 0))
        self.historico.salvar(_resultado(False), {}, codigo="LOTE-02", data_analise=datetime(2026, 11, 8, 8, 0))

        encontrados = self.historico.buscar(data="08/11/2026", situacao="nao_conforme")
        self.assertEqual([registro["codigo"] for registro in encontrados], ["LOTE-02"])

    def test_formata_data_do_banco_para_o_cabecalho_do_historico(self):
        exibida = formatar_data_historico("2026-11-07 14:49:18")

        self.assertEqual(exibida, "07/11/2026 14:49:18")

    def test_rejeita_codigo_duplicado(self):
        self.historico.salvar(_resultado(), {}, codigo="LOTE-01")

        with self.assertRaisesRegex(ValueError, "Já existe"):
            self.historico.salvar(_resultado(), {}, codigo="LOTE-01")


if __name__ == "__main__":
    unittest.main()
