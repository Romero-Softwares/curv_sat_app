"""Telas informativas reutilizáveis da aplicação.

O módulo concentra a estrutura visual das janelas de informação para que
novas telas (licença, sincronização, versão e outras) não precisem duplicar
configuração de ``CTkToplevel`` e componentes de contato.
"""

from __future__ import annotations

import webbrowser
from collections.abc import Callable
import os
import sys
import threading

import customtkinter as ctk

from i18n import tr
from license_service import (
    AUTOMATIC_DATA_SYNC_INTERVAL_SECONDS,
    LicenseError,
    activate_license,
    get_license_info,
    is_automatic_data_sync_enabled,
    set_automatic_data_sync_enabled,
    sync_active_license,
    sync_active_system_data,
)
from tooltip import add_tooltip


_WINDOW_COLOR = "#1f344a"
_CARD_COLOR = "#eef4f8"
_ACCENT_COLOR = "#1f6fae"


def _resource_path(relative_path: str) -> str:
    """Resolve recursos tanto no código-fonte quanto no executável empacotado."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def _configurar_icone_janela(janela: ctk.CTkToplevel) -> None:
    """Aplica o ícone do aplicativo e o reaplica após o Toplevel ser criado no Windows."""
    caminho_icone = _resource_path("assets/icons/logo.ico")
    if not os.path.exists(caminho_icone):
        return

    try:
        janela.iconbitmap(caminho_icone)
        janela.after(
            300,
            lambda: janela.iconbitmap(caminho_icone) if janela.winfo_exists() else None,
        )
    except Exception:
        pass


def criar_janela_informacao(
    parent: ctk.CTk,
    *,
    titulo: str,
    icone: str,
    subtitulo: str = "",
    geometry: str = "680x510",
) -> tuple[ctk.CTkToplevel, ctk.CTkFrame]:
    """Cria uma janela padronizada e devolve a área para o conteúdo específico."""
    janela = ctk.CTkToplevel(parent)
    janela.title(titulo)
    _configurar_icone_janela(janela)
    janela.geometry(geometry)
    janela.minsize(580, 420)
    janela.transient(parent)
    janela.grab_set()
    janela.grid_columnconfigure(0, weight=1)
    janela.grid_rowconfigure(1, weight=1)

    cabecalho = ctk.CTkFrame(janela, corner_radius=0, fg_color=_WINDOW_COLOR)
    cabecalho.grid(row=0, column=0, sticky="ew")
    cabecalho.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(
        cabecalho,
        text=icone,
        font=ctk.CTkFont(size=23, weight="bold"),
        text_color="#f3f7fb",
    ).grid(row=0, column=0, padx=(24, 12), pady=18)
    ctk.CTkLabel(
        cabecalho,
        text=titulo,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color="#f3f7fb",
    ).grid(row=0, column=1, padx=(0, 22), pady=(15, 0), sticky="sw")
    if subtitulo:
        ctk.CTkLabel(
            cabecalho,
            text=subtitulo,
            font=ctk.CTkFont(size=12),
            text_color="#c5d8e8",
        ).grid(row=1, column=1, padx=(0, 22), pady=(0, 16), sticky="nw")

    conteudo = ctk.CTkScrollableFrame(janela, corner_radius=0, fg_color="transparent")
    conteudo.grid(row=1, column=0, padx=22, pady=18, sticky="nsew")
    conteudo.grid_columnconfigure(1, weight=1)
    return janela, conteudo


def _copiar_texto(janela: ctk.CTkToplevel, texto: str, status: ctk.CTkLabel) -> None:
    janela.clipboard_clear()
    janela.clipboard_append(texto)
    status.configure(text=tr("information_copied"))


def adicionar_item_informacao(
    parent: ctk.CTkFrame,
    *,
    linha: int,
    icone: str,
    rotulo: str,
    valor: str,
    janela: ctk.CTkToplevel,
    status: ctk.CTkLabel,
    acao: Callable[[], None] | None = None,
) -> None:
    """Adiciona um cartão de informação, com cópia e ação opcional."""
    cartao = ctk.CTkFrame(parent, corner_radius=8, fg_color=_CARD_COLOR)
    cartao.grid(row=linha, column=0, columnspan=2, pady=4, sticky="ew")
    cartao.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(cartao, text=icone, font=ctk.CTkFont(size=20), width=38).grid(
        row=0, column=0, rowspan=2, padx=(10, 5), pady=8
    )
    ctk.CTkLabel(
        cartao,
        text=rotulo,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color="#35516d",
    ).grid(row=0, column=1, padx=(0, 8), pady=(7, 0), sticky="w")
    valor_widget = ctk.CTkLabel(
        cartao,
        text=valor,
        font=ctk.CTkFont(size=13),
        text_color="#172033",
        anchor="w",
    )
    valor_widget.grid(row=1, column=1, padx=(0, 8), pady=(0, 7), sticky="ew")
    if acao is not None:
        valor_widget.bind("<Button-1>", lambda _event: acao())
        valor_widget.configure(cursor="hand2")

    copiar_button = ctk.CTkButton(
        cartao,
        text="⧉",
        width=32,
        height=28,
        font=ctk.CTkFont(size=16),
        fg_color="#6b7c8f",
        hover_color="#526477",
        command=lambda: _copiar_texto(janela, valor, status),
    )
    copiar_button.grid(row=0, column=2, rowspan=2, padx=(2, 5), pady=8)
    add_tooltip(copiar_button, tr("tooltip_copy_info", label=rotulo.lower()))
    if acao is not None:
        abrir_button = ctk.CTkButton(
            cartao,
            text="↗",
            width=32,
            height=28,
            font=ctk.CTkFont(size=16),
            fg_color=_ACCENT_COLOR,
            hover_color="#2f80c4",
            command=acao,
        )
        abrir_button.grid(row=0, column=3, rowspan=2, padx=(0, 9), pady=8)
        add_tooltip(abrir_button, tr("tooltip_open_info", label=rotulo.lower()))


def _abrir_link(url: str) -> None:
    webbrowser.open_new_tab(url)


def abrir_informacoes_desenvolvedor(parent: ctk.CTk) -> None:
    """Exibe os créditos e os canais oficiais do desenvolvimento."""
    janela, conteudo = criar_janela_informacao(
        parent,
        titulo=tr("developer_info_title"),
        icone="🛠",
        subtitulo=tr("developer_info_subtitle"),
    )
    ctk.CTkLabel(
        conteudo,
        text=tr("developer_team"),
        font=ctk.CTkFont(size=16, weight="bold"),
    ).grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

    status = ctk.CTkLabel(conteudo, text="", text_color="#2f6f4e", anchor="w")
    itens = (
        ("🤖", tr("developer_agents"), "MTD Softwares e Merotec IA", None),
        ("👤", tr("developer_label"), "Romero Souza", None),
        ("✉", tr("email"), "merotec31@gmail.com", lambda: _abrir_link("mailto:merotec31@gmail.com")),
        ("✉", tr("email"), "merotec32@gmail.com", lambda: _abrir_link("mailto:merotec32@gmail.com")),
        ("☎", "WhatsApp", "(21) 97382-2425", lambda: _abrir_link("https://wa.me/5521973822425")),
        ("🌐", tr("website"), "merotec.online", lambda: _abrir_link("https://merotec.online")),
        ("◉", "GitHub", "github.com/Romero-Softwares", lambda: _abrir_link("https://github.com/Romero-Softwares")),
    )
    for indice, (icone, rotulo, valor, acao) in enumerate(itens, start=1):
        adicionar_item_informacao(
            conteudo,
            linha=indice,
            icone=icone,
            rotulo=rotulo,
            valor=valor,
            janela=janela,
            status=status,
            acao=acao,
        )

    status.grid(row=len(itens) + 1, column=0, columnspan=2, pady=(8, 2), sticky="w")
    fechar_button = ctk.CTkButton(conteudo, text=tr("close"), width=110, command=janela.destroy)
    fechar_button.grid(
        row=len(itens) + 2, column=1, pady=(6, 2), sticky="e"
    )
    add_tooltip(fechar_button, tr("tooltip_close_window"))


def abrir_licenca_sincronizacao(parent: ctk.CTk) -> None:
    """Exibe e controla a ativação e a sincronização da licença do sistema."""
    janela, conteudo = criar_janela_informacao(
        parent,
        titulo=tr("license_sync_title"),
        icone="☁",
        subtitulo=tr("license_activation_title"),
        geometry="680x700",
    )
    conteudo.grid_columnconfigure(0, weight=1)

    license_frame = ctk.CTkFrame(conteudo, corner_radius=8, fg_color="#eaf2f8")
    license_frame.grid(row=0, column=0, padx=2, pady=(0, 10), sticky="ew")
    license_frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        license_frame,
        text=tr("license_activation_title"),
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#1f4967",
    ).grid(row=0, column=0, columnspan=2, padx=14, pady=(14, 4), sticky="w")
    ctk.CTkLabel(
        license_frame,
        text=tr("installation_key"),
        text_color="#35516d",
    ).grid(row=1, column=0, padx=14, pady=(5, 2), sticky="w")

    license_info = get_license_info()
    installation_key_var = ctk.StringVar(value=str(license_info["installation_key"]))
    installation_key_entry = ctk.CTkEntry(license_frame, textvariable=installation_key_var, state="readonly")
    installation_key_entry.grid(row=2, column=0, padx=(14, 6), pady=(0, 5), sticky="ew")

    license_status = ctk.CTkLabel(license_frame, text="", justify="left", anchor="w", wraplength=500)
    sync_status = ctk.CTkLabel(license_frame, text="", justify="left", anchor="w", wraplength=390)

    def copiar_chave_instalacao() -> None:
        janela.clipboard_clear()
        janela.clipboard_append(installation_key_var.get())
        license_status.configure(text=tr("installation_key_copied"), text_color="#2f6f4e")

    copy_key_button = ctk.CTkButton(
        license_frame, text=tr("copy_key"), width=92, command=copiar_chave_instalacao
    )
    copy_key_button.grid(row=2, column=1, padx=(0, 14), pady=(0, 5))
    add_tooltip(copy_key_button, tr("tooltip_copy_installation_key"))
    ctk.CTkLabel(
        license_frame,
        text=tr("activation_key"),
        text_color="#35516d",
    ).grid(row=3, column=0, padx=14, pady=(6, 2), sticky="w")
    activation_code_var = ctk.StringVar()
    activation_entry = ctk.CTkEntry(
        license_frame,
        textvariable=activation_code_var,
        placeholder_text=tr("activation_key_placeholder"),
    )
    activation_entry.grid(row=4, column=0, padx=(14, 6), pady=(0, 5), sticky="ew")
    license_status.grid(row=5, column=0, columnspan=2, padx=14, pady=(4, 2), sticky="ew")
    sync_status.grid(row=6, column=0, padx=(14, 6), pady=(2, 12), sticky="ew")

    def atualizar_status_licenca() -> None:
        current = get_license_info()
        status = current["status"]
        if status == "active":
            validade = current["expires"] or tr("license_no_expiration")
            license_status.configure(
                text=tr("license_active", organization=current["organization"], expires=validade),
                text_color="#2f6f4e",
            )
            copy_key_button.configure(state="disabled")
            activation_entry.configure(state="disabled")
            activate_button.configure(state="disabled")
        else:
            status_messages = {
                "expired": "license_expired",
                "invalid": "license_invalid",
                "revoked": "license_revoked",
                "suspended": "license_suspended",
            }
            message_key = status_messages.get(status, "license_pending")
            license_status.configure(
                text=tr(message_key),
                text_color="#a23b2a" if status in status_messages else "#4a5568",
            )
            copy_key_button.configure(state="normal")
            activation_entry.configure(state="normal")
            activate_button.configure(state="normal")

    def sincronizar_licenca() -> None:
        if get_license_info()["status"] not in {"active", "revoked", "suspended"}:
            sync_status.configure(text="")
            return
        sync_button.configure(state="disabled")
        sync_status.configure(text=tr("license_syncing"), text_color="#4a5568")

        def concluir() -> None:
            result = sync_active_license()

            def atualizar_tela() -> None:
                if not janela.winfo_exists():
                    return
                sync_button.configure(state="normal")
                if result["result"] == "synced":
                    sync_status.configure(text=tr("license_sync_success"), text_color="#2f6f4e")
                    atualizar_status_licenca()
                elif result["result"] == "mismatch":
                    sync_status.configure(text=tr("license_sync_mismatch"), text_color="#a23b2a")
                elif result["result"] == "offline":
                    sync_status.configure(text=tr("license_sync_offline"), text_color="#a2672a")

            try:
                janela.after(0, atualizar_tela)
            except Exception:
                pass

        threading.Thread(target=concluir, daemon=True).start()

    def ativar_licenca() -> None:
        try:
            activate_license(activation_code_var.get())
        except LicenseError as error:
            license_status.configure(text=tr("license_activation_error", message=error), text_color="#a23b2a")
            return
        activation_code_var.set("")
        atualizar_status_licenca()
        sincronizar_licenca()

    activate_button = ctk.CTkButton(
        license_frame, text=tr("activate_license"), width=92, command=ativar_licenca
    )
    activate_button.grid(row=4, column=1, padx=(0, 14), pady=(0, 5))
    add_tooltip(activate_button, tr("tooltip_activate_license"))
    sync_button = ctk.CTkButton(
        license_frame, text=tr("sync_license"), width=92, command=sincronizar_licenca
    )
    sync_button.grid(row=6, column=1, padx=(0, 14), pady=(2, 12))

    data_frame = ctk.CTkFrame(conteudo, corner_radius=8, fg_color="#eaf2f8")
    data_frame.grid(row=1, column=0, padx=2, pady=(0, 10), sticky="ew")
    data_frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        data_frame,
        text=tr("system_data_sync_title"),
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#1f4967",
    ).grid(row=0, column=0, columnspan=2, padx=14, pady=(14, 4), sticky="w")
    ctk.CTkLabel(
        data_frame, text=tr("system_data_sync_description"), justify="left", anchor="w",
        wraplength=500, text_color="#35516d",
    ).grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 8), sticky="ew")
    automatic_sync_var = ctk.BooleanVar(value=is_automatic_data_sync_enabled())
    data_status = ctk.CTkLabel(data_frame, text="", justify="left", anchor="w", wraplength=390)
    data_status.grid(row=3, column=0, padx=(14, 6), pady=(2, 12), sticky="ew")

    def alterar_sincronizacao_automatica() -> None:
        enabled = bool(automatic_sync_var.get())
        set_automatic_data_sync_enabled(enabled)
        if enabled:
            data_status.configure(
                text=tr("automatic_sync_enabled", minutes=AUTOMATIC_DATA_SYNC_INTERVAL_SECONDS // 60),
                text_color="#2f6f4e",
            )
            sincronizar_dados()
        else:
            data_status.configure(text=tr("automatic_sync_disabled"), text_color="#4a5568")
        schedule = getattr(parent, "agendar_sincronizacao_automatica", None)
        if callable(schedule):
            schedule()

    automatic_sync_check = ctk.CTkCheckBox(
        data_frame,
        text=tr("automatic_sync_option", minutes=AUTOMATIC_DATA_SYNC_INTERVAL_SECONDS // 60),
        variable=automatic_sync_var,
        command=alterar_sincronizacao_automatica,
    )
    automatic_sync_check.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 2), sticky="w")

    def sincronizar_dados() -> None:
        data_sync_button.configure(state="disabled")
        data_status.configure(text=tr("system_data_syncing"), text_color="#4a5568")

        def concluir() -> None:
            result = sync_active_system_data()

            def atualizar_tela() -> None:
                if not janela.winfo_exists():
                    return
                data_sync_button.configure(state="normal")
                if result["result"] == "synced":
                    data_status.configure(
                        text=tr("system_data_sync_success", records=result.get("records", 0), reports=result.get("reports", 0)),
                        text_color="#2f6f4e",
                    )
                    atualizar_status_licenca()
                elif result["result"] in {"offline", "blocked", "busy"}:
                    data_status.configure(
                        text=tr("system_data_sync_error", message=result.get("message") or tr("license_sync_offline")),
                        text_color="#a2672a",
                    )
                else:
                    data_status.configure(text=tr("system_data_sync_requires_license"), text_color="#a23b2a")

            try:
                janela.after(0, atualizar_tela)
            except Exception:
                pass

        threading.Thread(target=concluir, daemon=True).start()

    data_sync_button = ctk.CTkButton(
        data_frame, text=tr("sync_system_data"), width=150, command=sincronizar_dados
    )
    data_sync_button.grid(row=3, column=1, padx=(0, 14), pady=(2, 12))

    fechar_button = ctk.CTkButton(conteudo, text=tr("close"), width=110, command=janela.destroy)
    fechar_button.grid(row=2, column=0, padx=2, pady=(2, 0), sticky="e")
    add_tooltip(fechar_button, tr("tooltip_close_window"))
    atualizar_status_licenca()
    sincronizar_licenca()


def abrir_manual_uso(parent: ctk.CTk) -> None:
    """Abre o guia prático de operação sem depender de conexão com a internet."""
    janela, conteudo = criar_janela_informacao(
        parent,
        titulo=tr("user_manual_title"),
        icone="?",
        subtitulo=tr("user_manual_subtitle"),
        geometry="720x680",
    )
    secoes = (
        (tr("manual_step_1_title"), tr("manual_step_1_text")),
        (tr("manual_step_2_title"), tr("manual_step_2_text")),
        (tr("manual_step_3_title"), tr("manual_step_3_text")),
        (tr("manual_step_4_title"), tr("manual_step_4_text")),
        (tr("manual_step_5_title"), tr("manual_step_5_text")),
    )
    for linha, (titulo, texto) in enumerate(secoes):
        cartao = ctk.CTkFrame(conteudo, corner_radius=8, fg_color=_CARD_COLOR)
        cartao.grid(row=linha, column=0, padx=2, pady=4, sticky="ew")
        cartao.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            cartao, text=f"{linha + 1}. {titulo}", font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f4967", anchor="w",
        ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="ew")
        ctk.CTkLabel(
            cartao, text=texto, justify="left", wraplength=630, text_color="#172033", anchor="w",
        ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

    fechar_button = ctk.CTkButton(conteudo, text=tr("close"), width=110, command=janela.destroy)
    fechar_button.grid(row=len(secoes), column=0, padx=2, pady=(10, 2), sticky="e")
    add_tooltip(fechar_button, tr("tooltip_close_window"))


def abrir_informacoes_sistema(parent: ctk.CTk) -> None:
    """Exibe os dados operacionais relevantes e o acesso ao manual integrado."""
    janela, conteudo = criar_janela_informacao(
        parent,
        titulo=tr("about_system_title"),
        icone="ⓘ",
        subtitulo=tr("about_system_subtitle"),
        geometry="680x610",
    )
    status = ctk.CTkLabel(conteudo, text="", text_color="#2f6f4e", anchor="w")
    itens = (
        ("▣", tr("system_product"), tr("system_product_value")),
        ("◷", tr("system_version"), tr("system_version_value")),
        ("✓", tr("system_scope"), tr("system_scope_value")),
        ("☁", tr("system_sync"), tr("system_sync_value")),
        ("▣", tr("system_offline"), tr("system_offline_value")),
        ("§", tr("system_references_info"), tr("system_references_info_value")),
    )
    for linha, (icone, rotulo, valor) in enumerate(itens):
        adicionar_item_informacao(
            conteudo, linha=linha, icone=icone, rotulo=rotulo, valor=valor, janela=janela, status=status
        )

    status.grid(row=len(itens), column=0, columnspan=2, padx=2, pady=(6, 2), sticky="w")
    botoes = ctk.CTkFrame(conteudo, fg_color="transparent")
    botoes.grid(row=len(itens) + 1, column=0, columnspan=2, padx=2, pady=(8, 2), sticky="ew")
    botoes.grid_columnconfigure(0, weight=1)
    manual_button = ctk.CTkButton(
        botoes, text=tr("open_user_manual"), width=190, command=lambda: abrir_manual_uso(janela)
    )
    manual_button.grid(row=0, column=0, sticky="w")
    add_tooltip(manual_button, tr("tooltip_open_user_manual"))
    fechar_button = ctk.CTkButton(botoes, text=tr("close"), width=110, command=janela.destroy)
    fechar_button.grid(row=0, column=1, sticky="e")
    add_tooltip(fechar_button, tr("tooltip_close_window"))


def abrir_tela_em_preparacao(parent: ctk.CTk, titulo: str, icone: str) -> None:
    """Apresenta uma tela padronizada enquanto um módulo futuro é implementado."""
    janela, conteudo = criar_janela_informacao(parent, titulo=titulo, icone=icone, geometry="560x380")
    ctk.CTkLabel(
        conteudo,
        text=tr("info_screen_coming_soon"),
        justify="left",
        wraplength=480,
        font=ctk.CTkFont(size=14),
    ).grid(row=0, column=0, pady=(24, 18), sticky="w")
    fechar_button = ctk.CTkButton(conteudo, text=tr("close"), width=110, command=janela.destroy)
    fechar_button.grid(row=1, column=0, sticky="e")
    add_tooltip(fechar_button, tr("tooltip_close_window"))
