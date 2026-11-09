"""Aba interativa para análise granulométrica de esfera por peneiras."""

from __future__ import annotations

import html
import math
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from curvsat.content.translations import html_language, load_language, sieve_texts
from curvsat.core.paths import user_data_file
from curvsat.core.sieve_analysis import (
    CRITERIOS_SAE_J444,
    analisar_amostra_peneiras,
    limites_midia_em_uso_para_designacao,
    peneiras_para_analise,
)
from curvsat.reporting.reports import abrir_relatorio_html_para_impressao
from curvsat.services.sieve_history import HistoricoAnalisesPeneiras, formatar_data_historico


# Mantido como nome público por compatibilidade com consumidores existentes;
# os valores efetivos agora são derivados do catálogo central de traduções.
_TEXTOS = {idioma: sieve_texts(idioma) for idioma in ("PT", "EN", "ES")}


def _numero(texto: str) -> float:
    valor = texto.strip().replace(",", ".")
    return float(valor) if valor else 0.0


def _texto_limite(linha: dict, textos: dict[str, str], criterio_j444: bool) -> str:
    """Formata critérios numéricos no idioma atual, sem usar texto persistido."""
    if not criterio_j444:
        if linha.get("conforme_midia_em_uso") is None:
            return textos["registro_distribuicao"]
        return (
            textos["limite_usada_retida"]
            if linha.get("tipo_criterio") == "retida_max"
            else textos["limite_usada_passante"]
        )
    if linha.get("tipo_criterio") == "retida_max":
        return textos["limite_retida"].format(limite=linha["limite"])
    return textos["limite_acumulada"].format(
        limite=linha["limite"], passante=linha["limite_passante_max"]
    )


def _ativar_quebra_automatica(rotulo: ctk.CTkLabel, margem: int = 16) -> ctk.CTkLabel:
    """Faz a célula acompanhar sua largura e reservar altura para texto quebrado.

    O ``<Configure>`` do Tk informa pixels físicos, enquanto ``CTkLabel`` recebe
    ``wraplength`` em pixels lógicos e aplica a escala do Windows internamente.
    Converter a medida evita linhas calculadas maiores que a célula em telas com
    escala acima de 100%. A altura é atualizada depois do Tk medir o texto.
    """
    estado = {"ajuste_agendado": False, "altura": None}

    def escala() -> float:
        try:
            return max(1.0, float(rotulo._get_widget_scaling()))
        except (AttributeError, TypeError, ValueError):
            return 1.0

    def ajustar_altura() -> None:
        estado["ajuste_agendado"] = False
        if not rotulo.winfo_exists() or rotulo.winfo_width() <= 1:
            return
        # ``winfo_reqheight`` é físico; CTkLabel.configure(height=...) é lógico.
        altura = max(28, math.ceil(rotulo._label.winfo_reqheight() / escala()) + 4)
        if estado["altura"] != altura:
            estado["altura"] = altura
            rotulo.configure(height=altura)

    def ajustar(_event=None) -> None:
        largura_fisica = rotulo.winfo_width()
        if largura_fisica <= 1:
            return
        largura = max(40, math.floor(largura_fisica / escala()) - margem)
        if rotulo.cget("wraplength") != largura:
            rotulo.configure(wraplength=largura)
        if not estado["ajuste_agendado"]:
            estado["ajuste_agendado"] = True
            rotulo.after_idle(ajustar_altura)

    rotulo.bind("<Configure>", ajustar, add="+")
    rotulo.after_idle(ajustar)
    return rotulo


