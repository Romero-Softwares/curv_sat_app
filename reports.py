"""Cadastro por PN e geração de relatórios técnicos da curva de saturação."""

from __future__ import annotations

import base64
import html
import json
import os, sys
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app_paths import user_data_file
from i18n import html_language, load_language, tr
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Se for o .exe, o caminho é a pasta onde o .exe está
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_base_path()
    return os.path.join(base_path, relative_path)

CAMPO_UNIDADE_RELATORIO = {
    "Intensidade de peening": ("mm", "in"),
    "Esfera": ("SAE (S)", "mm", "in"),
    "Dureza": ("HRC", "HV", "HB", "HS"),
    "Bico": ("mm", "in", "Nº"),
    "Injetor": ("mm", "in", "Nº"),
    "Distância": ("mm", "cm", "in"),
    "Ângulo": ("°", "rad"),
    "Pressão": ("bar", "psi", "MPa", "kgf/cm²"),
}

CAMPO_TEXTO_RELATORIO = ("Peça / PN", "SN da peça", "Referência", "Reparo", "Equipamento")
CAMPOS_DADOS_EQUIPAMENTO_RELATORIO = ("Equipamento", "Bico", "Injetor", "Distância", "Ângulo", "Pressão")
_CAMPO_CHAVES = {
    "Peça / PN": "piece_pn", "SN da peça": "part_serial_number", "Referência": "reference", "Reparo": "repair", "Equipamento": "equipment",
    "Intensidade de peening": "required_peening_intensity", "Observações": "notes", "Esfera": "shot", "Dureza": "hardness",
    "Bico": "nozzle", "Injetor": "injector", "Distância": "distance", "Ângulo": "angle",
    "Pressão": "pressure", "Tipo de lâmina Almen": "almen_type",
    "Unidade de exposição": "exposure_unit", "Unidade da flecha": "arc_unit",
    "Desvios de lâmina cadastrados": "registered_deviations",
}


def texto_campo(rotulo):
    return tr(_CAMPO_CHAVES[rotulo]) if rotulo in _CAMPO_CHAVES else rotulo


def normas_relatorio():
    return ("SAE J443", "SAE J2597", tr("standard_default"), tr("standard_other"))


def criar_dados_relatorio():
    """Retorna um cadastro de relatório vazio com as unidades padrão."""
    return {
        **{rotulo: "" for rotulo in CAMPO_TEXTO_RELATORIO},
        **{rotulo: "" for rotulo in CAMPO_UNIDADE_RELATORIO},
        **{f"Unidade de {rotulo}": unidades[0] for rotulo, unidades in CAMPO_UNIDADE_RELATORIO.items()},
        "Norma": tr("standard_default"),
        "Observações": "",
    }


def _migrar_campos_legados(dados):
    """Conserva valores cadastrados sob rótulos anteriores."""
    dados = dict(dados)
    if "Referência" not in dados and "Desenho" in dados:
        dados["Referência"] = dados["Desenho"]
    dados.pop("Desenho", None)

    campo_atual = "Intensidade de peening"
    unidade_atual = f"Unidade de {campo_atual}"
    for campo_antigo in ("Faixa de intensidade de peening requerida", "Altura do arco"):
        unidade_antiga = f"Unidade de {campo_antigo}"
        if campo_atual not in dados and campo_antigo in dados:
            dados[campo_atual] = dados[campo_antigo]
        if unidade_atual not in dados and unidade_antiga in dados:
            dados[unidade_atual] = dados[unidade_antiga]
    return dados


