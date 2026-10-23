import unittest
import sqlite3
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
from matplotlib.figure import Figure

import app_paths
from main import (
    AlmenApp,
    TIPOS_LAMINA,
    calcular_saturacao,
    compensar_desvio_lamina,
    configurar_escala_vertical,
    configurar_compatibilidade_visual,
    converter_arco,
    eh_windows_8,
    montar_relatorio_html,
)
from reports import (
    BancoDadosPN,
    CAMPO_UNIDADE_RELATORIO,
    calcular_sha256_relatorio,
    criar_dados_relatorio,
    destacar_faixa_intensidade,
    extrair_faixa_intensidade,
    remover_destaque_faixa_intensidade,
)
from technical_data import GRANULOMETRIA_ESFERAS, NORMAS_REFERENCIA
from i18n import LANGUAGES, _TEXTS, load_language, save_language, technical_content, tr


class CalcularSaturacaoTests(unittest.TestCase):
    def setUp(self):
        self.idioma_anterior = load_language()
        save_language("PT")

    def tearDown(self):
        save_language(self.idioma_anterior)

    def test_tipos_de_lamina_exibem_apenas_siglas(self):
        self.assertEqual([tr(chave, "PT") for chave in TIPOS_LAMINA.values()], ["N", "A", "C"])

    def test_router_e_esfera_sem_seletor_de_unidade(self):
        dados = criar_dados_relatorio()

        self.assertIn("Router", dados)
        self.assertNotIn("Ordem de Serviço", dados)
        self.assertIn("Esfera", dados)
        self.assertNotIn("Esfera", CAMPO_UNIDADE_RELATORIO)
        self.assertNotIn("Unidade de Esfera", dados)
        self.assertEqual(tr("piece_pn", "PT"), "PN")
        self.assertEqual(tr("piece_pn", "EN"), "PN")
        self.assertEqual(tr("piece_pn", "ES"), "PN")
        self.assertEqual(tr("reference_cmm", "PT"), "Referência CMM")
        self.assertEqual(tr("reference_cmm", "EN"), "CMM Reference")
        self.assertEqual(tr("reference_cmm", "ES"), "Referencia CMM")

        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            banco.salvar({"Router": "Router 01", "Peça / PN": "PN-ROUTER", "Ordem de Serviço": "OS-2026-0042", "Esfera": "S230"})
            cadastro = banco.obter("PN-ROUTER")

        self.assertNotIn("Ordem de Serviço", cadastro)
        self.assertEqual(cadastro["Router"], "Router 01")
        self.assertEqual(cadastro["Esfera"], "S230")

    def test_curva_salva_e_recarrega_desvios_de_lamina(self):
        class Entrada:
            def __init__(self, valor):
                self.valor = str(valor)

            def get(self):
                return self.valor

        class Selecao:
            def __init__(self, valor):
                self.valor = valor

            def get(self):
                return self.valor

        app = SimpleNamespace(
            _ultimo_resultado={"h_data_compensada": np.array([0.1011, 0.1710, 0.2211, 0.2410])},
            _obter_dados_entradas=lambda: (
                np.array([1.0, 2.0, 4.0, 8.0]),
                np.array([0.1000, 0.1700, 0.2200, 0.2400]),
                np.array([-0.0011, 0.0, -0.0011, 0.0]),
            ),
            rows=[
                {"tempo": Entrada(1), "altura": Entrada(0.1), "lamina_var": Selecao("L-NEG")},
                {"tempo": Entrada(2), "altura": Entrada(0.17), "lamina_var": Selecao("L-ZERO")},
                {"tempo": Entrada(4), "altura": Entrada(0.22), "lamina_var": Selecao("L-NEG")},
                {"tempo": Entrada(8), "altura": Entrada(0.24), "lamina_var": Selecao("L-ZERO")},
            ],
            desvios_laminas={"L-NEG": -0.0011, "L-ZERO": 0.0},
            unidade_arco="mm",
            tipo_lamina="A",
            tipo_exposicao="seconds",
        )

        curva = AlmenApp.curva_atual_para_salvar(app)

        self.assertEqual(curva["alturas"], [0.1, 0.17, 0.22, 0.24])
        self.assertEqual(curva["laminas"], ["L-NEG", "L-ZERO", "L-NEG", "L-ZERO"])
        self.assertEqual(curva["desvios_laminas"], {"L-NEG": -0.0011, "L-ZERO": 0.0})

        linhas_recarregadas = []
        app_recarregado = SimpleNamespace(
            unidade_arco="mm",
            tipo_lamina="A",
            tipo_exposicao="seconds",
            desvios_laminas={},
            _atualizar_textos_unidade=lambda: None,
            add_row=lambda tempo, altura, lamina=None: linhas_recarregadas.append((tempo, altura, lamina)),
        )
        self.assertTrue(AlmenApp._carregar_curva_salva(app_recarregado, curva))
        self.assertEqual(app_recarregado.desvios_laminas, curva["desvios_laminas"])
        self.assertEqual(linhas_recarregadas[0], (1.0, 0.1, "L-NEG"))
        self.assertEqual(linhas_recarregadas[1], (2.0, 0.17, "L-ZERO"))

    def test_indicador_informa_a_origem_dos_dados_da_curva(self):
        app = SimpleNamespace(
            _origem_curva={"tipo": "selected", "router": "Router 01", "pn": "PN-100", "sn": "SN-A"},
            t=lambda chave, **valores: tr(chave, "PT", **valores),
        )

        self.assertEqual(
            AlmenApp._texto_origem_curva(app),
            "Dados da curva exibida: cadastro selecionado — Router: Router 01 | PN: PN-100 | SN: SN-A",
        )

        app._origem_curva = {"tipo": "latest"}
        self.assertEqual(
            AlmenApp._texto_origem_curva(app),
            "Dados da curva exibida: última curva salva",
        )

    def test_detecta_windows_8_pelo_numero_de_compilacao(self):
        self.assertTrue(eh_windows_8("nt", 9200))
        self.assertTrue(eh_windows_8("nt", 9600))
        self.assertFalse(eh_windows_8("nt", 19045))
        self.assertFalse(eh_windows_8("posix", 9200))

    def test_compatibilidade_visual_do_windows_8_fixa_dpi_e_tema_claro(self):
        with patch("main.eh_windows_8", return_value=True), \
             patch("main.ctk.deactivate_automatic_dpi_awareness") as desativar_dpi, \
             patch("main.ctk.set_widget_scaling") as escalar_widgets, \
             patch("main.ctk.set_window_scaling") as escalar_janela, \
             patch("main.ctk.set_appearance_mode") as tema:
            self.assertTrue(configurar_compatibilidade_visual())

        desativar_dpi.assert_called_once_with()
        escalar_widgets.assert_called_once_with(1.0)
        escalar_janela.assert_called_once_with(1.0)
        tema.assert_called_once_with("Light")

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
        polegadas = converter_arco(25.4, "mm", "in")
        self.assertAlmostEqual(polegadas, 1.0)
        self.assertAlmostEqual(converter_arco(polegadas, "in", "mm"), 25.4)

    def test_mesma_curva_em_mm_e_in_produz_resultados_equivalentes(self):
        tempos = np.array([0.5, 1, 2, 4, 8, 16])
        alturas_mm = np.array([0.03143, 0.05923, 0.10681, 0.17557, 0.24837, 0.29112])
        alturas_in = np.array([converter_arco(altura, "mm", "in") for altura in alturas_mm])

        resultado_mm = calcular_saturacao(tempos, alturas_mm)
        resultado_in = calcular_saturacao(tempos, alturas_in)

        self.assertAlmostEqual(resultado_mm["t_sat"], resultado_in["t_sat"], places=8)
        self.assertAlmostEqual(
            resultado_mm["h_sat"],
            converter_arco(resultado_in["h_sat"], "in", "mm"),
            places=10,
        )
        self.assertAlmostEqual(
            resultado_mm["h_2sat"],
            converter_arco(resultado_in["h_2sat"], "in", "mm"),
            places=10,
        )

    def test_escala_vertical_em_milimetros_inicia_em_zero_e_ajusta_a_precisao(self):
        figura = Figure()
        eixo = figura.subplots()

        configurar_escala_vertical(eixo, [0.110, 0.170, 0.220, 0.240], "mm", (0.140, 0.180))

        limite_inferior, limite_superior = eixo.get_ylim()
        self.assertEqual(limite_inferior, 0)
        self.assertGreater(limite_superior, 0.240)
        self.assertEqual(eixo.yaxis.get_major_formatter()(0.11, 0), "0.11")

        eixo = figura.subplots()
        configurar_escala_vertical(eixo, [0.014, 0.016, 0.018], "mm")
        self.assertEqual(eixo.yaxis.get_major_formatter()(0.014, 0), "0.014")

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

    def test_rejeita_compensacao_que_torna_altura_do_arco_negativa(self):
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
            {"Router": "Router 01", "Nome da peça": "Eixo <A>"},
            "SAE J443 e SAE J2597",
            {"Cobertura": "200%"},
            resultado,
            "mm",
            "s",
            "YWJj",
        )

        self.assertIn("Eixo &lt;A&gt;", relatorio)
        self.assertNotIn(">ROUTER<", relatorio)
        self.assertIn("Router 01", relatorio)
        self.assertNotIn("Ordem de Serviço", relatorio)
        self.assertIn("SAE J443 e SAE J2597", relatorio)
        self.assertIn("Tempo de saturação (T)", relatorio)
        self.assertIn("data:image/png;base64,YWJj", relatorio)

    def test_relatorio_traduz_a_referencia_cmm_em_todos_os_idiomas(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
        )
        informacoes = {"Referencia-CMM": "CMM-42"}
        rotulos_esperados = {
            "PT": "Referência CMM",
            "EN": "CMM Reference",
            "ES": "Referencia CMM",
        }

        for idioma, rotulo in rotulos_esperados.items():
            save_language(idioma)
            relatorio = montar_relatorio_html(informacoes, "SAE J443", {}, resultado, "mm", "s", "YWJj")
            self.assertIn(f">{rotulo}</th><td>CMM-42</td>", relatorio)

    def test_relatorio_html_embute_logo_da_empresa_no_cabecalho(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
        )
        with TemporaryDirectory() as diretorio:
            logo = Path(diretorio) / "empresa.png"
            logo.write_bytes(b"logo de teste")
            relatorio = montar_relatorio_html({}, "SAE J443", {}, resultado, "mm", "s", "YWJj", logo)

        self.assertIn('class="logo-empresa"', relatorio)
        self.assertIn("data:image/png;base64,bG9nbyBkZSB0ZXN0ZQ==", relatorio)

    def test_relatorio_html_delimita_cabecalho_e_quebra_antes_dos_resultados(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0, 8.0],
            [0.110, 0.170, 0.220, 0.240, 0.245],
        )
        relatorio = montar_relatorio_html({}, "SAE J443", {}, resultado, "mm", "s", "YWJj")

        self.assertIn('class="cabecalho"', relatorio)
        self.assertIn("border: 1.5px solid #2f80c4", relatorio)
        self.assertIn("border-right: 1px solid #b7c9da", relatorio)
        self.assertIn("@page { size: A4; margin: 12mm; }", relatorio)
        self.assertIn("font-size: 18pt", relatorio)
        self.assertIn("min-height: 273mm", relatorio)
        self.assertIn('class="resultado-curva"', relatorio)
        self.assertIn('class="pagina-relatorio"', relatorio)
        for pagina in range(1, 4):
            self.assertIn(f'class="rodape-pagina">{tr("report_page")} {pagina}</footer>', relatorio)
        self.assertNotIn("counter(page)", relatorio)

    def test_relatorio_html_registra_leitura_desvio_negativo_e_compensacao(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0],
            [0.1100, 0.1700, 0.2200, 0.2400],
            [-0.0011, 0.0, 0.0, 0.0],
        )
        medicoes = [
            {
                "indice": 1,
                "lamina": "Lamina 01",
                "exposicao": 0.5,
                "altura_lida": 0.1100,
                "desvio": -0.0011,
                "altura_compensada": 0.1111,
            }
        ]

        relatorio = montar_relatorio_html({}, "SAE J443", {}, resultado, "mm", "s", "YWJj", medicoes_laminas=medicoes)

        self.assertIn('class="medicoes-laminas"', relatorio)
        self.assertIn("<td>0.5</td>", relatorio)
        self.assertNotIn("<td>0.5000</td>", relatorio)
        self.assertIn("-0.0011", relatorio)
        self.assertIn("0.1111", relatorio)
        self.assertIn("page-break-after: always", relatorio)

    def test_relatorio_html_deixa_assinaturas_para_preenchimento_impresso(self):
        resultado = calcular_saturacao(
            [0.5, 1.0, 2.0, 4.0],
            [0.1100, 0.1700, 0.2200, 0.2400],
        )

        relatorio = montar_relatorio_html(
            {}, "SAE J443", {}, resultado, "mm", "s", "YWJj",
            assinaturas={"Operador": "Ana Silva", "Inspetor Supervisor": "Bruno Lima"},
        )

        self.assertIn("Assinaturas", relatorio)
        self.assertIn("Operador", relatorio)
        self.assertIn("Inspetor Supervisor", relatorio)
        self.assertNotIn("Ana Silva", relatorio)
        self.assertNotIn("Bruno Lima", relatorio)
        self.assertIn('data-report-sha="true"', relatorio)

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

    def test_extrai_faixa_de_intensidade_com_virgula_ponto_e_sufixo_almen(self):
        self.assertEqual(extrair_faixa_intensidade("0,014-0.018A"), (0.014, 0.018))
        self.assertIsNone(extrair_faixa_intensidade("0,014A"))
        self.assertIsNone(extrair_faixa_intensidade("0.018-0.014A"))

    def test_destaque_de_intensidade_cria_area_e_duas_linhas_sem_alterar_grafico(self):
        figura = Figure()
        eixo = figura.subplots()
        eixo.set_ylim(0, 0.015)

        legenda = "Faixa de intensidade de peening: 0,014-0.018A mm"
        destaque = destacar_faixa_intensidade(eixo, "0,014-0.018A", "mm", "mm", legenda)

        self.assertEqual(len(eixo.patches), 1)
        self.assertEqual(len(eixo.lines), 2)
        self.assertGreater(eixo.get_ylim()[1], 0.018)
        self.assertEqual(eixo.patches[0].get_label(), legenda)

        remover_destaque_faixa_intensidade(eixo, destaque)
        self.assertEqual(len(eixo.patches), 0)
        self.assertEqual(len(eixo.lines), 0)
        self.assertEqual(eixo.get_ylim(), (0.0, 0.015))

    def test_banco_de_pn_salva_busca_atualiza_e_remove_cadastro(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            banco.salvar(
                {
                    "Router": "Router Principal",
                    "Peça / PN": "PN-0042",
                    "SN da peça": "SN-001",
                    "Referencia-CMM": "REF-19",
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
            self.assertEqual(banco.buscar_registros("principal"), [("PN-0042", "SN-001")])
            self.assertEqual(banco.buscar_registros("sn-001"), [("PN-0042", "SN-001")])
            cadastro = banco.obter("pn-0042", "sn-001")
            self.assertEqual(cadastro["Referencia-CMM"], "REF-19")
            self.assertEqual(cadastro["Unidade de Bico"], "mm")
            self.assertEqual(cadastro["Unidade de Injetor"], "in")
            self.assertEqual(cadastro["Unidade de Pressão"], "bar")

            banco.salvar({**cadastro, "Pressão": "5.5"})
            banco.salvar({**cadastro, "SN da peça": "SN-002", "Referencia-CMM": "REF-20", "Pressão": "6"})
            self.assertEqual(banco.buscar("004"), ["PN-0042"])
            self.assertEqual(
                banco.buscar_registros("004"), [("PN-0042", "SN-001"), ("PN-0042", "SN-002")]
            )
            self.assertEqual(banco.obter("PN-0042", "SN-001")["Pressão"], "5.5")
            self.assertEqual(banco.obter("PN-0042", "SN-002")["Referencia-CMM"], "REF-20")
            self.assertTrue(banco.remover("PN-0042", "SN-001"))
            self.assertIsNone(banco.obter("PN-0042", "SN-001"))
            self.assertEqual(banco.obter("PN-0042", "SN-002")["Referencia-CMM"], "REF-20")

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
            self.assertEqual(banco.obter("PN-LEGADO")["Referencia-CMM"], "DWG-0")
            banco.salvar({"Peça / PN": "PN-LEGADO", "SN da peça": "SN-001", "Desenho": "DWG-1"})
            banco.salvar({"Peça / PN": "PN-REFERENCIA", "Referência": "REF-LEG"})
            self.assertEqual(banco.buscar_registros("LEGADO"), [("PN-LEGADO", ""), ("PN-LEGADO", "SN-001")])
            self.assertEqual(banco.obter("PN-LEGADO", "SN-001")["Referencia-CMM"], "DWG-1")
            self.assertEqual(banco.obter("PN-REFERENCIA")["Referencia-CMM"], "REF-LEG")

    def test_banco_retorna_a_ultima_curva_salva(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            curva_antiga = {"tempos": [1, 2, 3, 4], "alturas": [0.1, 0.15, 0.19, 0.21]}
            curva_recente = {"tempos": [1, 2, 4, 8], "alturas": [0.1, 0.17, 0.22, 0.24]}
            banco.salvar({"Pe\u00e7a / PN": "PN-ANTIGO"}, curva_antiga)
            banco.salvar({"Pe\u00e7a / PN": "PN-RECENTE"}, curva_recente)

            self.assertEqual(banco.obter_ultima_curva(), curva_recente)

    def test_banco_retorna_a_curva_do_cadastro_selecionado(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            curva_a = {"tempos": [1, 2, 3, 4], "alturas": [0.1, 0.15, 0.19, 0.21]}
            curva_b = {"tempos": [1, 2, 4, 8], "alturas": [0.1, 0.17, 0.22, 0.24]}
            banco.salvar({"Peça / PN": "PN-100", "SN da peça": "SN-A"}, curva_a)
            banco.salvar({"Peça / PN": "PN-100", "SN da peça": "SN-B"}, curva_b)

            self.assertEqual(banco.obter_curva("PN-100", "SN-A"), curva_a)
            self.assertEqual(banco.obter_curva("PN-100", "SN-B"), curva_b)
            self.assertIsNone(banco.obter_curva("PN-100", "SN-INEXISTENTE"))

    def test_emissao_de_relatorio_sequencia_por_prefixo_ano_e_preserva_reimpressao(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")

            def renderizar(numero, emitido_em):
                return f"<html><body>{numero}|{emitido_em:%d/%m/%Y %H:%M}</body></html>"

            with patch("reports.datetime") as relogio:
                relogio.now.return_value = datetime(2026, 8, 10, 14, 30)
                primeiro = banco.emitir_relatorio("sp", "PN-100", "SN-7", renderizar)
                relogio.now.return_value = datetime(2026, 8, 11, 9, 5)
                segundo = banco.emitir_relatorio("SP", "PN-101", "", renderizar)
                relogio.now.return_value = datetime(2027, 1, 2, 8, 0)
                proximo_ano = banco.emitir_relatorio("SP", "PN-102", "", renderizar)

            self.assertEqual(primeiro["numero"], "SP-001-26")
            self.assertEqual(segundo["numero"], "SP-002-26")
            self.assertEqual(proximo_ano["numero"], "SP-001-27")
            encontrados = banco.buscar_relatorios_emitidos("PN-100")
            self.assertEqual(len(encontrados), 1)
            arquivado = banco.obter_relatorio_emitido(encontrados[0]["id"])
            self.assertEqual(arquivado["numero"], primeiro["numero"])
            self.assertEqual(arquivado["conteudo_html"], primeiro["conteudo_html"])

    def test_emissao_nao_reinicia_sequencia_apos_excluir_e_reabrir_no_mesmo_ano(self):
        with TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "cadastros.db"
            banco = BancoDadosPN(caminho)

            with patch("reports.datetime") as relogio:
                relogio.now.return_value = datetime(2026, 8, 10, 14, 30)
                primeiro = banco.emitir_relatorio("SP", "PN-100", "", lambda numero, _data: f"<html>{numero}</html>")
                relogio.now.return_value = datetime(2026, 8, 11, 9, 5)
                segundo = banco.emitir_relatorio("SP", "PN-101", "", lambda numero, _data: f"<html>{numero}</html>")

                for relatorio in banco.buscar_relatorios_emitidos():
                    banco.remover_relatorio_emitido(relatorio["id"])

                banco_reaberto = BancoDadosPN(caminho)
                relogio.now.return_value = datetime(2026, 8, 12, 8, 0)
                terceiro = banco_reaberto.emitir_relatorio(
                    "SP", "PN-102", "", lambda numero, _data: f"<html>{numero}</html>"
                )
                relogio.now.return_value = datetime(2027, 1, 2, 8, 0)
                primeiro_novo_ano = banco_reaberto.emitir_relatorio(
                    "SP", "PN-103", "", lambda numero, _data: f"<html>{numero}</html>"
                )

            self.assertEqual(primeiro["numero"], "SP-001-26")
            self.assertEqual(segundo["numero"], "SP-002-26")
            self.assertEqual(terceiro["numero"], "SP-003-26")
            self.assertEqual(primeiro_novo_ano["numero"], "SP-001-27")

    def test_emissao_de_relatorio_arquiva_sha256_verificavel(self):
        with TemporaryDirectory() as diretorio:
            banco = BancoDadosPN(Path(diretorio) / "cadastros.db")
            emissao = banco.emitir_relatorio(
                "SP", "PN-100", "SN-7", lambda numero, _data: f"<html><body>{numero}</body></html>"
            )

            self.assertRegex(emissao["sha256"], r"^[0-9a-f]{64}$")
            self.assertIn(emissao["sha256"], emissao["conteudo_html"])
            self.assertEqual(calcular_sha256_relatorio(emissao["conteudo_html"]), emissao["sha256"])
            arquivado = banco.obter_relatorio_emitido(1)
            self.assertEqual(arquivado["sha256"], emissao["sha256"])

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
