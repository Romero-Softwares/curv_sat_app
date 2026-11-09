import unittest

from curvsat.core.sieve_analysis import (
    analisar_amostra_peneiras,
    limites_midia_em_uso_para_designacao,
    peneira_nominal_para_designacao,
    peneiras_para_designacao,
)
from curvsat.ui.sieve_analysis import _TEXTOS, gerar_html_impressao_analise_peneiras


class AnalisePeneirasTests(unittest.TestCase):
    def test_rotulo_da_aba_de_peneiramento_e_traduzido(self):
        self.assertEqual(_TEXTOS["PT"]["aba"], "Granulometria por peneiramento")
        self.assertEqual(_TEXTOS["EN"]["aba"], "Sieve analysis")
        self.assertEqual(_TEXTOS["ES"]["aba"], "Granulometría por tamizado")

    def test_s110_tem_peneiras_e_medidas_corretas(self):
        peneiras = peneiras_para_designacao("s110")
        self.assertEqual([p.numero for p in peneiras], [30, 35, 50, 80])
        self.assertEqual(peneiras[0].abertura_mm, 0.600)
        self.assertEqual(peneiras[-1].abertura_mm, 0.180)

    def test_s170_tem_limites_e_peneiras_normativos(self):
        peneiras = peneiras_para_designacao("S170")

        self.assertEqual([p.numero for p in peneiras], [20, 25, 40, 45])
        self.assertEqual([p.limite for p in peneiras], [0, 10, 85, 97])

    def test_peneira_nominal_da_s230_e_a_30(self):
        peneira = peneira_nominal_para_designacao("S230")

        self.assertEqual(peneira.numero, 30)
        self.assertEqual(peneira.abertura_mm, 0.600)

    def test_limites_ams2430_de_midia_em_uso_da_s230(self):
        limites = limites_midia_em_uso_para_designacao("S230")

        self.assertEqual(limites.peneira_retida_max, 18)
        self.assertEqual(limites.peneira_passante_max, 30)

    def test_esfera_usada_s780_inclui_a_peneira_6_da_ams2430(self):
        resultado = analisar_amostra_peneiras(
            "S780", {6: 0.5, 7: 4, 10: 75.5, 12: 19, "fundo": 1}, tipo_amostra="usada",
        )

        self.assertEqual([linha["peneira"] for linha in resultado["linhas"]], [6, 7, 10, 12])
        self.assertTrue(resultado["midia_em_uso_conforme"])
        self.assertTrue(resultado["linhas"][0]["conforme_midia_em_uso"])
        self.assertTrue(resultado["linhas"][2]["conforme_midia_em_uso"])

    def test_s230_reprova_mais_de_dez_porcento_retido_na_peneira_20(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0, 20: 11, 30: 74, 35: 12, "fundo": 3},
        )

        self.assertFalse(resultado["conforme"])
        self.assertEqual(resultado["linhas"][1]["limite"], 10)
        self.assertFalse(resultado["linhas"][1]["conforme"])

    def test_s230_exibe_limites_cumulativos_e_passantes_equivalentes(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0, 20: 5, 30: 80, 35: 12, "fundo": 3},
        )

        linha_30 = resultado["linhas"][2]
        linha_35 = resultado["linhas"][3]
        self.assertTrue(resultado["conforme"])
        self.assertEqual(linha_30["percentual_retido"], 80.0)
        self.assertEqual(linha_30["percentual_retido_acumulado"], 85.0)
        self.assertEqual(linha_30["percentual_passante"], 15.0)
        self.assertEqual(linha_30["limite_passante_max"], 15.0)
        self.assertEqual(linha_35["percentual_retido"], 12.0)
        self.assertEqual(linha_35["percentual_retido_acumulado"], 97.0)
        self.assertEqual(linha_35["percentual_passante"], 3.0)
        self.assertEqual(linha_35["limite_passante_max"], 3.0)

    def test_amostra_s110_de_100g_dentro_dos_limites_e_conforme(self):
        resultado = analisar_amostra_peneiras(
            "S110", {30: 0, 35: 4, 50: 76, 80: 10, "fundo": 10},
        )

        self.assertTrue(resultado["massa_conforme"])
        self.assertTrue(resultado["criterios_conformes"])
        self.assertTrue(resultado["conforme"])
        self.assertAlmostEqual(resultado["linhas"][2]["percentual_retido_acumulado"], 80.0)
        self.assertAlmostEqual(resultado["linhas"][3]["percentual_retido_acumulado"], 90.0)
        self.assertEqual(resultado["fundo_limite_max"], 10.0)
        self.assertTrue(resultado["fundo_conforme"])

    def test_reprova_retencao_acima_do_maximo(self):
        resultado = analisar_amostra_peneiras(
            "S110", {30: 0, 35: 11, 50: 79, 80: 0, "fundo": 10},
        )

        self.assertFalse(resultado["conforme"])
        self.assertFalse(resultado["linhas"][1]["conforme"])

    def test_fundo_e_coletor_do_passante_sem_criterio_independente(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0, 20: 5, 30: 80, 35: 11, "fundo": 4},
        )

        self.assertEqual(resultado["fundo_limite_max"], 3.0)
        self.assertFalse(resultado["fundo_conforme"])
        self.assertFalse(resultado["linhas"][-1]["conforme"])
        self.assertFalse(resultado["fundo_criterio_independente"])
        self.assertEqual(resultado["fundo_referencia_peneira"], 35)

    def test_amostra_fora_de_100g_nao_e_aprovada(self):
        resultado = analisar_amostra_peneiras(
            "S780", {7: 0, 10: 4, 12: 1, "fundo": 90},
        )

        self.assertAlmostEqual(resultado["massa_total_g"], 95.0)
        self.assertFalse(resultado["massa_conforme"])
        self.assertFalse(resultado["conforme"])

    def test_esfera_usada_aplica_limites_ams2430_sem_aprovacao_j444_de_compra(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0, 20: 5, 30: 80, 35: 12, "fundo": 3}, tipo_amostra="usada",
        )

        self.assertEqual(resultado["tipo_amostra"], "usada")
        self.assertFalse(resultado["criterios_normativos_aplicaveis"])
        self.assertTrue(resultado["massa_conforme"])
        self.assertTrue(resultado["criterios_j444_conformes"])
        self.assertIsNone(resultado["criterios_conformes"])
        self.assertIsNone(resultado["conforme"])
        self.assertIsNone(resultado["linhas"][2]["conforme"])
        self.assertTrue(resultado["midia_em_uso_conforme"])
        self.assertTrue(resultado["linhas"][0]["conforme_midia_em_uso"])
        self.assertTrue(resultado["linhas"][2]["conforme_midia_em_uso"])

    def test_esfera_usada_aprova_os_dois_limites_ams2430(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0.5, 20: 10, 30: 70, 35: 19, "fundo": 0.5}, tipo_amostra="usada",
        )

        self.assertTrue(resultado["massa_conforme"])
        self.assertEqual(resultado["peneira_retida_max_midia_em_uso"], 18)
        self.assertEqual(resultado["peneira_passante_max_midia_em_uso"], 30)
        self.assertEqual(resultado["percentual_retido_peneira_retida_max"], 0.5)
        self.assertEqual(resultado["percentual_passante_peneira_passante_max"], 19.5)
        self.assertTrue(resultado["midia_em_uso_conforme"])
        self.assertTrue(resultado["linhas"][0]["conforme_midia_em_uso"])
        self.assertTrue(resultado["linhas"][2]["conforme_midia_em_uso"])

    def test_esfera_usada_reprova_retencao_grossa_acima_do_limite_ams2430(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0.6, 20: 10, 30: 70, 35: 19, "fundo": 0.4}, tipo_amostra="usada",
        )

        self.assertFalse(resultado["midia_em_uso_conforme"])
        self.assertFalse(resultado["linhas"][0]["conforme_midia_em_uso"])
        self.assertTrue(resultado["linhas"][2]["conforme_midia_em_uso"])

    def test_esfera_usada_reprova_finos_acima_do_limite_ams2430(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0.5, 20: 10, 30: 69, 35: 20, "fundo": 0.5}, tipo_amostra="usada",
        )

        self.assertFalse(resultado["midia_em_uso_conforme"])
        self.assertTrue(resultado["linhas"][0]["conforme_midia_em_uso"])
        self.assertFalse(resultado["linhas"][2]["conforme_midia_em_uso"])

    def test_relatorio_de_impressao_mostra_limites_ams_e_codigo(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0.5, 20: 10, 30: 70, 35: 19, "fundo": 0.5}, tipo_amostra="usada",
        )

        conteudo = gerar_html_impressao_analise_peneiras(
            resultado, "CONFORME AMS 2430", _TEXTOS["PT"], "Usada - controle de mídia AMS 2430", "P000123",
        )

        self.assertIn("Imprimir", _TEXTOS["PT"]["imprimir"])
        self.assertIn("CONFORME AMS 2430", conteudo)
        self.assertIn("Código / identificador: P000123", conteudo)
        self.assertIn("passante ≤ 20%", conteudo)
        self.assertIn("Fundo da pilha", conteudo)

    def test_relatorio_do_historico_usa_condicao_do_resultado(self):
        resultado = analisar_amostra_peneiras(
            "S230", {18: 0.5, 20: 10, 30: 70, 35: 19, "fundo": 0.5}, tipo_amostra="usada",
        )

        conteudo = gerar_html_impressao_analise_peneiras(
            resultado, "CONFORME AMS 2430", _TEXTOS["PT"], "Nova - especificação SAE J444", "P000124",
        )

        self.assertIn("Resultado — S230", conteudo)
        self.assertIn("Usada - controle de mídia AMS 2430", conteudo)
        self.assertNotIn("Nova - especificação SAE J444", conteudo)

    def test_tipo_de_amostra_invalido_e_rejeitado(self):
        with self.assertRaisesRegex(ValueError, "Tipo de amostra inválido"):
            analisar_amostra_peneiras("S110", {30: 0, 35: 4, 50: 76, 80: 10, "fundo": 10}, tipo_amostra="recuperada")


if __name__ == "__main__":
    unittest.main()