class BancoDadosPN:
    """Persistência local dos relatórios, identificados pela combinação PN + SN."""

    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else user_data_file("dados_pn.db")
        self._criar_estrutura()

    @contextmanager
    def _conectar(self):
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        try:
            yield conexao
            conexao.commit()
        finally:
            conexao.close()

    def _criar_estrutura(self):
        with self._conectar() as conexao:
            colunas = conexao.execute("PRAGMA table_info(cadastros_pn)").fetchall()
            if colunas and "serial_number" not in {coluna["name"] for coluna in colunas}:
                conexao.execute(
                    """
                    CREATE TABLE cadastros_pn_novo (
                        pn TEXT NOT NULL COLLATE NOCASE,
                        serial_number TEXT NOT NULL COLLATE NOCASE,
                        dados_json TEXT NOT NULL,
                        atualizado_em TEXT NOT NULL,
                        PRIMARY KEY (pn, serial_number)
                    )
                    """
                )
                conexao.execute(
                    """
                    INSERT INTO cadastros_pn_novo (pn, serial_number, dados_json, atualizado_em)
                    SELECT pn, '', dados_json, atualizado_em FROM cadastros_pn
                    """
                )
                conexao.execute("DROP TABLE cadastros_pn")
                conexao.execute("ALTER TABLE cadastros_pn_novo RENAME TO cadastros_pn")
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS cadastros_pn (
                    pn TEXT NOT NULL COLLATE NOCASE,
                    serial_number TEXT NOT NULL COLLATE NOCASE,
                    dados_json TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    PRIMARY KEY (pn, serial_number)
                )
                """
            )
            conexao.execute(
                "CREATE INDEX IF NOT EXISTS idx_cadastros_pn_atualizado ON cadastros_pn(atualizado_em DESC)"
            )

    @staticmethod
    def _normalizar_pn(valor):
        return str(valor or "").strip()

    @staticmethod
    def _normalizar_sn(valor):
        return str(valor or "").strip()

    def salvar(self, dados):
        dados_normalizados = criar_dados_relatorio()
        dados_normalizados.update(
            {chave: str(valor or "").strip() for chave, valor in _migrar_campos_legados(dados).items()}
        )
        pn = self._normalizar_pn(dados_normalizados["Peça / PN"])
        if not pn:
            raise ValueError(tr("pn_required_save"))
        sn = self._normalizar_sn(dados_normalizados["SN da peça"])
        dados_normalizados["Peça / PN"] = pn
        dados_normalizados["SN da peça"] = sn
        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO cadastros_pn (pn, serial_number, dados_json, atualizado_em)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(pn, serial_number) DO UPDATE SET
                    dados_json = excluded.dados_json,
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    pn,
                    sn,
                    json.dumps(dados_normalizados, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
        return dados_normalizados

    def obter(self, pn, sn=""):
        pn = self._normalizar_pn(pn)
        if not pn:
            return None
        sn = self._normalizar_sn(sn)
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT dados_json FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn)
            ).fetchone()
        if linha is None:
            return None
        try:
            dados_salvos = json.loads(linha["dados_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(dados_salvos, dict):
            return None
        dados = criar_dados_relatorio()
        dados.update({chave: str(valor or "") for chave, valor in _migrar_campos_legados(dados_salvos).items()})
        return dados

    def buscar_registros(self, termo="", limite=40):
        termo = self._normalizar_pn(termo)
        with self._conectar() as conexao:
            if termo:
                termo_escapado = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                linhas = conexao.execute(
                    """
                    SELECT pn, serial_number FROM cadastros_pn
                    WHERE pn LIKE ? ESCAPE '\\'
                    ORDER BY pn COLLATE NOCASE, serial_number COLLATE NOCASE
                    LIMIT ?
                    """,
                    (f"%{termo_escapado}%", limite),
                ).fetchall()
            else:
                linhas = conexao.execute(
                    "SELECT pn, serial_number FROM cadastros_pn ORDER BY pn COLLATE NOCASE, serial_number COLLATE NOCASE LIMIT ?", (limite,)
                ).fetchall()
        return [(linha["pn"], linha["serial_number"]) for linha in linhas]

    def buscar(self, termo="", limite=40):
        """Lista PNs distintos encontrados; a seleção de serial é feita por buscar_registros."""
        pns = []
        for pn, _sn in self.buscar_registros(termo, limite):
            if pn not in pns:
                pns.append(pn)
        return pns

    def remover(self, pn, sn=""):
        pn = self._normalizar_pn(pn)
        if not pn:
            raise ValueError(tr("pn_required_remove"))
        sn = self._normalizar_sn(sn)
        with self._conectar() as conexao:
            cursor = conexao.execute("DELETE FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn))
        return cursor.rowcount > 0


def montar_relatorio_html(informacoes_peca, norma, parametros, resultado, unidade_flecha, unidade_exposicao, grafico_base64):
    """Monta um relatório HTML autocontido, seguro para arquivamento e impressão."""
    def linhas_tabela(campos):
        linhas = []
        for rotulo, valor in campos:
            valor = str(valor).strip()
            linhas.append(
                f"<tr><th>{html.escape(texto_campo(str(rotulo)))}</th><td>{html.escape(valor or tr('no_information'))}</td></tr>"
            )
        return "\n".join(linhas) or f"<tr><td colspan='2'>{tr('no_information')}</td></tr>"

    resultados = [
        (tr("saturation_time"), f"{resultado['t_sat']:.2f} {unidade_exposicao}"),
        (tr("intensity"), f"{resultado['h_sat']:.4f} {unidade_flecha}"),
        (tr("point_2t"), f"{resultado['t_2sat']:.2f} {unidade_exposicao}"),
        (tr("height_2t"), f"{resultado['h_2sat']:.4f} {unidade_flecha}"),
        (tr("fit"), f"{resultado['r2']:.4f}"),
        (tr("measurements"), str(len(resultado['h_data_compensada']))),
    ]
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!doctype html>
<html lang="{html_language()}">
<head>
<meta charset="utf-8">
<title>{tr('report_heading')}</title>
<style>
    @page {{ size: A4; margin: 16mm; }}
    body {{ color: #172033; font: 11pt Arial, sans-serif; margin: 0; }}
    h1 {{ color: #153e67; font-size: 20pt; margin: 0 0 5px; }}
    h2 {{ border-bottom: 2px solid #2f80c4; color: #153e67; font-size: 13pt; margin: 24px 0 8px; padding-bottom: 4px; }}
    .subtitle {{ color: #52606d; margin: 0; }}
    .meta {{ color: #52606d; font-size: 9pt; margin-top: 14px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #eef5fb; font-weight: bold; width: 38%; }}
    .norma {{ background: #f1f8f4; border-left: 4px solid #2e9b62; padding: 10px; white-space: pre-line; }}
    .grafico {{ border: 1px solid #cbd5e1; box-sizing: border-box; margin-top: 8px; max-width: 100%; padding: 8px; width: 100%; }}
    .aviso {{ background: #fff8e5; border-left: 4px solid #e0a020; margin-top: 18px; padding: 10px; }}
</style>
</head>
<body>
<h1>{tr('report_heading')}</h1>
<p class="subtitle">{tr('report_subtitle')}</p>
<p class="meta">{tr('issued', date=data_emissao)}</p>
<h2>{tr('piece_information')}</h2>
<table>{linhas_tabela(informacoes_peca.items())}</table>
<h2>{tr('standard_to_meet')}</h2>
<div class="norma">{html.escape(str(norma).strip() or tr('no_information'))}</div>
<h2>{tr('process_parameters')}</h2>
<table>{linhas_tabela(parametros.items())}</table>
<h2>{tr('curve_results')}</h2>
<table>{linhas_tabela(resultados)}</table>
<h2>{tr('saturation_chart')}</h2>
<img class="grafico" src="data:image/png;base64,{grafico_base64}" alt="{tr('saturation_chart')}">
</body>
</html>"""


