import unittest
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np

import app_paths
from main import calcular_saturacao, compensar_desvio_lamina, converter_flecha, montar_relatorio_html
from reports import BancoDadosPN
from technical_data import GRANULOMETRIA_ESFERAS, NORMAS_REFERENCIA
from i18n import LANGUAGES, _TEXTS, load_language, save_language, technical_content, tr


class CalcularSaturacaoTests(unittest.TestCase):
    def setUp(self):
        self.idioma_anterior = load_language()
        save_language("PT")

    def tearDown(self):
        save_language(self.idioma_anterior)

    def test_ajuste_respeita_regra_dos_dez_por_cento(self):
        tempos = np.array([0.5, 1.0, 2.0, 4.0, 8.0])
        alturas = np.array([0.11, 0.17, 0.22, 0.24, 0.245])

        resultado = calcular_saturacao(tempos, alturas)

        self.assertGreater(resultado["t_sat"], 0)
        self.assertGreater(resultado["h_sat"], 0)
        self.assertGreaterEqual(resultado["r2"], 0)
        self.assertLessEqual(resultado["r2"], 1)
        self.assertAlmostEqual(
            (resultado["h_2sat"] - resultado["h_sat"]) / resultado["h_sat"],
            0.1,
            places=10,
        )

    def test_exige_quatro_medicoes_validas(self):
        with self.assertRaisesRegex(ValueError, "pelo menos 4 medições"):
            calcular_saturacao([1, 2, 3], [0.1, 0.2, 0.22])

    def test_rejeita_medicoes_sem_variacao_de_altura(self):
        with self.assertRaisesRegex(ValueError, "precisam variar"):
            calcular_saturacao([1, 2, 3, 4], [0.2, 0.2, 0.2, 0.2])

    def test_rejeita_tempo_negativo(self):
        with self.assertRaisesRegex(ValueError, "não podem ser negativos"):
            calcular_saturacao([-1, 1, 2, 3], [0.1, 0.2, 0.22, 0.23])

    def test_converte_milimetros_para_polegadas_e_vice_versa(self):
        polegadas = converter_flecha(25.4, "mm", "in")
        self.assertAlmostEqual(polegadas, 1.0)
        self.assertAlmostEqual(converter_flecha(polegadas, "in", "mm"), 25.4)

    def test_compensa_desvio_positivo_subtraindo_da_medicao(self):
        alturas = compensar_desvio_lamina([0.110, 0.170, 0.220, 0.240], 0.005)
        np.testing.assert_allclose(alturas, [0.105, 0.165, 0.215, 0.235])

    def test_compensa_um_desvio_para_cada_lamina(self):
        alturas = compensar_desvio_lamina([0.110, 0.170, 0.220, 0.240], [0.005, -0.002, 0.0, 0.010])
        np.testing.assert_allclose(alturas, [0.105, 0.172, 0.220, 0.230])

    def test_calculo_preserva_os_desvios_individuais_compensados(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
            [0.005, 0.004, 0.003, 0.002, 0.001],
        )

        np.testing.assert_allclose(resultado["h_data_compensada"], [0.105, 0.166, 0.217, 0.238, 0.244])
        np.testing.assert_allclose(resultado["desvios_lamina"], [0.005, 0.004, 0.003, 0.002, 0.001])

    def test_rejeita_compensacao_que_torna_flecha_negativa(self):
        with self.assertRaisesRegex(ValueError, "compensada negativa"):
            calcular_saturacao([1, 2, 3, 4], [0.1, 0.2, 0.22, 0.23], 0.11)

    def test_tabela_de_granulometria_tem_designacoes_principais(self):
        tamanhos = {linha[0]: linha[2] for linha in GRANULOMETRIA_ESFERAS}
        self.assertEqual(tamanhos["S110"], "0,279")
        self.assertEqual(tamanhos["S780"], "1,981")

    def test_tabela_de_normas_cobre_midia_e_curva_de_saturacao(self):
        normas = {linha[0] for linha in NORMAS_REFERENCIA}
        self.assertTrue({"SAE J444", "SAE J827", "SAE J443", "SAE J2597"}.issubset(normas))

    def test_relatorio_html_inclui_dados_tecnicos_e_escapa_campos(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
        )
        relatorio = montar_relatorio_html(
            {"Nome da peça": "Eixo <A>"},
            "SAE J443 e SAE J2597",
            {"Cobertura": "200%"},
            resultado,
            "mm",
            "s",
            "YWJj",
        )

        self.assertIn("Eixo &lt;A&gt;", relatorio)
        self.assertIn("SAE J443 e SAE J2597", relatorio)
        self.assertIn("Tempo de saturação (T)", relatorio)
        self.assertIn("data:image/png;base64,YWJj", relatorio)

    def test_relatorio_mantem_dados_de_equipamento_em_sequencia(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
        )
        parametros = {
            "Equipamento": "Máquina A",
            "Bico": "B-12",
            "Injetor": "I-08",
            "Distância": "120 mm",
            "Ângulo": "90 °",
            "Pressão": "4 bar",
        }

        relatorio = montar_relatorio_html({}, "SAE J443", parametros, resultado, "mm", "s", "YWJj")
        posicoes = [relatorio.index(rotulo) for rotulo in parametros]

        self.assertEqual(posicoes, sorted(posicoes))

    def test_banco_de_pn_salva_busca_atualiza_e_remove_cadastro(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            banco.salvar(
                {
                    "Peça / PN": "PN-0042",
                    "SN da peça": "SN-001",
                    "Referência": "REF-19",
                    "Equipamento": "Turbina 1",
                    "Bico": "8",
                    "Unidade de Bico": "mm",
                    "Injetor": "3/8",
                    "Unidade de Injetor": "in",
                    "Pressão": "4",
                    "Unidade de Pressão": "bar",
                }
            )

            self.assertEqual(banco.buscar("004"), ["PN-0042"])
            self.assertEqual(banco.buscar_registros("004"), [("PN-0042", "SN-001")])
            cadastro = banco.obter("pn-0042", "sn-001")
            self.assertEqual(cadastro["Referência"], "REF-19")
            self.assertEqual(cadastro["Unidade de Bico"], "mm")
            self.assertEqual(cadastro["Unidade de Injetor"], "in")
            self.assertEqual(cadastro["Unidade de Pressão"], "bar")

            banco.salvar({**cadastro, "Pressão": "5.5"})
            banco.salvar({**cadastro, "SN da peça": "SN-002", "Referência": "REF-20", "Pressão": "6"})
            self.assertEqual(banco.buscar("004"), ["PN-0042"])
            self.assertEqual(
                banco.buscar_registros("004"), [("PN-0042", "SN-001"), ("PN-0042", "SN-002")]
            )
            self.assertEqual(banco.obter("PN-0042", "SN-001")["Pressão"], "5.5")
            self.assertEqual(banco.obter("PN-0042", "SN-002")["Referência"], "REF-20")
            self.assertTrue(banco.remover("PN-0042", "SN-001"))
            self.assertIsNone(banco.obter("PN-0042", "SN-001"))
            self.assertEqual(banco.obter("PN-0042", "SN-002")["Referência"], "REF-20")

    def test_banco_migra_cadastro_legado_para_serial_vazio(self):
        with TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "cadastros.db"
            conexao = sqlite3.connect(caminho)
            try:
                conexao.execute(
                    "CREATE TABLE cadastros_pn (pn TEXT PRIMARY KEY COLLATE NOCASE, dados_json TEXT NOT NULL, atualizado_em TEXT NOT NULL)"
                )
                conexao.execute(
                    "INSERT INTO cadastros_pn VALUES (?, ?, ?)",
                    ("PN-LEGADO", '{"Peça / PN": "PN-LEGADO", "Desenho": "DWG-0"}', "2026-01-01T00:00:00"),
                )
                conexao.commit()
            finally:
                conexao.close()

            banco = BancoDadosPN(caminho)
            self.assertEqual(banco.obter("PN-LEGADO")["Referência"], "DWG-0")
            banco.salvar({"Peça / PN": "PN-LEGADO", "SN da peça": "SN-001", "Desenho": "DWG-1"})
            self.assertEqual(banco.buscar_registros("LEGADO"), [("PN-LEGADO", ""), ("PN-LEGADO", "SN-001")])
            self.assertEqual(banco.obter("PN-LEGADO", "SN-001")["Referência"], "DWG-1")

    def test_dados_persistentes_usam_pasta_local_do_usuario_e_migram_legado(self):
        with TemporaryDirectory() as diretorio:
            raiz = Path(diretorio)
            legado = raiz / "configuracoes.json"
            legado.write_text('{"language": "EN"}', encoding="utf-8")

            with patch.object(app_paths.sys, "platform", "win32"), patch.dict(
                app_paths.os.environ, {"LOCALAPPDATA": str(raiz / "AppData" / "Local")}, clear=False
            ), patch.object(app_paths, "_legacy_data_paths", return_value=(legado,)):
                destino = app_paths.user_data_file("configuracoes.json")

            self.assertEqual(destino, raiz / "AppData" / "Local" / "CurvSatApp" / "configuracoes.json")
            self.assertEqual(destino.read_text(encoding="utf-8"), '{"language": "EN"}')

    def test_dicionario_disponibiliza_pt_en_es_com_bandeiras(self):
        self.assertEqual(set(LANGUAGES), {"PT", "EN", "ES"})
        self.assertIn("🇧🇷", LANGUAGES["PT"])
        self.assertIn("🇺🇸", LANGUAGES["EN"])
        self.assertIn("🇪🇸", LANGUAGES["ES"])
        self.assertEqual(tr("settings", "EN"), "Settings")
        self.assertEqual(tr("settings", "ES"), "Configuración")

    def test_dicionario_tem_as_mesmas_chaves_em_todos_os_idiomas(self):
        chaves_pt = set(_TEXTS["PT"])
        self.assertEqual(set(_TEXTS["EN"]), chaves_pt)
        self.assertEqual(set(_TEXTS["ES"]), chaves_pt)
        self.assertEqual(technical_content("EN")["analysis"][2], ("Item", "Check", "Purpose"))
        self.assertEqual(technical_content("ES")["media"][0], "Tipos de medio")


if __name__ == "__main__":
    unittest.main()