def gerar_html_impressao_analise_peneiras(
    resultado: dict,
    titulo: str,
    textos: dict[str, str],
    condicao_amostra: str | None = None,
    codigo: str = "",
    idioma: str = "PT",
) -> str:
    """Monta um relatório A4 coerente com o resultado analisado."""
    def esc(valor: object) -> str:
        return html.escape(str(valor), quote=True)

    def linha_tabela(valores: tuple[str, str, str, str]) -> str:
        return "<tr>" + "".join(f"<td>{esc(valor)}</td>" for valor in valores) + "</tr>"

    condicao_amostra = (
        textos["esfera_usada"]
        if resultado.get("tipo_amostra") == "usada"
        else textos["esfera_nova"]
    )
    linhas = []
    for linha in resultado["linhas"]:
        if linha["tipo_criterio"] == "retida_max":
            medida = f"{linha['percentual_retido']:.2f}%"
        else:
            medida = (
                f"{textos['retida_acumulada']} {linha['percentual_retido_acumulado']:.2f}% | "
                f"{textos['passante']} {linha['percentual_passante']:.2f}%"
            )
        if resultado["criterios_normativos_aplicaveis"]:
            criterio = _texto_limite(linha, textos, True)
            situacao = (
                textos["conforme"] if linha["conforme"] is True else
                textos["nao_conforme"] if linha["conforme"] is False else textos["registrado"]
            )
        else:
            criterio = _texto_limite(linha, textos, False)
            situacao = (
                textos["conforme_ams2430"] if linha["conforme_midia_em_uso"] is True else
                textos["nao_conforme_ams2430"] if linha["conforme_midia_em_uso"] is False else textos["registrado"]
            )
        linhas.append(linha_tabela((
            f"#{linha['peneira']} — {linha['abertura_mm']:.3f} mm", criterio, medida, situacao,
        )))
    linhas.append(linha_tabela((
        textos["fundo"],
            textos["fundo_sem_criterio"].format(peneira=resultado["fundo_referencia_peneira"])
        if resultado["criterios_normativos_aplicaveis"] else textos["sem_limite_normativo"],
        f"{resultado['percentual_fundo']:.2f}%",
        f"{textos['fundo_limite']}: {resultado['fundo_referencia_peneira']}",
    )))
    referencia = textos["referencia"] if resultado["criterios_normativos_aplicaveis"] else textos["referencia_usada"]
    identificador = f" | {esc(textos['codigo'])}: {esc(codigo)}" if codigo else ""
    return f"""<!doctype html>
<html lang="{html_language(idioma)}"><head><meta charset="utf-8"><title>{esc(textos['resultado'])} — {esc(resultado['designacao'])}</title>
<style>
@page {{ size: A4; margin: 14mm; }}
body {{ color:#172033; font-family:Arial,Helvetica,sans-serif; font-size:10pt; }}
h1 {{ color:#153e67; font-size:17pt; margin:0 0 4mm; }}
.meta {{ color:#52606d; margin:0 0 5mm; }}
.status {{ background:#e8f3eb; border-left:5px solid #1f6b45; font-size:12pt; font-weight:bold; margin:0 0 5mm; padding:3mm; }}
table {{ border-collapse:collapse; width:100%; }} th,td {{ border:1px solid #cbd5e1; padding:2.5mm; text-align:left; vertical-align:top; }}
th {{ background:#1f344a; color:#fff; }} tr:nth-child(even) {{ background:#f4f8fb; }}
.referencia {{ color:#4a5568; line-height:1.4; margin-top:5mm; }}
.rodape {{ border-top:1px solid #cbd5e1; color:#52606d; font-size:8pt; margin-top:8mm; padding-top:3mm; }}
</style></head><body>
<h1>{esc(textos['resultado'])} — {esc(resultado['designacao'])}</h1>
<p class="meta">{esc(condicao_amostra)}{identificador}<br>{esc(datetime.now().strftime('%d/%m/%Y %H:%M'))}</p>
<div class="status">{esc(titulo)} | {esc(textos['total'])}: {resultado['massa_total_g']:.2f} g</div>
<table><thead><tr><th>{esc(textos['peneira'])}</th><th>{esc(textos['criterio'])}</th><th>{esc(textos['medido'])}</th><th>{esc(textos['situacao'])}</th></tr></thead>
<tbody>{''.join(linhas)}</tbody></table>
<p class="referencia">{esc(referencia)}</p>
<p class="rodape">CurvSat App — {esc(textos['resultado'])}</p>
</body></html>"""