def abrir_relatorio(app):
    """Abre o formulário de relatório, com busca e manutenção do cadastro por PN."""
    app.calcular_e_plotar()
    if app._ultimo_resultado is None:
        return

    janela = ctk.CTkToplevel(app)
    janela.title(tr("report_title"))
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    largura_janela = min(max(720, int(largura_tela * 0.88)), 960)
    altura_janela = min(max(580, int(altura_tela * 0.84)), 600)
    janela.geometry(f"{largura_janela}x{altura_janela}")
    janela.minsize(700, 560)
    janela.transient(app)
    janela.grab_set()
    janela.grid_columnconfigure(0, weight=1)
    janela.grid_rowconfigure(2, weight=1)

    path_icon = resource_path("assets/icons/logo.ico")
    if os.path.exists(path_icon):
        janela.iconbitmap(path_icon)

        # Garantia para o Windows (caso o ícone demore a aparecer)
    janela.after(300, lambda: janela.iconbitmap(
            path_icon) if janela.winfo_exists() else None)

    ctk.CTkLabel(
        janela,
        text=tr("report_heading"),
        font=ctk.CTkFont(size=20, weight="bold"),
    ).grid(row=0, column=0, padx=24, pady=(18, 8), sticky="w")

    busca_frame = ctk.CTkFrame(janela, corner_radius=10)
    busca_frame.grid(row=1, column=0, padx=24, pady=(0, 10), sticky="ew")
    busca_frame.grid_columnconfigure(1, weight=1)
    busca_frame.grid_columnconfigure(3, weight=1)
    titulo_busca = ctk.CTkLabel(busca_frame, text=tr("pn_registry"), font=ctk.CTkFont(size=14, weight="bold"))
    titulo_busca.grid(
        row=0, column=0, columnspan=4, padx=14, pady=(10, 3), sticky="w"
    )
    rotulo_busca = ctk.CTkLabel(busca_frame, text=tr("search_pn"))
    rotulo_busca.grid(row=1, column=0, padx=(14, 7), pady=(0, 12), sticky="w")
    busca_entry = ctk.CTkEntry(busca_frame, placeholder_text=tr("search_pn_placeholder"))
    busca_entry.grid(row=1, column=1, padx=(0, 8), pady=(0, 12), sticky="ew")
    resultado_busca = ctk.CTkComboBox(busca_frame, values=[tr("none_found")], state="readonly")
    resultado_busca.grid(row=1, column=3, padx=(0, 14), pady=(0, 12), sticky="ew")
    rotulo_resultados = ctk.CTkLabel(busca_frame, text=tr("results"))
    rotulo_resultados.grid(row=1, column=2, padx=(0, 7), pady=(0, 12), sticky="w")

    formularios_frame = ctk.CTkScrollableFrame(janela, fg_color="transparent", corner_radius=0)
    formularios_frame.grid(row=2, column=0, padx=24, pady=(0, 10), sticky="nsew")
    formularios_frame.grid_columnconfigure((0, 1), weight=1, uniform="painel")
    formularios_frame.grid_rowconfigure(0, weight=1)

    peca_frame = ctk.CTkFrame(formularios_frame, corner_radius=10)
    peca_frame.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
    peca_frame.grid_columnconfigure(0, weight=1)
    peca_frame.grid_rowconfigure(1, weight=1)
    ctk.CTkLabel(peca_frame, text=tr("piece_identification"), font=ctk.CTkFont(size=15, weight="bold")).grid(
        row=0, column=0, padx=14, pady=(12, 6), sticky="w"
    )
    area_peca = ctk.CTkFrame(peca_frame, fg_color="transparent")
    area_peca.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")
    area_peca.grid_columnconfigure((0, 1), weight=1, uniform="campo_peca")

    def criar_campo_texto(container, rotulo, linha, coluna, destino):
        campo = ctk.CTkFrame(container, fg_color="transparent")
        campo.grid(row=linha, column=coluna, padx=(0, 8) if coluna == 0 else (8, 0), pady=(3, 5), sticky="ew")
        campo.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(campo, text=texto_campo(rotulo)).grid(row=0, column=0, pady=(0, 1), sticky="w")
        entrada = ctk.CTkEntry(campo, height=30)
        entrada.grid(row=1, column=0, sticky="ew")
        destino[rotulo] = entrada

    def criar_campo_medida(container, rotulo, linha, coluna, destino):
        campo = ctk.CTkFrame(container, fg_color="transparent")
        campo.grid(row=linha, column=coluna, padx=(0, 8) if coluna == 0 else (8, 0), pady=(3, 5), sticky="ew")
        campo.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(campo, text=texto_campo(rotulo)).grid(row=0, column=0, columnspan=2, pady=(0, 1), sticky="w")
        entrada = ctk.CTkEntry(campo, placeholder_text=tr("value"), height=30)
        entrada.grid(row=1, column=0, padx=(0, 6), sticky="ew")
        unidade_var = ctk.StringVar()
        ctk.CTkOptionMenu(campo, variable=unidade_var, values=CAMPO_UNIDADE_RELATORIO[rotulo], width=92, height=30).grid(
            row=1, column=1, sticky="e"
        )
        destino[rotulo] = (entrada, unidade_var)

    campos_peca = {}
    criar_campo_texto(area_peca, "Peça / PN", 0, 0, campos_peca)
    criar_campo_texto(area_peca, "SN da peça", 0, 1, campos_peca)
    criar_campo_texto(area_peca, "Referência", 1, 0, campos_peca)
    criar_campo_texto(area_peca, "Reparo", 1, 1, campos_peca)

    norma_var = ctk.StringVar()
    campo_norma = ctk.CTkFrame(area_peca, fg_color="transparent")
    campo_norma.grid(row=2, column=1, padx=(8, 0), pady=(3, 5), sticky="ew")
    campo_norma.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(campo_norma, text=tr("standard")).grid(row=0, column=0, pady=(0, 1), sticky="w")
    ctk.CTkComboBox(campo_norma, variable=norma_var, values=normas_relatorio(), height=30).grid(row=1, column=0, sticky="ew")

    campos_medidas_peca = {}
    criar_campo_medida(area_peca, "Intensidade de peening", 2, 0, campos_medidas_peca)
    criar_campo_medida(area_peca, "Esfera", 3, 0, campos_medidas_peca)
    criar_campo_medida(area_peca, "Dureza", 3, 1, campos_medidas_peca)

    parametros_frame = ctk.CTkFrame(formularios_frame, corner_radius=10)
    parametros_frame.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
    parametros_frame.grid_columnconfigure(0, weight=1)
    parametros_frame.grid_rowconfigure(1, weight=1)
    ctk.CTkLabel(parametros_frame, text=tr("process_data"), font=ctk.CTkFont(size=15, weight="bold")).grid(
        row=0, column=0, padx=14, pady=(12, 6), sticky="w"
    )
    area_parametros = ctk.CTkFrame(parametros_frame, fg_color="transparent")
    area_parametros.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")
    area_parametros.grid_columnconfigure((0, 1), weight=1, uniform="campo_processo")
    campos_parametros = {}
    criar_campo_texto(area_parametros, "Equipamento", 0, 0, campos_parametros)

    campos_medidas_parametros = {}
    criar_campo_medida(area_parametros, "Bico", 0, 1, campos_medidas_parametros)
    criar_campo_medida(area_parametros, "Injetor", 1, 0, campos_medidas_parametros)
    criar_campo_medida(area_parametros, "Distância", 1, 1, campos_medidas_parametros)
    criar_campo_medida(area_parametros, "Ângulo", 2, 0, campos_medidas_parametros)
    criar_campo_medida(area_parametros, "Pressão", 2, 1, campos_medidas_parametros)

    campo_observacoes = ctk.CTkFrame(area_parametros, fg_color="transparent")
    campo_observacoes.grid(row=3, column=0, columnspan=2, padx=0, pady=(3, 5), sticky="nsew")
    campo_observacoes.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(campo_observacoes, text=tr("notes")).grid(row=0, column=0, pady=(0, 1), sticky="w")
    observacoes = ctk.CTkTextbox(campo_observacoes, height=68)
    observacoes.grid(row=1, column=0, sticky="nsew")

    def preencher(dados):
        dados_completos = criar_dados_relatorio()
        dados_completos.update(dados or {})
        for rotulo, entrada in {**campos_peca, **campos_parametros}.items():
            entrada.delete(0, "end")
            entrada.insert(0, dados_completos[rotulo])
        for rotulo, (entrada, unidade_var) in {**campos_medidas_peca, **campos_medidas_parametros}.items():
            entrada.delete(0, "end")
            entrada.insert(0, dados_completos[rotulo])
            unidade_var.set(dados_completos[f"Unidade de {rotulo}"])
        norma_var.set(dados_completos["Norma"])
        observacoes.delete("1.0", "end")
        observacoes.insert("1.0", dados_completos["Observações"])

    def coletar_dados():
        dados = criar_dados_relatorio()
        dados.update({rotulo: entrada.get().strip() for rotulo, entrada in campos_peca.items()})
        dados.update({rotulo: entrada.get().strip() for rotulo, entrada in campos_parametros.items()})
        for rotulo, (entrada, unidade_var) in {**campos_medidas_peca, **campos_medidas_parametros}.items():
            dados[rotulo] = entrada.get().strip()
            dados[f"Unidade de {rotulo}"] = unidade_var.get()
        dados["Norma"] = norma_var.get().strip()
        dados["Observações"] = observacoes.get("1.0", "end-1c").strip()
        return dados

    opcoes_busca = {}

    def rotulo_resultado(pn, sn):
        return f"{pn} | SN: {sn or '-'}"

    def atualizar_resultados(termo=None):
        registros = app.banco_pn.buscar_registros(busca_entry.get() if termo is None else termo)
        opcoes_busca.clear()
        for pn, sn in registros:
            opcoes_busca[rotulo_resultado(pn, sn)] = (pn, sn)
        opcoes = list(opcoes_busca) or [tr("none_found")]
        resultado_busca.configure(values=opcoes)
        resultado_busca.set(opcoes[0])

    def carregar_pn(opcao=None):
        chave = opcoes_busca.get(opcao or resultado_busca.get())
        if chave is None:
            return
        pn, sn = chave
        dados = app.banco_pn.obter(pn, sn)
        if not dados:
            return
        preencher(dados)
        busca_entry.delete(0, "end")
        busca_entry.insert(0, dados["Peça / PN"])
        app.dados_relatorio = dados
        app.lbl_status.configure(text=tr("pn_loaded", pn=dados["Peça / PN"]), text_color="#2ecc71")

    def salvar_atualizacao():
        try:
            dados = app.banco_pn.salvar(coletar_dados())
        except (OSError, sqlite3.Error, ValueError) as err:
            app.lbl_status.configure(text=tr("save_pn_error", message=err), text_color="#e74c3c")
            return None
        app.dados_relatorio = dados
        busca_entry.delete(0, "end")
        busca_entry.insert(0, dados["Peça / PN"])
        atualizar_resultados(dados["Peça / PN"])
        resultado_busca.set(rotulo_resultado(dados["Peça / PN"], dados["SN da peça"]))
        app.lbl_status.configure(text=tr("pn_saved", pn=dados["Peça / PN"]), text_color="#2ecc71")
        return dados

    def excluir_pn():
        pn = campos_peca["Peça / PN"].get().strip()
        sn = campos_peca["SN da peça"].get().strip()
        if not pn:
            app.lbl_status.configure(text=tr("pn_required_delete"), text_color="#e74c3c")
            return
        if not messagebox.askyesno(tr("delete_registry"), tr("delete_confirmation", pn=pn), parent=janela):
            return
        try:
            removido = app.banco_pn.remover(pn, sn)
        except (OSError, sqlite3.Error, ValueError) as err:
            app.lbl_status.configure(text=tr("delete_pn_error", message=err), text_color="#e74c3c")
            return
        if removido:
            preencher(criar_dados_relatorio())
            app.dados_relatorio = criar_dados_relatorio()
            busca_entry.delete(0, "end")
            atualizar_resultados()
            app.lbl_status.configure(text=tr("pn_removed", pn=pn), text_color="#2ecc71")
        else:
            app.lbl_status.configure(text=tr("pn_not_found", pn=pn), text_color="#e74c3c")

    def gerar():
        dados = salvar_atualizacao()
        if dados is None:
            return

        def valor_com_unidade(rotulo):
            valor = dados[rotulo]
            return f"{valor} {dados[f'Unidade de {rotulo}']}" if valor else ""

        parametros = {
            "Tipo de lâmina Almen": app._nome_tipo_lamina(),
            "Unidade de exposição": f"{app._nome_tipo_exposicao()} ({app.abreviacao_exposicao})",
            "Unidade da flecha": app.unidade_flecha,
            **{rotulo: valor_com_unidade(rotulo) for rotulo in ("Intensidade de peening", "Esfera", "Dureza")},
            **{
                rotulo: dados[rotulo] if rotulo in CAMPO_TEXTO_RELATORIO else valor_com_unidade(rotulo)
                for rotulo in CAMPOS_DADOS_EQUIPAMENTO_RELATORIO
            },
            "Desvios de lâmina cadastrados": ", ".join(
                f"{nome}: {valor:+.4f} {app.unidade_flecha}" for nome, valor in app.desvios_laminas.items()
            ) or tr("none_applied"),
            "Observações": dados["Observações"],
        }
        informacoes_peca = {rotulo: dados[rotulo] for rotulo in ("Peça / PN", "SN da peça", "Referência", "Reparo")}
        buffer_grafico = BytesIO()
        app.fig.savefig(buffer_grafico, format="png", dpi=180, facecolor=app.fig.get_facecolor(), bbox_inches="tight")
        relatorio = montar_relatorio_html(
            informacoes_peca,
            dados["Norma"],
            parametros,
            app._ultimo_resultado,
            app.unidade_flecha,
            app.abreviacao_exposicao,
            base64.b64encode(buffer_grafico.getvalue()).decode("ascii"),
        )
        caminho = filedialog.asksaveasfilename(
            parent=janela,
            title=tr("save_report"),
            defaultextension=".html",
            filetypes=[(tr("html_report"), "*.html"), (tr("all_files"), "*.*")],
            initialfile=tr("report_file"),
        )
        if not caminho:
            return
        try:
            Path(caminho).write_text(relatorio, encoding="utf-8")
            app.lbl_status.configure(text=tr("report_generated"), text_color="#2ecc71")
            janela.destroy()
            if os.name == "nt":
                os.startfile(str(caminho))
        except OSError as err:
            app.lbl_status.configure(text=tr("save_report_error", message=err), text_color="#e74c3c")

    botao_buscar = ctk.CTkButton(busca_frame, text=tr("search"), width=100, command=atualizar_resultados)
    botao_buscar.grid(
        row=1, column=4, padx=(0, 14), pady=(0, 12)
    )
    resultado_busca.configure(command=carregar_pn)
    busca_entry.bind("<Return>", lambda _evento: atualizar_resultados())
    busca_entry.bind("<KeyRelease>", lambda _evento: atualizar_resultados())

    preencher(app.dados_relatorio)
    botoes_frame = ctk.CTkFrame(janela, fg_color="transparent")
    botoes_frame.grid(row=3, column=0, padx=24, pady=(0, 18), sticky="ew")
    botoes_frame.grid_columnconfigure(0, weight=1)
    botoes_frame.grid_columnconfigure(1, weight=1)
    botoes_frame.grid_columnconfigure(2, weight=2)
    ctk.CTkButton(botoes_frame, text=tr("save_update_pn"), height=40, command=salvar_atualizacao).grid(
        row=0, column=0, padx=(0, 8), sticky="ew"
    )
    ctk.CTkButton(
        botoes_frame, text=tr("delete_pn"), height=40, fg_color="#c0392b", hover_color="#e74c3c", command=excluir_pn
    ).grid(row=0, column=1, padx=8, sticky="ew")
    ctk.CTkButton(
        botoes_frame, text=tr("generate_html"), height=40, fg_color="#1f6fae", hover_color="#2f80c4", command=gerar
    ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

    modo_compacto = None

    def ajustar_layout(_evento=None):
        """Reorganiza os painéis para caber sem campos excessivamente largos."""
        nonlocal modo_compacto
        compacto = janela.winfo_width() < 940
        if compacto != modo_compacto:
            modo_compacto = compacto
            if compacto:
                peca_frame.grid_configure(row=0, column=0, columnspan=2, padx=0, pady=0)
                parametros_frame.grid_configure(row=1, column=0, columnspan=2, padx=0, pady=(10, 0))
                formularios_frame.grid_rowconfigure(1, weight=1)
            else:
                peca_frame.grid_configure(row=0, column=0, columnspan=1, padx=(0, 6), pady=0)
                parametros_frame.grid_configure(row=0, column=1, columnspan=1, padx=(6, 0), pady=0)

        busca_compacta = janela.winfo_width() < 850
        if busca_compacta:
            titulo_busca.grid_configure(columnspan=5)
            rotulo_busca.grid_configure(row=1, column=0, padx=(14, 7), pady=(0, 6))
            busca_entry.grid_configure(row=1, column=1, columnspan=4, padx=(0, 14), pady=(0, 6))
            rotulo_resultados.grid_configure(row=2, column=0, padx=(14, 7), pady=(0, 12))
            resultado_busca.grid_configure(row=2, column=1, columnspan=3, padx=(0, 8), pady=(0, 12))
            botao_buscar.grid_configure(row=2, column=4, padx=(0, 14), pady=(0, 12))
        else:
            rotulo_busca.grid_configure(row=1, column=0, padx=(14, 7), pady=(0, 12))
            busca_entry.grid_configure(row=1, column=1, columnspan=1, padx=(0, 8), pady=(0, 12))
            rotulo_resultados.grid_configure(row=1, column=2, padx=(0, 7), pady=(0, 12))
            resultado_busca.grid_configure(row=1, column=3, columnspan=1, padx=(0, 14), pady=(0, 12))
            botao_buscar.grid_configure(row=1, column=4, padx=(0, 14), pady=(0, 12))

    janela.bind("<Configure>", ajustar_layout)
    janela.after_idle(ajustar_layout)
