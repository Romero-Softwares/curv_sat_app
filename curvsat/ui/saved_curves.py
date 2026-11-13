"""Tela da biblioteca de curvas de saturação ainda sem vínculo com PN."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from curvsat.content.translations import tr
from curvsat.reporting.reports import (
    CAMPO_UNIDADE_RELATORIO,
    CAMPOS_DADOS_PROCESSO_CURVA,
    criar_dados_processo_curva,
    extrair_faixa_intensidade,
    texto_campo,
)
from curvsat.ui.tooltip import add_tooltip


def _data_curta(valor):
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return "-"


def _rotulo_curva(curva):
    codigo = curva.get("codigo_curva") or "-"
    tipo = curva.get("tipo_lamina") or "-"
    unidade = curva.get("unidade_arco", curva.get("unidade_flecha", "-"))
    medicoes = len(curva.get("tempos") or ())
    return tr(
        "standalone_curve_option",
        code=codigo,
        blade=tipo,
        unit=unidade,
        count=medicoes,
        date=_data_curta(curva.get("_atualizado_em")),
    )


def abrir_curvas_salvas(app):
    """Abre busca e seleção das curvas que existem fora do cadastro de PN."""
    janela = ctk.CTkToplevel(app)
    janela.title(tr("saved_curves_title"))
    janela.geometry("860x520")
    janela.minsize(700, 440)
    janela.grid_columnconfigure(0, weight=1)
    janela.grid_rowconfigure(3, weight=1)

    ctk.CTkLabel(
        janela,
        text=tr("saved_curves_title"),
        font=ctk.CTkFont(size=20, weight="bold"),
    ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")
    ctk.CTkLabel(
        janela,
        text=tr("saved_curves_subtitle"),
        justify="left",
        wraplength=800,
        text_color="#526477",
    ).grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

    busca_frame = ctk.CTkFrame(janela, corner_radius=10)
    busca_frame.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
    busca_frame.grid_columnconfigure(0, weight=1)
    busca_entry = ctk.CTkEntry(busca_frame, placeholder_text=tr("search_curve_placeholder"), height=34)
    busca_entry.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
    buscar_button = ctk.CTkButton(busca_frame, text=tr("search"), width=100)
    buscar_button.grid(row=0, column=1, padx=(0, 12), pady=12)

    lista_frame = ctk.CTkScrollableFrame(janela, corner_radius=10)
    lista_frame.grid(row=3, column=0, padx=24, pady=(0, 12), sticky="nsew")
    lista_frame.grid_columnconfigure(0, weight=1)

    rodape = ctk.CTkFrame(janela, fg_color="transparent")
    rodape.grid(row=4, column=0, padx=24, pady=(0, 20), sticky="ew")
    rodape.grid_columnconfigure(0, weight=1)
    contador = ctk.CTkLabel(rodape, text="")
    contador.grid(row=0, column=0, sticky="w")

    def nova_curva():
        formulario = ctk.CTkToplevel(janela)
        formulario.title(tr("new_curve_data_title"))
        formulario.geometry("720x590")
        formulario.minsize(650, 540)
        formulario.transient(janela)
        formulario.grab_set()
        formulario.grid_columnconfigure(0, weight=1)
        formulario.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            formulario,
            text=tr("new_curve_data_title"),
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(
            formulario,
            text=tr("new_curve_data_subtitle"),
            justify="left",
            wraplength=660,
            text_color="#526477",
        ).grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")

        campos_frame = ctk.CTkFrame(formulario, corner_radius=10)
        campos_frame.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
        campos_frame.grid_columnconfigure((0, 1), weight=1, uniform="processo")
        entradas = {}
        unidades = {}

        def adicionar_campo(rotulo, linha, coluna, colunas=1):
            campo = ctk.CTkFrame(campos_frame, fg_color="transparent")
            campo.grid(
                row=linha,
                column=coluna,
                columnspan=colunas,
                padx=(14, 14) if colunas == 2 else ((14, 7) if coluna == 0 else (7, 14)),
                pady=(10, 4),
                sticky="ew",
            )
            campo.grid_columnconfigure(0, weight=1)
            texto_rotulo = tr("desired_intensity") if rotulo == "Intensidade de peening" else texto_campo(rotulo)
            ctk.CTkLabel(campo, text=texto_rotulo).grid(
                row=0, column=0, columnspan=2, pady=(0, 2), sticky="w"
            )
            entrada = ctk.CTkEntry(campo, height=32)
            entrada.grid(row=1, column=0, padx=(0, 6) if rotulo in CAMPO_UNIDADE_RELATORIO else 0, sticky="ew")
            entradas[rotulo] = entrada
            if rotulo in CAMPO_UNIDADE_RELATORIO:
                unidade = ctk.StringVar(value=CAMPO_UNIDADE_RELATORIO[rotulo][0])
                ctk.CTkOptionMenu(
                    campo,
                    variable=unidade,
                    values=CAMPO_UNIDADE_RELATORIO[rotulo],
                    width=92,
                    height=32,
                ).grid(row=1, column=1, sticky="e")
                unidades[rotulo] = unidade

        campos_formulario = tuple(
            campo for campo in CAMPOS_DADOS_PROCESSO_CURVA if campo != "Intensidade de peening"
        )
        for indice, rotulo in enumerate(campos_formulario):
            adicionar_campo(rotulo, indice // 2, indice % 2)
        adicionar_campo("Intensidade de peening", len(campos_formulario) // 2, 0, 2)

        erro_label = ctk.CTkLabel(formulario, text="", text_color="#c0392b")
        erro_label.grid(row=3, column=0, padx=24, pady=(0, 4), sticky="w")

        botoes = ctk.CTkFrame(formulario, fg_color="transparent")
        botoes.grid(row=4, column=0, padx=24, pady=(0, 20), sticky="ew")
        botoes.grid_columnconfigure(0, weight=1)

        def iniciar():
            intensidade = entradas["Intensidade de peening"].get().strip()
            if extrair_faixa_intensidade(intensidade) is None:
                erro_label.configure(text=tr("desired_intensity_required"))
                entradas["Intensidade de peening"].focus_set()
                return
            dados = {}
            for rotulo, entrada in entradas.items():
                dados[rotulo] = entrada.get().strip()
                if rotulo in unidades:
                    dados[f"Unidade de {rotulo}"] = unidades[rotulo].get()
            app.iniciar_nova_curva_avulsa(criar_dados_processo_curva(dados))
            formulario.grab_release()
            formulario.destroy()
            janela.destroy()

        ctk.CTkButton(
            botoes,
            text=tr("cancel"),
            command=formulario.destroy,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            width=120,
            height=38,
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(
            botoes,
            text=tr("start_curve"),
            command=iniciar,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            width=160,
            height=38,
        ).grid(row=0, column=2)
        formulario.after(100, entradas["Equipamento"].focus_set)

    novo_button = ctk.CTkButton(
        rodape,
        text=tr("new_curve"),
        command=nova_curva,
        fg_color="#27ae60",
        hover_color="#2ecc71",
        height=38,
    )
    novo_button.grid(row=0, column=1, sticky="e")
    add_tooltip(novo_button, tr("tooltip_new_curve"))

    def selecionar(curva):
        if app.carregar_curva_avulsa(curva):
            app.lbl_status.configure(
                text=tr("standalone_curve_selected", code=curva.get("codigo_curva", "-")),
                text_color="#1f6b45",
            )
            janela.destroy()

    def excluir(curva):
        codigo = curva.get("codigo_curva", "-")
        if not messagebox.askyesno(
            tr("delete_curve"),
            tr("delete_curve_confirmation", code=codigo),
            parent=janela,
        ):
            return
        if app.banco_pn.remover_curva_avulsa(curva.get("_id")):
            atualizar_lista()

    def atualizar_lista(_evento=None):
        for widget in lista_frame.winfo_children():
            widget.destroy()
        curvas = app.banco_pn.buscar_curvas_avulsas(busca_entry.get())
        contador.configure(text=tr("standalone_curve_count", count=len(curvas)))
        if not curvas:
            ctk.CTkLabel(lista_frame, text=tr("no_saved_curves"), text_color="#657586").grid(
                row=0, column=0, padx=16, pady=28, sticky="ew"
            )
            return
        for indice, curva in enumerate(curvas):
            linha = ctk.CTkFrame(lista_frame, fg_color=("#edf3f8", "#263442"), corner_radius=8)
            linha.grid(row=indice, column=0, padx=4, pady=4, sticky="ew")
            linha.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                linha,
                text=_rotulo_curva(curva),
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=0, column=0, padx=12, pady=12, sticky="ew")
            selecionar_button = ctk.CTkButton(
                linha,
                text=tr("select_curve"),
                width=105,
                command=lambda item=curva: selecionar(item),
            )
            selecionar_button.grid(row=0, column=1, padx=(6, 4), pady=8)
            add_tooltip(selecionar_button, tr("tooltip_select_curve"))
            ctk.CTkButton(
                linha,
                text=tr("delete_curve"),
                width=86,
                fg_color="#a63d33",
                hover_color="#c0392b",
                command=lambda item=curva: excluir(item),
            ).grid(row=0, column=2, padx=(4, 8), pady=8)

    buscar_button.configure(command=atualizar_lista)
    busca_entry.bind("<Return>", atualizar_lista)
    busca_entry.bind("<KeyRelease>", atualizar_lista)
    atualizar_lista()
    janela.after(150, janela.lift)
