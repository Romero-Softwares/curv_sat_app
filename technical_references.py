"""Janela de consulta para análise, granulometria, tipos de mídia e normas."""

from __future__ import annotations

import customtkinter as ctk
import os, sys
from i18n import tr

from technical_data import dados_tecnicos

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

def _adicionar_tabela(parent, colunas, linhas, larguras=None):
    """Cria uma tabela legível dentro de uma área rolável."""
    tabela = ctk.CTkScrollableFrame(parent, fg_color="transparent", label_text="")
    tabela.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    for coluna, titulo in enumerate(colunas):
        # ``wraplength`` não reserva espaço no grid do CustomTkinter. Sem uma
        # largura mínima, colunas com valores curtos (como "SAE J444") podem
        # encolher até ocultar o conteúdo. As tabelas ocupam uma aba inteira,
        # portanto estas larguras continuam legíveis mesmo na janela mínima.
        largura = None if larguras is None else larguras[coluna]
        tabela.grid_columnconfigure(coluna, weight=1, minsize=largura or 80)
        ctk.CTkLabel(
            tabela,
            text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f344a",
            corner_radius=6,
            text_color="#ffffff",
            anchor="w",
        ).grid(row=0, column=coluna, padx=3, pady=(2, 5), sticky="ew")

    for linha_indice, linha in enumerate(linhas, start=1):
        cor = "#edf3f8" if linha_indice % 2 else "#dce8f1"
        for coluna, valor in enumerate(linha):
            largura = None if larguras is None else larguras[coluna]
            ctk.CTkLabel(
                tabela,
                text=valor,
                justify="left",
                anchor="w",
                wraplength=largura,
                fg_color=cor,
                text_color="#17212b",
                corner_radius=5,
            ).grid(row=linha_indice, column=coluna, padx=3, pady=2, sticky="nsew")
    return tabela


def _adicionar_cabecalho(parent, titulo, descricao):
    ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).pack(
        anchor="w", padx=14, pady=(14, 2)
    )
    ctk.CTkLabel(
        parent,
        text=descricao,
        justify="left",
        wraplength=880,
        text_color="#4a5568",
    ).pack(anchor="w", padx=14, pady=(0, 10))


def abrir_referencias_tecnicas(master):
    """Abre uma janela independente de consulta técnica."""
    janela = ctk.CTkToplevel(master)
    janela.title(tr("technical_title"))
    janela.geometry("1040x600")
    janela.minsize(960, 560)
    janela.transient(master)

    path_icon = resource_path("assets/icons/logo.ico")
    if os.path.exists(path_icon):
        janela.iconbitmap(path_icon)

    # Garantia para o Windows (caso o ícone demore a aparecer)
    janela.after(300, lambda: janela.iconbitmap(path_icon) if janela.winfo_exists() else None)

    ctk.CTkLabel(
        janela,
        text=tr("technical_heading"),
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", padx=22, pady=(20, 3))
    ctk.CTkLabel(
        janela,
        text=tr("technical_subtitle"),
        text_color="#4a5568",
    ).pack(anchor="w", padx=22, pady=(0, 12))

    abas = ctk.CTkTabview(janela)
    abas.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    aba_analise = abas.add(tr("tab_analysis"))
    aba_granulometria = abas.add(tr("tab_grain_size"))
    aba_tipos = abas.add(tr("tab_media_types"))
    aba_normas = abas.add(tr("tab_standards"))
    conteudo = dados_tecnicos()

    for aba, chave, larguras in (
        (aba_analise, "analysis", (170, 290, 330)),
        (aba_granulometria, "grain", (130, 180, 190, 180)),
        (aba_tipos, "media", (180, 130, 190, 260)),
        (aba_normas, "standards", (120, 290, 370)),
    ):
        titulo, descricao, colunas, linhas = conteudo[chave]
        _adicionar_cabecalho(aba, titulo, descricao)
        _adicionar_tabela(aba, colunas, linhas, larguras)

    ctk.CTkLabel(
        janela,
        text=conteudo["notice"],
        justify="left",
        wraplength=960,
        fg_color="#1f344a",
        text_color="#ffffff",
        corner_radius=7,
    ).pack(fill="x", padx=20, pady=(0, 20))

    return janela
