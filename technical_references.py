"""Janela de consulta para análise, granulometria, tipos de mídia e normas."""

from __future__ import annotations

import customtkinter as ctk

from technical_data import (
    ANALISE_ESFERAS,
    AVISO_TECNICO,
    GRANULOMETRIA_ESFERAS,
    NORMAS_REFERENCIA,
    TIPOS_MIDIA,
)


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
    janela.title("Tabelas técnicas — mídia de shot peening")
    janela.geometry("1040x700")
    janela.minsize(880, 560)
    janela.transient(master)

    ctk.CTkLabel(
        janela,
        text="Tabelas técnicas de mídia e normas",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(anchor="w", padx=22, pady=(20, 3))
    ctk.CTkLabel(
        janela,
        text="Referência rápida para análise de esferas, granulometria, tipos de mídia e normas aplicáveis.",
        text_color="#4a5568",
    ).pack(anchor="w", padx=22, pady=(0, 12))

    abas = ctk.CTkTabview(janela)
    abas.pack(fill="both", expand=True, padx=20, pady=(0, 10))
    aba_analise = abas.add("Análise de esferas")
    aba_granulometria = abas.add("Granulometria")
    aba_tipos = abas.add("Tipos de mídia")
    aba_normas = abas.add("Normas")

    _adicionar_cabecalho(
        aba_analise,
        "Roteiro de análise de esferas / mídia metálica",
        "Use o roteiro junto com o plano de inspeção e o certificado do lote; ele não substitui ensaios nem critérios contratuais.",
    )
    _adicionar_tabela(aba_analise, ("Item", "Verificação", "Finalidade"), ANALISE_ESFERAS, (170, 290, 330))

    _adicionar_cabecalho(
        aba_granulometria,
        "Granulometria de esfera conforme designação SAE J444",
        "A abertura nominal identifica a classe. A distribuição completa e seus limites devem ser conferidos na edição vigente da J444 e no certificado do lote.",
    )
    _adicionar_tabela(
        aba_granulometria,
        ("Designação", "Abertura nominal (in)", "Abertura nominal (mm)", "Classe visual"),
        GRANULOMETRIA_ESFERAS,
        (130, 180, 190, 180),
    )

    _adicionar_cabecalho(
        aba_tipos,
        "Tipos de mídia",
        "Escolha conforme desenho, material da peça e processo aprovado.",
    )
    _adicionar_tabela(
        aba_tipos,
        ("Tipo", "Designação", "Referência", "Uso"),
        TIPOS_MIDIA,
        (180, 130, 190, 260),
    )

    _adicionar_cabecalho(
        aba_normas,
        "Normas de referência",
        "Verifique a revisão contratual antes de declarar conformidade.",
    )
    _adicionar_tabela(
        aba_normas,
        ("Norma", "Assunto", "Aplicação no app"),
        NORMAS_REFERENCIA,
        (120, 290, 370),
    )

    ctk.CTkLabel(
        janela,
        text=AVISO_TECNICO,
        justify="left",
        wraplength=960,
        fg_color="#1f344a",
        text_color="#ffffff",
        corner_radius=7,
    ).pack(fill="x", padx=20, pady=(0, 20))

    return janela
