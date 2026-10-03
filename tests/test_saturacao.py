import unittest

import numpy as np

from main import calcular_saturacao, compensar_desvio_lamina, converter_flecha
from technical_data import GRANULOMETRIA_ESFERAS, NORMAS_REFERENCIA


class CalcularSaturacaoTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