class _CalculadoraPeneiras:
    def __init__(self, parent, textos: dict[str, str], idioma: str):
        self.textos = textos
        self.idioma = idioma
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)
        self.designacao = ctk.StringVar(value="S230")
        self.tipo_amostra = ctk.StringVar(value=textos["esfera_nova"])
        self.entradas: dict[object, ctk.CTkEntry] = {}
        self.janela_resultado: ctk.CTkToplevel | None = None
        self.historico = HistoricoAnalisesPeneiras(language=idioma)

        ctk.CTkLabel(self.frame, text=textos["titulo"], font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=14, pady=(14, 2)
        )
        _ativar_quebra_automatica(
            ctk.CTkLabel(self.frame, text=textos["ajuda"], justify="left", text_color="#4a5568")
        ).pack(anchor="w", fill="x", padx=14, pady=(0, 8))
        seletor = ctk.CTkFrame(self.frame, fg_color="#e5edf3", corner_radius=7)
        seletor.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(seletor, text=textos["designacao"], font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(12, 8), pady=8
        )
        ctk.CTkOptionMenu(
            seletor,
            variable=self.designacao,
            values=list(CRITERIOS_SAE_J444),
            command=lambda _valor: self._montar_entradas(),
            width=120,
        ).pack(side="left", padx=(0, 12), pady=8)
        ctk.CTkLabel(seletor, text=textos["tipo_amostra"], font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(8, 8), pady=8
        )
        ctk.CTkOptionMenu(
            seletor,
            variable=self.tipo_amostra,
            values=[textos["esfera_nova"], textos["esfera_usada"]],
            command=lambda _valor: self._montar_entradas(),
            width=220,
        ).pack(side="left", padx=(0, 12), pady=8)
        ctk.CTkButton(seletor, text=textos["calcular"], command=self._calcular, width=150).pack(
            side="right", padx=10, pady=8
        )
        ctk.CTkButton(seletor, text=textos["historico"], command=self._abrir_historico, width=105).pack(
            side="right", padx=(0, 4), pady=8
        )

        self.entradas_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.entradas_frame.pack(fill="x", padx=14)
        self.mensagem = ctk.CTkLabel(
            self.frame,
            text=textos["instrucoes_entrada"],
            justify="left",
            text_color="#4a5568",
        )
        _ativar_quebra_automatica(self.mensagem)
        self.mensagem.pack(anchor="w", fill="x", padx=18, pady=(4, 14))
        self._montar_entradas()

    def _tipo_amostra_selecionado(self) -> str:
        return "usada" if self.tipo_amostra.get() == self.textos["esfera_usada"] else "nova"

    def _montar_entradas(self):
        for filho in self.entradas_frame.winfo_children():
            filho.destroy()
        self.entradas.clear()
        ctk.CTkLabel(self.entradas_frame, text=self.textos["peneira"], font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=4, pady=(0, 3), sticky="w"
        )
        ctk.CTkLabel(self.entradas_frame, text=self.textos["massa"], font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, padx=4, pady=(0, 3), sticky="w"
        )
        # A tabela ocupa a terceira coluna; sem peso, ela fica presa às
        # larguras mínimas embora a aba tenha área disponível à direita.
        self.entradas_frame.grid_columnconfigure(2, weight=1)
        tabela_especificacao = ctk.CTkFrame(self.entradas_frame, fg_color="#eef4f8", corner_radius=7)
        tabela_especificacao.grid(row=0, column=2, rowspan=20, padx=(28, 4), pady=(4, 4), sticky="nsew")
        # As duas primeiras colunas precisam comportar o cabeçalho e a medida
        # completa (por exemplo, "1.000 mm") sem quebrar cada palavra em uma
        # linha. O espaço excedente continua destinado ao critério normativo.
        tabela_especificacao.grid_columnconfigure(0, weight=0, minsize=145)
        tabela_especificacao.grid_columnconfigure(1, weight=0, minsize=125)
        tabela_especificacao.grid_columnconfigure(2, weight=1, minsize=210)
        tipo_amostra = self._tipo_amostra_selecionado()
        cabecalho_referencia = self.textos["limite_aceitavel"] if tipo_amostra == "nova" else self.textos["referencia_midia_em_uso"]
        limites_midia_em_uso = limites_midia_em_uso_para_designacao(self.designacao.get())
        for coluna, texto in enumerate((self.textos["peneira"], self.textos["abertura"], cabecalho_referencia)):
            celula_cabecalho = ctk.CTkFrame(
                tabela_especificacao,
                fg_color="#1f344a",
                corner_radius=0,
            )
            celula_cabecalho.grid(row=0, column=coluna, sticky="nsew")
            _ativar_quebra_automatica(ctk.CTkLabel(
                celula_cabecalho,
                text=texto,
                text_color="#ffffff",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                justify="left",
            )).pack(fill="both", padx=7, pady=7)
        for indice, criterio in enumerate(
            peneiras_para_analise(self.designacao.get(), tipo_amostra=tipo_amostra), start=1
        ):
            ctk.CTkLabel(
                self.entradas_frame,
                text=f"#{criterio.numero}  —  {criterio.abertura_mm:.3f} mm",
            ).grid(row=indice, column=0, padx=4, pady=2, sticky="w")
            entrada = ctk.CTkEntry(self.entradas_frame, width=150, placeholder_text="0,0")
            entrada.grid(row=indice, column=1, padx=4, pady=2, sticky="w")
            self.entradas[criterio.numero] = entrada
            if tipo_amostra == "nova":
                limite = _texto_limite({
                    "tipo_criterio": criterio.tipo,
                    "limite": criterio.limite,
                    "limite_passante_max": 100.0 - criterio.limite,
                }, self.textos, True)
            else:
                limite = (
                    self.textos["limite_usada_retida"]
                    if criterio.numero == limites_midia_em_uso.peneira_retida_max
                    else self.textos["limite_usada_passante"]
                    if criterio.numero == limites_midia_em_uso.peneira_passante_max
                    else self.textos["registro_distribuicao"]
                )
            for coluna, texto in enumerate((f"#{criterio.numero}", f"{criterio.abertura_mm:.3f} mm", limite)):
                _ativar_quebra_automatica(
                    ctk.CTkLabel(tabela_especificacao, text=texto, anchor="w", justify="left")
                ).grid(row=indice, column=coluna, padx=7, pady=3, sticky="ew")
        linha_fundo = len(self.entradas) + 1
        ctk.CTkLabel(self.entradas_frame, text=self.textos["fundo"]).grid(
            row=linha_fundo, column=0, padx=4, pady=2, sticky="w"
        )
        entrada_fundo = ctk.CTkEntry(self.entradas_frame, width=150, placeholder_text="0,0")
        entrada_fundo.grid(row=linha_fundo, column=1, padx=4, pady=2, sticky="w")
        self.entradas["fundo"] = entrada_fundo
        ultimo_criterio = peneiras_para_analise(self.designacao.get(), tipo_amostra=tipo_amostra)[-1]
        limite_fundo = 100.0 - ultimo_criterio.limite
        ctk.CTkLabel(
            tabela_especificacao,
            text=self.textos["fundo_curto"],
            anchor="w",
        ).grid(row=linha_fundo, column=0, padx=7, pady=3, sticky="w")
        ctk.CTkLabel(
            tabela_especificacao,
            text=f"< #{ultimo_criterio.numero}",
            anchor="w",
        ).grid(row=linha_fundo, column=1, padx=7, pady=3, sticky="w")
        ctk.CTkLabel(
            tabela_especificacao,
            text=(
                self.textos["fundo_criterio"].format(
                    peneira=ultimo_criterio.numero, limite=limite_fundo
                )
                if tipo_amostra == "nova"
                else self.textos["registro_distribuicao"]
            ),
            anchor="w",
        ).grid(row=linha_fundo, column=2, padx=7, pady=3, sticky="w")

    def _mostrar_aviso(self, texto: str, cor: str):
        self.mensagem.configure(text=texto, text_color=cor)

    def _fechar_resultado(self):
        if self.janela_resultado is not None and self.janela_resultado.winfo_exists():
            self.janela_resultado.destroy()
        self.janela_resultado = None

    def _abrir_resultado(
        self,
        resultado: dict,
        titulo: str,
        cor: str,
        massas: dict,
        codigo: str = "",
        salvavel: bool = True,
    ):
        self._fechar_resultado()
        designacao = resultado["designacao"]
        condicao_amostra = self._texto_condicao_resultado(resultado)
        janela = ctk.CTkToplevel(self.frame.winfo_toplevel())
        janela.title(f"{self.textos['resultado']} — {designacao}")
        janela.geometry("1120x610")
        janela.minsize(920, 520)
        janela.transient(self.frame.winfo_toplevel())
        janela.grab_set()
        janela.protocol("WM_DELETE_WINDOW", self._fechar_resultado)
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(1, weight=1)
        self.janela_resultado = janela

        barra = ctk.CTkFrame(janela, fg_color="#e5edf3", corner_radius=0)
        barra.grid(row=0, column=0, sticky="ew")
        barra.grid_columnconfigure(0, weight=1)
        _ativar_quebra_automatica(ctk.CTkLabel(
            barra,
            text=f"{self.textos['resultado']} — {designacao} | {condicao_amostra}",
            font=ctk.CTkFont(size=16, weight="bold"),
            justify="left",
            anchor="w",
        )).grid(row=0, column=0, padx=18, pady=12, sticky="ew")
        ctk.CTkButton(
            barra,
            text=self.textos["imprimir"],
            command=lambda: self._imprimir_resultado(resultado, titulo, codigo),
            width=170,
        ).grid(row=0, column=1, padx=(14, 4), pady=8)
        ctk.CTkButton(
            barra,
            text=self.textos["fechar"],
            command=self._fechar_resultado,
            width=100,
        ).grid(row=0, column=2, padx=(4, 14), pady=8)

        resultado_frame = ctk.CTkFrame(janela, fg_color="#f4f8fb")
        resultado_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self._montar_resultado(resultado_frame, resultado, titulo, cor, massas, codigo, salvavel)
        janela.after_idle(janela.focus_force)

    def _texto_condicao_resultado(self, resultado: dict) -> str:
        """Retorna a condição que foi registrada junto ao cálculo."""
        return (
            self.textos["esfera_usada"]
            if resultado.get("tipo_amostra") == "usada"
            else self.textos["esfera_nova"]
        )

    def _imprimir_resultado(self, resultado: dict, titulo: str, codigo: str) -> None:
        """Abre a análise em formato A4 para a impressão nativa do navegador."""
        identificador = codigo or f"{resultado['designacao']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            conteudo_html = gerar_html_impressao_analise_peneiras(
                resultado, titulo, self.textos, codigo=codigo, idioma=self.idioma,
            )
            arquivo_html = abrir_relatorio_html_para_impressao(
                conteudo_html, user_data_file(f"impressao_analise_peneiras_{identificador}.html")
            )
        except Exception as erro:
            messagebox.showerror(
                self.textos["imprimir"], self.textos["impressao_erro"].format(erro=erro), parent=self.janela_resultado,
            )
            return
        messagebox.showinfo(
            self.textos["imprimir"],
            f"{self.textos['impressao_pronta']}\n\n{arquivo_html}",
            parent=self.janela_resultado,
        )

    def _montar_resultado(self, resultado_frame, resultado: dict, titulo: str, cor: str, massas: dict, codigo: str, salvavel: bool):
        _ativar_quebra_automatica(ctk.CTkLabel(
            resultado_frame,
            text=f"{self.textos['resultado']}: {titulo}  |  {self.textos['total']}: {resultado['massa_total_g']:.2f} g",
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=cor, text_color="#ffffff", corner_radius=7,
            justify="left",
            anchor="w",
        )).pack(fill="x", padx=4, pady=(4, 6))
        if not resultado["massa_conforme"]:
            _ativar_quebra_automatica(
                ctk.CTkLabel(
                    resultado_frame, text=self.textos["massa_aviso"], text_color="#8a2d2d",
                    justify="left", anchor="w",
                )
            ).pack(anchor="w", fill="x", padx=6, pady=(0, 6))
        elif not resultado["criterios_normativos_aplicaveis"]:
            _ativar_quebra_automatica(
                ctk.CTkLabel(
                    resultado_frame, text=self.textos["aviso_usada"], text_color="#1f344a",
                    justify="left", anchor="w",
                )
            ).pack(anchor="w", fill="x", padx=6, pady=(0, 6))

        tabela_resultados = ctk.CTkFrame(resultado_frame, fg_color="transparent")
        tabela_resultados.pack(fill="x", padx=4)
        pesos_colunas = (26, 21, 34, 19)

        def adicionar_linha(valores, fundo, cabecalho=False):
            linha_frame = ctk.CTkFrame(tabela_resultados, fg_color="transparent")
            linha_frame.pack(fill="x", pady=(0, 1))
            for coluna, peso in enumerate(pesos_colunas):
                linha_frame.grid_columnconfigure(coluna, weight=peso, uniform="colunas_resultado")
            for coluna, valor in enumerate(valores):
                _ativar_quebra_automatica(
                    ctk.CTkLabel(
                        linha_frame,
                        text=valor,
                        text_color="#ffffff" if cabecalho else None,
                        fg_color=fundo,
                        corner_radius=0,
                        font=ctk.CTkFont(size=12, weight="bold") if cabecalho else None,
                        justify="left",
                        anchor="w",
                    )
                ).grid(
                    row=0,
                    column=coluna,
                    padx=0,
                    pady=0,
                    sticky="nsew",
                    ipadx=8,
                    ipady=5 if cabecalho else 4,
                )

        colunas = (self.textos["peneira"], self.textos["criterio"], self.textos["medido"], self.textos["situacao"])
        adicionar_linha(colunas, "#1f344a", cabecalho=True)
        for indice, linha in enumerate(resultado["linhas"]):
            if resultado["criterios_normativos_aplicaveis"]:
                fundo = "#e8f3eb" if linha["conforme"] is True else "#fdeaea" if linha["conforme"] is False else "#eef4f8"
            else:
                fundo = "#e8f3eb" if linha["conforme_midia_em_uso"] is True else "#fdeaea" if linha["conforme_midia_em_uso"] is False else "#eef4f8"
            if linha["tipo_criterio"] == "retida_max":
                medida = f"{linha['percentual_retido']:.2f}%"
            else:
                medida = (
                    f"{self.textos['retida_acumulada']} {linha['percentual_retido_acumulado']:.2f}% "
                    f"| {self.textos['passante']} {linha['percentual_passante']:.2f}%"
                )
            valores = (
                f"#{linha['peneira']} — {linha['abertura_mm']:.3f} mm",
                _texto_limite(linha, self.textos, resultado["criterios_normativos_aplicaveis"]),
                medida,
                self.textos["conforme"] if linha["conforme"] is True else self.textos["nao_conforme"] if linha["conforme"] is False else self.textos["conforme_ams2430"] if linha["conforme_midia_em_uso"] is True else self.textos["nao_conforme_ams2430"] if linha["conforme_midia_em_uso"] is False else self.textos["registrado"],
            )
            adicionar_linha(valores, fundo)
        valores = (
            self.textos["fundo"],
            self.textos["fundo_sem_criterio"].format(peneira=resultado["fundo_referencia_peneira"])
            if resultado["criterios_normativos_aplicaveis"] else self.textos["sem_limite_normativo"],
            f"{resultado['percentual_fundo']:.2f}%",
            f"{self.textos['fundo_limite']}: {resultado['fundo_referencia_peneira']}",
        )
        adicionar_linha(valores, "#eef4f8")
        _ativar_quebra_automatica(ctk.CTkLabel(
            resultado_frame,
            text=self.textos["referencia"] if resultado["criterios_normativos_aplicaveis"] else self.textos["referencia_usada"],
            justify="left", anchor="w", text_color="#4a5568",
        )).pack(anchor="w", fill="x", padx=6, pady=(8, 4))

        acoes = ctk.CTkFrame(resultado_frame, fg_color="transparent")
        acoes.pack(fill="x", padx=6, pady=(2, 6))
        if salvavel:
            ctk.CTkLabel(acoes, text=self.textos["codigo"], font=ctk.CTkFont(weight="bold")).pack(
                side="left", padx=(0, 8)
            )
            entrada_codigo = ctk.CTkEntry(acoes, width=185, placeholder_text=self.textos["codigo_opcional"])
            entrada_codigo.pack(side="left", padx=(0, 8))
            if codigo:
                entrada_codigo.insert(0, codigo)
            status = ctk.CTkLabel(acoes, text="", text_color="#1f6b45")
            status.pack(side="right", padx=(10, 0))
            botao_salvar = ctk.CTkButton(acoes, text=self.textos["salvar"], width=140)
            botao_salvar.configure(
                command=lambda: self._salvar_analise(resultado, massas, entrada_codigo, botao_salvar, status)
            )
            botao_salvar.pack(side="right")
        else:
            ctk.CTkLabel(
                acoes, text=self.textos["arquivada"].format(codigo=codigo), text_color="#4a5568"
            ).pack(anchor="w")

    def _salvar_analise(self, resultado: dict, massas: dict, entrada_codigo, botao, status) -> None:
        try:
            registro = self.historico.salvar(resultado, massas, codigo=entrada_codigo.get())
        except ValueError as erro:
            status.configure(text=str(erro), text_color="#9b2c2c")
            return
        entrada_codigo.delete(0, "end")
        entrada_codigo.insert(0, registro["codigo"])
        entrada_codigo.configure(state="disabled")
        botao.configure(state="disabled")
        status.configure(text=self.textos["salvo"].format(codigo=registro["codigo"]), text_color="#1f6b45")

    def _titulo_resultado(self, resultado: dict) -> tuple[str, str]:
        if not resultado["massa_conforme"]:
            return self.textos["amostra_invalida"], "#9b2c2c"
        if not resultado["criterios_normativos_aplicaveis"]:
            if resultado["midia_em_uso_conforme"]:
                return self.textos["conforme_ams2430"], "#1f6b45"
            return self.textos["nao_conforme_ams2430"], "#9b2c2c"
        if resultado["conforme"]:
            return self.textos["conforme"], "#1f6b45"
        return self.textos["nao_conforme"], "#9b2c2c"

    def _abrir_historico(self) -> None:
        janela = ctk.CTkToplevel(self.frame.winfo_toplevel())
        janela.title(self.textos["historico_titulo"])
        janela.geometry("1040x560")
        janela.minsize(900, 480)
        janela.transient(self.frame.winfo_toplevel())
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(janela, text=self.textos["historico_titulo"], font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8)
        )
        filtros = ctk.CTkFrame(janela, fg_color="#e5edf3")
        filtros.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        codigo = ctk.CTkEntry(filtros, width=185, placeholder_text=self.textos["codigo"])
        codigo.pack(side="left", padx=(10, 6), pady=8)
        data = ctk.CTkEntry(filtros, width=160, placeholder_text=self.textos["data"])
        data.pack(side="left", padx=6, pady=8)
        situacao = ctk.StringVar(value=self.textos["todas"])
        opcoes_situacao = {
            self.textos["todas"]: "",
            self.textos["situacao_conforme"]: "conforme",
            self.textos["situacao_nao_conforme"]: "nao_conforme",
            self.textos["situacao_invalida"]: "invalida",
        }
        ctk.CTkOptionMenu(filtros, variable=situacao, values=list(opcoes_situacao), width=170).pack(
            side="left", padx=6, pady=8
        )
        lista = ctk.CTkFrame(janela, fg_color="#f4f8fb")
        lista.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 4))
        ctk.CTkLabel(janela, text=self.textos["registros_exibidos"], text_color="#4a5568").grid(
            row=3, column=0, sticky="w", padx=18, pady=(0, 10)
        )

        def texto_situacao(valor: str) -> str:
            return {
                "conforme": self.textos["situacao_conforme"],
                "nao_conforme": self.textos["situacao_nao_conforme"],
                "invalida": self.textos["situacao_invalida"],
            }.get(valor, valor)

        def abrir_registro(registro: dict) -> None:
            titulo, cor = self._titulo_resultado(registro["resultado"])
            self._abrir_resultado(registro["resultado"], titulo, cor, registro["massas"], registro["codigo"], False)

        def atualizar() -> None:
            for filho in lista.winfo_children():
                filho.destroy()
            try:
                registros = self.historico.buscar(codigo.get(), data.get(), opcoes_situacao[situacao.get()])
            except ValueError as erro:
                ctk.CTkLabel(lista, text=str(erro), text_color="#9b2c2c").pack(anchor="w", padx=12, pady=12)
                return
            if not registros:
                ctk.CTkLabel(lista, text=self.textos["nenhum_registro"], text_color="#4a5568").pack(
                    anchor="w", padx=12, pady=12
                )
                return
            cabecalho = ctk.CTkFrame(lista, fg_color="#1f344a")
            cabecalho.pack(fill="x", padx=5, pady=(5, 1))
            pesos_colunas = (16, 20, 16, 22, 18, 8)
            for indice, texto in enumerate((self.textos["codigo"], self.textos["data"], self.textos["designacao"], self.textos["tipo_amostra"], self.textos["situacao"], "")):
                cabecalho.grid_columnconfigure(indice, weight=pesos_colunas[indice], uniform="historico")
                ctk.CTkLabel(cabecalho, text=texto, text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold")).grid(
                    row=0, column=indice, padx=5, pady=5, sticky="w"
                )
            for registro in registros:
                linha = ctk.CTkFrame(lista, fg_color="#e8f3eb" if registro["situacao"] == "conforme" else "#fdeaea")
                linha.pack(fill="x", padx=5, pady=1)
                valores = (
                    registro["codigo"], formatar_data_historico(registro["data_analise"]), registro["designacao"],
                    registro["tipo_amostra"].capitalize(), texto_situacao(registro["situacao"]),
                )
                for indice, valor in enumerate(valores):
                    linha.grid_columnconfigure(indice, weight=pesos_colunas[indice], uniform="historico")
                    ctk.CTkLabel(linha, text=valor, anchor="w").grid(row=0, column=indice, padx=5, pady=4, sticky="w")
                ctk.CTkButton(linha, text=self.textos["ver"], width=58, height=28, command=lambda item=registro: abrir_registro(item)).grid(
                    row=0, column=5, padx=5, pady=3
                )

        ctk.CTkButton(filtros, text=self.textos["buscar"], width=105, command=atualizar).pack(
            side="right", padx=10, pady=8
        )
        atualizar()

    def _calcular(self):
        try:
            massas = {chave: _numero(entrada.get()) for chave, entrada in self.entradas.items()}
            resultado = analisar_amostra_peneiras(
                self.designacao.get(), massas, massa_fundo=massas["fundo"],
                tipo_amostra=self._tipo_amostra_selecionado(), language=self.idioma,
            )
        except ValueError as erro:
            self._mostrar_aviso(f"{self.textos['erro']}{erro}", "#9b2c2c")
            return

        titulo, cor = self._titulo_resultado(resultado)
        self._mostrar_aviso(self.textos["instrucoes_entrada"], "#4a5568")
        self._abrir_resultado(resultado, titulo, cor, massas)


def adicionar_analise_peneiras(abas) -> None:
    """Adiciona a aba de cálculo de peneiras à janela de tabelas técnicas."""
    idioma = load_language()
    textos = sieve_texts(idioma)
    aba = abas.add(textos["aba"])
    _CalculadoraPeneiras(aba, textos, idioma)
