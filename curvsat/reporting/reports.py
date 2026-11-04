"""Cadastro por PN e geração de relatórios técnicos da curva de saturação."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import subprocess
import sys
import re
import sqlite3
import threading
import tempfile
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from curvsat.core.paths import user_data_file
from curvsat.content.translations import html_language, load_language, tr
from curvsat.ui.tooltip import add_tooltip
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Se for o .exe, o caminho é a pasta onde o .exe está
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_base_path()
    return os.path.join(base_path, relative_path)


_PDF_CSS = """
body { color: #172033; font-family: Helvetica, sans-serif; font-size: 10.5pt; }
.cabecalho { border: 1.5px solid #2f80c4; border-radius: 5px; margin-bottom: 18px; padding: 12px 16px; }
.logo-empresa { float: left; height: 92px; margin-right: 18px; max-width: 165px; }
h1 { color: #153e67; font-size: 18pt; margin: 0 0 4px; }
h2 { border-bottom: 2px solid #2f80c4; color: #153e67; font-size: 12pt; margin: 20px 0 7px; padding-bottom: 3px; }
.subtitle, .meta, .formula-compensacao { color: #52606d; }
.meta { font-size: 8.5pt; margin-top: 10px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #cbd5e1; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background-color: #eef5fb; font-weight: bold; width: 180pt; }
.norma { background-color: #f1f8f4; border-left: 4px solid #2e9b62; padding: 8px; }
.grafico { border: 1px solid #cbd5e1; margin-top: 8px; max-width: 100%; width: 100%; }
.medicoes-laminas th, .medicoes-laminas td { text-align: center; }
.medicoes-laminas td:nth-child(2) { text-align: left; }
.formula-compensacao { font-size: 9pt; }
.assinaturas { margin-top: 22px; }
.assinatura { display: inline-block; text-align: center; width: 48%; }
.linha-assinatura { border-top: 1px solid #172033; margin: 30px auto 7px; width: 90%; }
.integridade-relatorio { background-color: #f5f8fb; border: 1px solid #cbd5e1; font-size: 8.5pt; margin-top: 22px; padding: 8px 10px; }
.integridade-relatorio code { display: block; font-family: Courier, monospace; font-size: 7pt; }
.rodape-pagina { color: #52606d; font-size: 8pt; margin: 0; text-align: right; }
"""
_DATA_IMAGE_RE = re.compile(
    r'(?P<prefix>\bsrc\s*=\s*)(?P<quote>["\'])data:(?P<mime>[\w.+/-]+);base64,(?P<data>.*?)(?P=quote)',
    re.IGNORECASE | re.DOTALL,
)
_FOOTER_RE = re.compile(
    r'<footer\b[^>]*\bclass\s*=\s*(["\'])[^"\']*\brodape-pagina\b[^"\']*\1[^>]*>.*?</footer>',
    re.IGNORECASE | re.DOTALL,
)
_BODY_RE = re.compile(r"<body\\b[^>]*>(?P<body>.*)</body\\s*>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\\b[^>]*>.*?</style\\s*>", re.IGNORECASE | re.DOTALL)
_SECTION_BREAK_RE = re.compile(
    r"(?=<section\\b[^>]*\\bclass\\s*=\\s*([\"'])[^\"']*\\b(?:resultado-curva|medicoes-laminas)\\b[^\"']*\\1)",
    re.IGNORECASE,
)
_SECTION_BREAK_CSS_RE = re.compile(
    r"\\.(?:resultado-curva|medicoes-laminas)\\s*\\{[^}]*\\}", re.IGNORECASE | re.DOTALL
)
_PAGE_BREAK_PROPERTY_RE = re.compile(
    r"\\b(?:break-before|page-break-before)\\s*:\\s*[^;}]+;?", re.IGNORECASE
)


def nome_arquivo_pdf_relatorio(numero, pn, sn, emitido_em):
    """Monta um nome de PDF legível e válido para o Windows."""
    def componente(valor):
        texto = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", str(valor or "").strip())
        return texto.strip(" .") or "sem-dado"

    data = emitido_em.strftime("%d-%m-%Y")
    return f"{componente(numero)}_{componente(pn)}_{componente(sn)}_{data}.pdf"


class _PaginasHtmlRelatorio(HTMLParser):
    """Separa as seções de página sem simplificar o HTML armazenado."""

    _TAGS_VAZIAS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.paginas = []
        self._pagina = None
        self._profundidade = 0

    def handle_starttag(self, tag, attrs):
        if self._pagina is None and tag == "section" and "pagina-relatorio" in dict(attrs).get("class", "").split():
            self._pagina = []
            self._profundidade = 1
            return
        if self._pagina is not None:
            self._pagina.append(self.get_starttag_text())
            if tag not in self._TAGS_VAZIAS:
                self._profundidade += 1

    def handle_startendtag(self, tag, attrs):
        if self._pagina is not None:
            self._pagina.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self._pagina is None:
            return
        if tag not in self._TAGS_VAZIAS:
            self._profundidade -= 1
        if self._profundidade == 0:
            self.paginas.append("".join(self._pagina))
            self._pagina = None
            return
        self._pagina.append(f"</{tag}>")

    def handle_data(self, data):
        if self._pagina is not None:
            self._pagina.append(data)

    def handle_entityref(self, name):
        if self._pagina is not None:
            self._pagina.append(f"&{name};")

    def handle_charref(self, name):
        if self._pagina is not None:
            self._pagina.append(f"&#{name};")


def _separar_paginas_por_quebra_css(conteudo_html: str) -> list[str]:
    """Converte as quebras de pagina do relatorio em documentos HTML independentes."""
    correspondencia = _BODY_RE.search(conteudo_html)
    if not correspondencia:
        return [conteudo_html]

    corpo = correspondencia.group("body")
    partes = [parte for parte in _SECTION_BREAK_RE.split(corpo) if parte.strip()]
    if len(partes) == 1:
        return [conteudo_html]

    estilos = "".join(_STYLE_RE.findall(conteudo_html))
    estilos = _SECTION_BREAK_CSS_RE.sub(
        lambda item: _PAGE_BREAK_PROPERTY_RE.sub("", item.group(0)), estilos
    )
    return [f"<html><head>{estilos}</head><body>{parte}</body></html>" for parte in partes]


def _preparar_recursos_html(conteudo_html: str, pymupdf):
    """Converte imagens data: em recursos internos aceitos pelo interpretador."""
    arquivo = pymupdf.Archive()
    indice = 0

    def substituir(coincidencia):
        nonlocal indice
        try:
            dados = base64.b64decode(coincidencia.group("data"), validate=True)
            pymupdf.Pixmap(dados)
        except Exception:
            return ""
        indice += 1
        extensao = coincidencia.group("mime").split("/")[-1].lower()
        nome = f"imagem_relatorio_{indice}.{extensao}"
        arquivo.add((dados, nome))
        return f'{coincidencia.group("prefix")}{coincidencia.group("quote")}{nome}{coincidencia.group("quote")}'

    return _DATA_IMAGE_RE.sub(substituir, conteudo_html), arquivo


class _ExtratorHtmlRelatorio(HTMLParser):
    """Extrai os elementos visuais do relatório HTML arquivado para o PDF."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elementos = []
        self._tag_texto = None
        self._texto = []
        self._linhas_tabela = None
        self._linha_tabela = None
        self._celula_tabela = None
        self._div_nivel = 0
        self._tag_div_nivel = None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "div":
            self._div_nivel += 1
        if tag == "table":
            self._linhas_tabela = []
        elif tag == "tr" and self._linhas_tabela is not None:
            self._linha_tabela = []
        elif tag in {"th", "td"} and self._linha_tabela is not None:
            self._celula_tabela = []
        elif tag == "img":
            origem = atributos.get("src", "")
            if origem.startswith("data:image/"):
                self.elementos.append(("imagem", origem, atributos.get("class", "")))
        elif tag == "div" and "assinatura" in atributos.get("class", "").split():
            self._tag_texto = "assinatura"
            self._texto = []
            self._tag_div_nivel = self._div_nivel
        elif tag == "section" and "integridade-relatorio" in atributos.get("class", "").split():
            self._tag_texto = "integridade"
            self._texto = []
            self._tag_div_nivel = None
        elif tag in {"h1", "h2", "p", "code", "footer"} and self._tag_texto is None:
            self._tag_texto = tag
            self._texto = []
        elif tag == "div" and "norma" in atributos.get("class", ""):
            self._tag_texto = "norma"
            self._texto = []
            self._tag_div_nivel = self._div_nivel
        elif tag == "br":
            if self._celula_tabela is not None:
                self._celula_tabela.append("\n")
            elif self._tag_texto:
                self._texto.append("\n")

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self._celula_tabela is not None:
            self._linha_tabela.append("".join(self._celula_tabela).strip())
            self._celula_tabela = None
        elif tag == "tr" and self._linha_tabela is not None:
            self._linhas_tabela.append(self._linha_tabela)
            self._linha_tabela = None
        elif tag == "table" and self._linhas_tabela is not None:
            if self._linhas_tabela:
                self.elementos.append(("tabela", self._linhas_tabela))
            self._linhas_tabela = None
        elif tag == self._tag_texto or (
            tag == "div"
            and self._tag_texto in {"norma", "assinatura", "integridade"}
            and self._tag_div_nivel == self._div_nivel
        ) or (
            tag == "section" and self._tag_texto == "integridade"
        ):
            texto = "".join(self._texto).strip()
            if texto:
                self.elementos.append((self._tag_texto, texto))
            if tag == "footer":
                self.elementos.append(("quebra",))
            self._tag_texto = None
            self._texto = []
            self._tag_div_nivel = None
        if tag == "div":
            self._div_nivel -= 1

    def handle_data(self, data):
        if self._celula_tabela is not None:
            self._celula_tabela.append(data)
        elif self._tag_texto:
            self._texto.append(data)


def _gerar_relatorio_html_em_pdf_reportlab_legacy(conteudo_html: str, destino: str | Path) -> None:
    """Gera um PDF a partir da versão HTML imutável do relatório."""
    raise RuntimeError("A conversão alternativa por ReportLab foi removida para preservar a impressão do navegador.")

    extrator = _ExtratorHtmlRelatorio()
    extrator.feed(conteudo_html)
    extrator.close()
    elementos = list(extrator.elementos)
    while elementos and elementos[-1][0] == "quebra":
        elementos.pop()

    documento = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm, title="Relatório de Curva de Saturação Almen",
    )
    estilos = getSampleStyleSheet()
    estilo_corpo = ParagraphStyle(
        "RelatorioCorpo", parent=estilos["BodyText"], fontName="Helvetica", fontSize=9,
        leading=12, textColor=colors.HexColor("#172033"), spaceAfter=5,
    )
    estilo_titulo = ParagraphStyle(
        "RelatorioTitulo", parent=estilos["Heading1"], fontName="Helvetica-Bold", fontSize=18,
        leading=22, textColor=colors.HexColor("#153e67"), spaceAfter=10,
    )
    estilo_secao = ParagraphStyle(
        "RelatorioSecao", parent=estilos["Heading2"], fontName="Helvetica-Bold", fontSize=12,
        leading=16, textColor=colors.HexColor("#153e67"), spaceBefore=10, spaceAfter=6,
    )
    estilo_rodape = ParagraphStyle(
        "RelatorioRodape", parent=estilo_corpo, fontSize=8, textColor=colors.HexColor("#52606d"), alignment=2,
    )
    estilo_assinatura = ParagraphStyle("RelatorioAssinatura", parent=estilo_corpo, alignment=1, spaceAfter=0)
    estilo_integridade = ParagraphStyle("RelatorioIntegridade", parent=estilo_corpo, fontSize=8, leading=10, spaceAfter=0)
    historia = []
    assinaturas_pendentes = []

    def paragrafo(texto, estilo):
        return Paragraph(html.escape(texto).replace("\n", "<br/>"), estilo)

    def adicionar_assinaturas():
        if not assinaturas_pendentes:
            return
        colunas = len(assinaturas_pendentes)
        dados = [[Spacer(1, 0.35 * cm) for _ in assinaturas_pendentes], [
            paragrafo(assinatura, estilo_assinatura) for assinatura in assinaturas_pendentes
        ]]
        tabela = Table(dados, colWidths=[documento.width / colunas] * colunas, rowHeights=[0.35 * cm, None])
        tabela.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.HexColor("#172033")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        historia.extend((tabela, Spacer(1, 0.25 * cm)))
        assinaturas_pendentes.clear()

    for elemento in elementos:
        tipo = elemento[0]
        if tipo != "assinatura":
            adicionar_assinaturas()
        if tipo == "h1":
            historia.append(paragrafo(elemento[1], estilo_titulo))
        elif tipo == "h2":
            historia.append(paragrafo(elemento[1], estilo_secao))
        elif tipo in {"p", "code"}:
            historia.append(paragrafo(elemento[1], estilo_corpo))
        elif tipo == "norma":
            bloco = Table([[paragrafo(elemento[1], estilo_corpo)]], colWidths=[documento.width])
            bloco.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f8f4")),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#2e9b62")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            historia.extend((bloco, Spacer(1, 0.2 * cm)))
        elif tipo == "integridade":
            bloco = Table([[paragrafo(elemento[1], estilo_integridade)]], colWidths=[documento.width])
            bloco.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f8fb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            historia.extend((bloco, Spacer(1, 0.2 * cm)))
        elif tipo == "assinatura":
            assinaturas_pendentes.append(elemento[1])
        elif tipo == "footer":
            historia.append(Spacer(1, 0.3 * cm))
            historia.append(paragrafo(elemento[1], estilo_rodape))
        elif tipo == "quebra":
            historia.append(PageBreak())
        elif tipo == "tabela":
            linhas = elemento[1]
            colunas = max(len(linha) for linha in linhas)
            dados = [[paragrafo(celula, estilo_corpo) for celula in linha + [""] * (colunas - len(linha))] for linha in linhas]
            larguras = [documento.width / colunas] * colunas
            if colunas == 2:
                larguras = [documento.width * 0.38, documento.width * 0.62]
            tabela = Table(dados, colWidths=larguras, repeatRows=1 if len(dados) > 1 else 0)
            tabela.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef5fb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            historia.extend((tabela, Spacer(1, 0.25 * cm)))
        elif tipo == "imagem":
            try:
                conteudo = base64.b64decode(elemento[1].split(",", 1)[1])
                imagem = Image(BytesIO(conteudo))
                imagem._restrictSize(documento.width, 14 * cm if "grafico" in elemento[2] else 3 * cm)
                historia.extend((imagem, Spacer(1, 0.25 * cm)))
            except (IndexError, ValueError):
                continue
    adicionar_assinaturas()
    documento.build(historia or [paragrafo("Relatório sem conteúdo.", estilo_corpo)])


def abrir_relatorio_html_para_impressao(conteudo_html: str, destino: str | Path) -> Path:
    """Abre o HTML arquivado no navegador para a impressão nativa."""
    arquivo_html = Path(destino).expanduser().with_suffix(".html")
    arquivo_html.parent.mkdir(parents=True, exist_ok=True)
    arquivo_html.write_text(conteudo_html, encoding="utf-8")
    if not webbrowser.open_new_tab(arquivo_html.resolve().as_uri()):
        raise OSError("não foi possível abrir o navegador padrão")
    return arquivo_html


def _localizar_navegador_para_pdf() -> Path | None:
    """Localiza um navegador Chromium capaz de renderizar o HTML em PDF."""
    candidatos = [
        os.environ.get("CURVSAT_BROWSER_PATH"),
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return Path(candidato)
    return None


def converter_relatorio_html_para_pdf(conteudo_html: str, destino: str | Path) -> Path:
    """Converte o HTML arquivado em PDF antes de qualquer impressão direta."""
    navegador = _localizar_navegador_para_pdf()
    if navegador is None:
        raise OSError("não foi encontrado um navegador compatível para gerar o PDF")

    arquivo_pdf = Path(destino).expanduser().with_suffix(".pdf")
    arquivo_html = arquivo_pdf.with_suffix(".html")
    arquivo_pdf.parent.mkdir(parents=True, exist_ok=True)
    arquivo_html.write_text(conteudo_html, encoding="utf-8")
    if arquivo_pdf.exists():
        arquivo_pdf.unlink()

    with tempfile.TemporaryDirectory(prefix="curvsat-pdf-") as perfil_temporario:
        comando = [
            str(navegador),
            "--headless=new",
            "--disable-gpu",
            "--disable-software-rasterizer",
            f"--user-data-dir={perfil_temporario}",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={arquivo_pdf}",
            arquivo_html.resolve().as_uri(),
        ]
        try:
            processo = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired as erro:
            raise OSError("a conversão do relatório em PDF excedeu o tempo limite") from erro

    if processo.returncode != 0 or not arquivo_pdf.is_file() or arquivo_pdf.stat().st_size < 5:
        detalhe = (processo.stderr or processo.stdout or "falha desconhecida").strip()
        raise OSError(f"não foi possível converter o relatório em PDF: {detalhe}")
    if arquivo_pdf.read_bytes()[:5] != b"%PDF-":
        raise OSError("a conversão não produziu um arquivo PDF válido")
    return arquivo_pdf


def enviar_relatorio_html_para_impressora(conteudo_html: str, destino: str | Path) -> Path:
    """Converte o HTML arquivado em PDF e o envia à impressora padrão do Windows."""
    if os.name != "nt":
        raise OSError("a impressão direta está disponível somente no Windows")

    arquivo_pdf = converter_relatorio_html_para_pdf(conteudo_html, destino)
    os.startfile(str(arquivo_pdf), "print")
    return arquivo_pdf


CAMPO_UNIDADE_RELATORIO = {
    "Intensidade de peening": ("mm", "in"),
    "Dureza": ("HRC", "HV", "HB", "HS"),
    "Bico": ("mm", "in", "Nº"),
    "Injetor": ("mm", "in", "Nº"),
    "Distância": ("mm", "cm", "in"),
    "Ângulo": ("°", "rad"),
    "Pressão": ("bar", "psi", "MPa", "kgf/cm²"),
}

CAMPO_TEXTO_RELATORIO = (
    "Router", "Peça / PN", "SN da peça", "Referencia-CMM", "Reparo", "Equipamento", "Esfera",
)
CAMPOS_DADOS_EQUIPAMENTO_RELATORIO = ("Equipamento", "Bico", "Injetor", "Distância", "Ângulo", "Pressão")
_CAMPO_CHAVES = {
    "Peça / PN": "piece_pn", "SN da peça": "part_serial_number", "Referencia-CMM": "reference_cmm", "Reparo": "repair", "Equipamento": "equipment",
    "Intensidade de peening": "required_peening_intensity", "Observações": "notes", "Esfera": "shot", "Dureza": "hardness",
    "Bico": "nozzle", "Injetor": "injector", "Distância": "distance", "Ângulo": "angle",
    "Pressão": "pressure", "Tipo de lâmina Almen": "almen_type",
    "Unidade de exposição": "exposure_unit", "Unidade da altura do arco": "arc_unit",
    "Desvios de lâmina cadastrados": "registered_deviations",
}


RETENCAO_MARCADOR_EXCLUSAO_DIAS = 7


def _timestamp_sincronizacao() -> str:
    """Gera um instante inequívoco para o merge do Supabase.

    O banco remoto recebe ``timestamptz``. Horários sem fuso eram tratados
    como UTC, embora fossem criados no horário local, e uma exclusão podia
    parecer anterior ao relatório que deveria remover.
    """
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _possui_fuso_horario(timestamp: object) -> bool:
    """Informa se uma data ISO guarda o deslocamento UTC explicitamente."""
    if not isinstance(timestamp, str):
        return False
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def _marcador_exclusao_expirou(timestamp: object, agora: datetime | None = None) -> bool:
    """Indica se o marcador de exclusão ultrapassou a retenção configurada.

    Datas legadas sem fuso não expiram aqui: elas são normalizadas e reenviadas
    antes da limpeza, preservando a exclusão durante todo o prazo de retenção.
    """
    if not isinstance(timestamp, str):
        return False
    try:
        momento = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    if momento.tzinfo is None:
        return False
    referencia = agora or datetime.now(timezone.utc)
    return momento <= referencia - timedelta(days=RETENCAO_MARCADOR_EXCLUSAO_DIAS)


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


def extrair_faixa_intensidade(valor):
    """Extrai os limites de uma faixa de intensidade informada no cadastro.

    Aceita vírgula ou ponto como separador decimal e ignora o sufixo do tipo
    de lâmina, por exemplo ``0,014-0.018A``. Valores isolados ou limites
    invertidos não representam uma faixa e, por isso, não recebem destaque.
    """
    numeros = re.findall(r"(?:\d+(?:[.,]\d+)?|[.,]\d+)", str(valor or ""))
    if len(numeros) != 2:
        return None
    try:
        limite_inferior, limite_superior = (float(numero.replace(",", ".")) for numero in numeros)
    except ValueError:
        return None
    if limite_inferior < 0 or limite_superior <= limite_inferior:
        return None
    return limite_inferior, limite_superior


def avaliar_intensidade_requerida(intensidade_calculada, intensidade_requerida, unidade_requerida, unidade_grafico):
    """Compara H(T) à faixa cadastrada, convertida para a unidade do gráfico.

    Uma faixa ausente ou inválida não configura um requisito selecionado e não
    produz avaliação. Os limites retornados já estão na unidade exibida.
    """
    faixa = extrair_faixa_intensidade(intensidade_requerida)
    if faixa is None:
        return None
    try:
        intensidade_calculada = float(intensidade_calculada)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(intensidade_calculada):
        return None

    limite_inferior, limite_superior = (
        _converter_unidade_arco(valor, unidade_requerida, unidade_grafico) for valor in faixa
    )
    return {
        "conforme": limite_inferior <= intensidade_calculada <= limite_superior,
        "limite_inferior": limite_inferior,
        "limite_superior": limite_superior,
    }


def _converter_unidade_arco(valor, unidade_origem, unidade_destino):
    """Converte valores entre as unidades suportadas no cadastro de intensidade."""
    if unidade_origem == unidade_destino:
        return valor
    if unidade_origem == "mm" and unidade_destino == "in":
        return valor / 25.4
    if unidade_origem == "in" and unidade_destino == "mm":
        return valor * 25.4
    raise ValueError("Unidade de intensidade incompatível com o gráfico.")


def destacar_faixa_intensidade(eixo, intensidade, unidade_intensidade, unidade_grafico, legenda=None):
    """Desenha temporariamente os limites solicitados para a imagem do relatório.

    Retorna os artistas criados e os limites originais do eixo para que o
    gráfico interativo permaneça inalterado após a exportação.
    """
    faixa = extrair_faixa_intensidade(intensidade)
    if faixa is None:
        return None

    limite_inferior, limite_superior = (
        _converter_unidade_arco(valor, unidade_intensidade, unidade_grafico) for valor in faixa
    )
    limites_originais = eixo.get_ylim()
    if limite_superior > limites_originais[1]:
        eixo.set_ylim(limites_originais[0], limite_superior * 1.08)

    cor = "#f39c12"
    artistas = [
        eixo.axhspan(limite_inferior, limite_superior, facecolor=cor, alpha=0.16, zorder=0, label=legenda),
        eixo.axhline(limite_inferior, color=cor, linewidth=1.8, linestyle="--", zorder=4),
        eixo.axhline(limite_superior, color=cor, linewidth=1.8, linestyle="--", zorder=4),
    ]
    return artistas, limites_originais


def remover_destaque_faixa_intensidade(eixo, destaque):
    """Remove a marcação temporária usada exclusivamente no relatório."""
    if destaque is None:
        return
    artistas, limites_originais = destaque
    for artista in artistas:
        artista.remove()
    eixo.set_ylim(limites_originais)


def _migrar_campos_legados(dados):
    """Conserva valores cadastrados sob rótulos anteriores."""
    dados = dict(dados)
    dados.pop("Ordem de Serviço", None)
    campo_atual_referencia = "Referencia-CMM"
    for campo_antigo in ("Referência", "Desenho"):
        if campo_atual_referencia not in dados and campo_antigo in dados:
            dados[campo_atual_referencia] = dados[campo_antigo]
        dados.pop(campo_antigo, None)

    campo_atual = "Intensidade de peening"
    unidade_atual = f"Unidade de {campo_atual}"
    for campo_antigo in ("Faixa de intensidade de peening requerida", "Altura do arco"):
        unidade_antiga = f"Unidade de {campo_antigo}"
        if campo_atual not in dados and campo_antigo in dados:
            dados[campo_atual] = dados[campo_antigo]
        if unidade_atual not in dados and unidade_antiga in dados:
            dados[unidade_atual] = dados[unidade_antiga]
    return dados


_SHA_PLACEHOLDER = "__RELATORIO_SHA256__"
_CAMPO_SHA_RE = re.compile(r'(<code\s+data-report-sha="true">).*?(</code>)', re.DOTALL)


def _garantir_campo_sha(conteudo_html):
    """Garante um campo SHA-256 normalizável também para renderizadores legados."""
    if _CAMPO_SHA_RE.search(conteudo_html):
        return conteudo_html
    bloco = (
        '<section class="integridade-relatorio"><strong>SHA-256:</strong> '
        f'<code data-report-sha="true">{_SHA_PLACEHOLDER}</code></section>'
    )
    return conteudo_html.replace("</body>", f"{bloco}</body>", 1) if "</body>" in conteudo_html else conteudo_html + bloco


def calcular_sha256_relatorio(conteudo_html):
    """Calcula a impressão SHA-256 ignorando somente o valor exibido do próprio SHA."""
    conteudo_normalizado = _garantir_campo_sha(conteudo_html)
    conteudo_normalizado = _CAMPO_SHA_RE.sub(
        lambda correspondencia: f"{correspondencia.group(1)}{_SHA_PLACEHOLDER}{correspondencia.group(2)}",
        conteudo_normalizado,
        count=1,
    )
    return hashlib.sha256(conteudo_normalizado.encode("utf-8")).hexdigest()


def inserir_sha256_relatorio(conteudo_html, sha256):
    """Insere a impressão calculada no único campo reservado para a integridade."""
    conteudo_html = _garantir_campo_sha(conteudo_html)
    return _CAMPO_SHA_RE.sub(
        lambda correspondencia: f"{correspondencia.group(1)}{html.escape(sha256)}{correspondencia.group(2)}",
        conteudo_html,
        count=1,
    )


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
                        curva_json TEXT,
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
                colunas = conexao.execute("PRAGMA table_info(cadastros_pn)").fetchall()
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS cadastros_pn (
                    pn TEXT NOT NULL COLLATE NOCASE,
                    serial_number TEXT NOT NULL COLLATE NOCASE,
                    dados_json TEXT NOT NULL,
                    curva_json TEXT,
                    atualizado_em TEXT NOT NULL,
                    PRIMARY KEY (pn, serial_number)
                )
                """
            )
            if colunas and "curva_json" not in {coluna["name"] for coluna in colunas}:
                conexao.execute("ALTER TABLE cadastros_pn ADD COLUMN curva_json TEXT")
            conexao.execute(
                "CREATE INDEX IF NOT EXISTS idx_cadastros_pn_atualizado ON cadastros_pn(atualizado_em DESC)"
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS cadastros_pn_excluidos (
                    pn TEXT NOT NULL COLLATE NOCASE,
                    serial_number TEXT NOT NULL COLLATE NOCASE,
                    excluido_em TEXT NOT NULL,
                    PRIMARY KEY (pn, serial_number)
                )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS relatorios_emitidos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL UNIQUE,
                    prefixo TEXT NOT NULL,
                    ano INTEGER NOT NULL,
                    sequencia INTEGER NOT NULL,
                    emitido_em TEXT NOT NULL,
                    pn TEXT NOT NULL DEFAULT '',
                    serial_number TEXT NOT NULL DEFAULT '',
                    conteudo_html TEXT NOT NULL,
                    sha256 TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL,
                    UNIQUE(prefixo, ano, sequencia)
                )
                """
            )
            colunas_relatorios = conexao.execute("PRAGMA table_info(relatorios_emitidos)").fetchall()
            if "sha256" not in {coluna["name"] for coluna in colunas_relatorios}:
                conexao.execute("ALTER TABLE relatorios_emitidos ADD COLUMN sha256 TEXT NOT NULL DEFAULT ''")
            conexao.execute(
                "CREATE INDEX IF NOT EXISTS idx_relatorios_emitidos_busca "
                "ON relatorios_emitidos(ano DESC, sequencia DESC, pn, serial_number)"
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS relatorios_sequencias (
                    prefixo TEXT NOT NULL,
                    ano INTEGER NOT NULL,
                    ultima_sequencia INTEGER NOT NULL,
                    PRIMARY KEY (prefixo, ano)
                )
                """
            )
            # Migra bancos existentes sem depender dos relatórios que venham a
            # ser excluídos depois desta atualização.
            conexao.execute(
                """
                INSERT INTO relatorios_sequencias (prefixo, ano, ultima_sequencia)
                SELECT prefixo, ano, MAX(sequencia)
                FROM relatorios_emitidos
                GROUP BY prefixo, ano
                ON CONFLICT(prefixo, ano) DO UPDATE SET
                    ultima_sequencia = MAX(
                        relatorios_sequencias.ultima_sequencia,
                        excluded.ultima_sequencia
                    )
                """
            )
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS relatorios_emitidos_excluidos (
                    sha256 TEXT PRIMARY KEY,
                    excluido_em TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _normalizar_pn(valor):
        return str(valor or "").strip()

    @staticmethod
    def _normalizar_sn(valor):
        return str(valor or "").strip()

    @staticmethod
    def _registrar_sequencia_relatorio(conexao, prefixo, ano, sequencia):
        """Mantém a maior sequência anual, inclusive para relatórios excluídos."""
        conexao.execute(
            """
            INSERT INTO relatorios_sequencias (prefixo, ano, ultima_sequencia)
            VALUES (?, ?, ?)
            ON CONFLICT(prefixo, ano) DO UPDATE SET
                ultima_sequencia = MAX(
                    relatorios_sequencias.ultima_sequencia,
                    excluded.ultima_sequencia
                )
            """,
            (prefixo, ano, sequencia),
        )

    def salvar(self, dados, curva=None):
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
                INSERT INTO cadastros_pn (pn, serial_number, dados_json, curva_json, atualizado_em)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(pn, serial_number) DO UPDATE SET
                    dados_json = excluded.dados_json,
                    curva_json = COALESCE(excluded.curva_json, cadastros_pn.curva_json),
                    atualizado_em = excluded.atualizado_em
                """,
                (
                    pn,
                    sn,
                    json.dumps(dados_normalizados, ensure_ascii=False),
                    json.dumps(curva, ensure_ascii=False) if curva is not None else None,
                    _timestamp_sincronizacao(),
                ),
            )
            conexao.execute(
                "DELETE FROM cadastros_pn_excluidos WHERE pn = ? AND serial_number = ?", (pn, sn)
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

    def obter_curva(self, pn, sn=""):
        """Retorna a curva vinculada ao cadastro exato de PN e número de série."""
        pn = self._normalizar_pn(pn)
        if not pn:
            return None
        sn = self._normalizar_sn(sn)
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT curva_json FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn)
            ).fetchone()
        if linha is None or not linha["curva_json"]:
            return None
        try:
            curva = json.loads(linha["curva_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        return curva if isinstance(curva, dict) else None

    def atualizar_codigo_curva(self, pn, sn, codigo_curva):
        """Grava o identificador gerado na própria curva já arquivada."""
        pn = self._normalizar_pn(pn)
        sn = self._normalizar_sn(sn)
        codigo_curva = str(codigo_curva or "").strip().upper()
        if not pn:
            raise ValueError(tr("pn_required_save"))
        if not re.fullmatch(r"[NAC]\d{4}", codigo_curva):
            raise ValueError("Identificador de curva inválido.")

        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT curva_json FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn)
            ).fetchone()
            if linha is None or not linha["curva_json"]:
                return False
            try:
                curva = json.loads(linha["curva_json"])
            except (TypeError, json.JSONDecodeError):
                return False
            if not isinstance(curva, dict):
                return False
            if curva.get("codigo_curva") == codigo_curva:
                return True
            curva["codigo_curva"] = codigo_curva
            conexao.execute(
                "UPDATE cadastros_pn SET curva_json = ?, atualizado_em = ? WHERE pn = ? AND serial_number = ?",
                (json.dumps(curva, ensure_ascii=False), _timestamp_sincronizacao(), pn, sn),
            )
        return True

    def obter_ultima_curva(self, incluir_origem=False):
        """Retorna a curva associada ao PN salvo mais recentemente, se houver."""
        with self._conectar() as conexao:
            linha = conexao.execute(
                """
                SELECT pn, serial_number, curva_json FROM cadastros_pn
                WHERE curva_json IS NOT NULL AND curva_json <> ''
                ORDER BY atualizado_em DESC, rowid DESC
                LIMIT 1
                """
            ).fetchone()
        if linha is None:
            return None
        try:
            curva = json.loads(linha["curva_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(curva, dict):
            return None
        if incluir_origem:
            curva["_cadastro_pn"] = linha["pn"]
            curva["_cadastro_sn"] = linha["serial_number"]
        return curva

    def buscar_registros(self, termo="", limite=40):
        termo = self._normalizar_pn(termo)
        with self._conectar() as conexao:
            if termo:
                termo_escapado = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                linhas = conexao.execute(
                    """
                    SELECT pn, serial_number FROM cadastros_pn
                    WHERE pn LIKE ? ESCAPE '\\'
                       OR serial_number LIKE ? ESCAPE '\\'
                       OR json_extract(dados_json, '$.Router') LIKE ? ESCAPE '\\'
                    ORDER BY pn COLLATE NOCASE, serial_number COLLATE NOCASE
                    LIMIT ?
                    """,
                    (f"%{termo_escapado}%", f"%{termo_escapado}%", f"%{termo_escapado}%", limite),
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
            if cursor.rowcount:
                conexao.execute(
                    """
                    INSERT INTO cadastros_pn_excluidos (pn, serial_number, excluido_em)
                    VALUES (?, ?, ?)
                    ON CONFLICT(pn, serial_number) DO UPDATE SET excluido_em = excluded.excluido_em
                    """,
                    (pn, sn, _timestamp_sincronizacao()),
                )
        return cursor.rowcount > 0

    def exportar_para_sincronizacao(self):
        """Serializa apenas dados do sistema, sem copiar o arquivo SQLite entre PCs."""
        with self._conectar() as conexao:
            # Reemite uma vez os marcadores criados por versões antigas, que
            # gravavam data sem fuso. Isso permite que exclusões já pendentes
            # vençam o registro remoto que recebeu um ``updated_at`` UTC.
            for tabela, chave in (
                ("cadastros_pn_excluidos", "pn, serial_number"),
                ("relatorios_emitidos_excluidos", "sha256"),
            ):
                linhas_legadas = conexao.execute(
                    f"SELECT {chave}, excluido_em FROM {tabela}"
                ).fetchall()
                for linha in linhas_legadas:
                    if _possui_fuso_horario(linha["excluido_em"]):
                        continue
                    if tabela == "cadastros_pn_excluidos":
                        conexao.execute(
                            "UPDATE cadastros_pn_excluidos SET excluido_em = ? WHERE pn = ? AND serial_number = ?",
                            (_timestamp_sincronizacao(), linha["pn"], linha["serial_number"]),
                        )
                    else:
                        conexao.execute(
                            "UPDATE relatorios_emitidos_excluidos SET excluido_em = ? WHERE sha256 = ?",
                            (_timestamp_sincronizacao(), linha["sha256"]),
                        )
            agora = datetime.now(timezone.utc)
            for tabela in ("cadastros_pn_excluidos", "relatorios_emitidos_excluidos"):
                linhas_expiradas = conexao.execute(
                    f"SELECT rowid, excluido_em FROM {tabela}"
                ).fetchall()
                for linha in linhas_expiradas:
                    if _marcador_exclusao_expirou(linha["excluido_em"], agora):
                        conexao.execute(f"DELETE FROM {tabela} WHERE rowid = ?", (linha["rowid"],))
            cadastros = conexao.execute(
                "SELECT pn, serial_number, dados_json, curva_json, atualizado_em FROM cadastros_pn"
            ).fetchall()
            excluidos = conexao.execute(
                "SELECT pn, serial_number, excluido_em FROM cadastros_pn_excluidos"
            ).fetchall()
            relatorios = conexao.execute(
                """
                SELECT numero, prefixo, ano, sequencia, emitido_em, pn, serial_number,
                       conteudo_html, sha256, criado_em
                FROM relatorios_emitidos
                """
            ).fetchall()
            relatorios_excluidos = conexao.execute(
                "SELECT sha256, excluido_em FROM relatorios_emitidos_excluidos"
            ).fetchall()
        records = []
        for cadastro in cadastros:
            try:
                dados = json.loads(cadastro["dados_json"])
                curva = json.loads(cadastro["curva_json"]) if cadastro["curva_json"] else None
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(dados, dict) and (curva is None or isinstance(curva, dict)):
                records.append({
                    "pn": cadastro["pn"], "serial_number": cadastro["serial_number"],
                    "data": dados, "curve": curva, "updated_at": cadastro["atualizado_em"], "deleted": False,
                })
        records.extend({
            "pn": row["pn"], "serial_number": row["serial_number"], "data": None,
            "curve": None, "updated_at": row["excluido_em"], "deleted": True,
        } for row in excluidos)
        reports = [
            {**dict(row), "deleted": False, "updated_at": row["criado_em"]}
            for row in relatorios
        ]
        reports.extend(
            {"sha256": row["sha256"], "deleted": True, "updated_at": row["excluido_em"]}
            for row in relatorios_excluidos
        )
        return {"records": records, "reports": reports}

    def importar_da_sincronizacao(self, records, reports):
        """Mescla o estado remoto, preservando localmente a altera\u00e7\u00e3o mais recente."""
        if not isinstance(records, list) or not isinstance(reports, list):
            raise ValueError("Os dados remotos do sistema s\u00e3o inv\u00e1lidos.")
        imported_records = imported_reports = 0
        with self._conectar() as conexao:
            for record in records:
                if not isinstance(record, dict):
                    continue
                pn = self._normalizar_pn(record.get("pn"))
                sn = self._normalizar_sn(record.get("serial_number"))
                updated_at = record.get("updated_at")
                deleted = record.get("deleted", False)
                if not pn or not isinstance(updated_at, str) or not isinstance(deleted, bool):
                    continue
                if deleted and _marcador_exclusao_expirou(updated_at):
                    continue
                local = conexao.execute(
                    "SELECT dados_json, curva_json, atualizado_em FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn)
                ).fetchone()
                tombstone = conexao.execute(
                    "SELECT excluido_em FROM cadastros_pn_excluidos WHERE pn = ? AND serial_number = ?", (pn, sn)
                ).fetchone()
                newest_local = max(
                    local["atualizado_em"] if local else "",
                    tombstone["excluido_em"] if tombstone else "",
                )
                if newest_local > updated_at:
                    continue
                if deleted:
                    changed = (
                        local is not None
                        or tombstone is None
                        or tombstone["excluido_em"] != updated_at
                    )
                    conexao.execute("DELETE FROM cadastros_pn WHERE pn = ? AND serial_number = ?", (pn, sn))
                    conexao.execute(
                        """
                        INSERT INTO cadastros_pn_excluidos (pn, serial_number, excluido_em)
                        VALUES (?, ?, ?)
                        ON CONFLICT(pn, serial_number) DO UPDATE SET excluido_em = excluded.excluido_em
                        """, (pn, sn, updated_at)
                    )
                    if changed:
                        imported_records += 1
                    continue
                dados, curva = record.get("data"), record.get("curve")
                if not isinstance(dados, dict) or (curva is not None and not isinstance(curva, dict)):
                    continue
                serialized_data = json.dumps(dados, ensure_ascii=False)
                serialized_curve = json.dumps(curva, ensure_ascii=False) if curva is not None else None
                try:
                    local_data = json.loads(local["dados_json"]) if local else None
                    local_curve = json.loads(local["curva_json"]) if local and local["curva_json"] else None
                except (TypeError, json.JSONDecodeError):
                    local_data = local_curve = None
                changed = (
                    local is None
                    or tombstone is not None
                    or local["atualizado_em"] != updated_at
                    or local_data != dados
                    or local_curve != curva
                )
                conexao.execute(
                    """
                    INSERT INTO cadastros_pn (pn, serial_number, dados_json, curva_json, atualizado_em)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(pn, serial_number) DO UPDATE SET
                        dados_json = excluded.dados_json, curva_json = excluded.curva_json,
                        atualizado_em = excluded.atualizado_em
                    """, (pn, sn, serialized_data, serialized_curve, updated_at)
                )
                conexao.execute("DELETE FROM cadastros_pn_excluidos WHERE pn = ? AND serial_number = ?", (pn, sn))
                if changed:
                    imported_records += 1

            for report in reports:
                if not isinstance(report, dict):
                    continue
                sha256 = report.get("sha256")
                deleted = report.get("deleted", False)
                updated_at = report.get("updated_at", report.get("criado_em"))
                if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
                    continue
                if not isinstance(deleted, bool) or not isinstance(updated_at, str):
                    continue
                if deleted and _marcador_exclusao_expirou(updated_at):
                    continue
                local = conexao.execute(
                    "SELECT id, criado_em FROM relatorios_emitidos WHERE sha256 = ?", (sha256,)
                ).fetchone()
                tombstone = conexao.execute(
                    "SELECT excluido_em FROM relatorios_emitidos_excluidos WHERE sha256 = ?", (sha256,)
                ).fetchone()
                # A exclusão é definitiva para este identificador. Um relatório
                # ativo que ainda exista em uma instalação/servidor desatualizado
                # não pode consumir a marca local de exclusão e reaparecer aqui.
                # Um novo relatório recebe outro SHA-256, portanto não há perda
                # de uma recriação legítima.
                if tombstone is not None and not deleted:
                    continue
                newest_local = max(
                    local["criado_em"] if local else "",
                    tombstone["excluido_em"] if tombstone else "",
                )
                if newest_local > updated_at:
                    continue
                if deleted:
                    changed = (
                        local is not None
                        or tombstone is None
                        or tombstone["excluido_em"] != updated_at
                    )
                    conexao.execute("DELETE FROM relatorios_emitidos WHERE sha256 = ?", (sha256,))
                    conexao.execute(
                        """
                        INSERT INTO relatorios_emitidos_excluidos (sha256, excluido_em)
                        VALUES (?, ?)
                        ON CONFLICT(sha256) DO UPDATE SET excluido_em = excluded.excluido_em
                        """,
                        (sha256, updated_at),
                    )
                    if changed:
                        imported_reports += 1
                    continue
                if local:
                    continue
                if not all(isinstance(report.get(key), str) for key in ("numero", "prefixo", "emitido_em", "conteudo_html", "criado_em")):
                    continue
                if not isinstance(report.get("ano"), int) or not isinstance(report.get("sequencia"), int):
                    continue
                numero, prefixo = report["numero"], report["prefixo"]
                self._registrar_sequencia_relatorio(
                    conexao, prefixo, report["ano"], report["sequencia"]
                )
                collision = conexao.execute(
                    "SELECT id FROM relatorios_emitidos WHERE numero = ? OR (prefixo = ? AND ano = ? AND sequencia = ?)",
                    (numero, prefixo, report["ano"], report["sequencia"]),
                ).fetchone()
                if collision:
                    suffix = report["sha256"][:6].upper()
                    numero, prefixo = f"{numero}-{suffix}", f"{prefixo}-{suffix}"
                conexao.execute(
                    """
                    INSERT INTO relatorios_emitidos
                    (numero, prefixo, ano, sequencia, emitido_em, pn, serial_number, conteudo_html, sha256, criado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (numero, prefixo, report["ano"], report["sequencia"], report["emitido_em"],
                           self._normalizar_pn(report.get("pn")), self._normalizar_sn(report.get("serial_number")),
                           report["conteudo_html"], sha256, report["criado_em"])
                )
                conexao.execute("DELETE FROM relatorios_emitidos_excluidos WHERE sha256 = ?", (sha256,))
                imported_reports += 1
        return {"records": imported_records, "reports": imported_reports}

    @staticmethod
    def _normalizar_prefixo_relatorio(prefixo):
        """Mantém o prefixo legível e seguro para identificação do relatório."""
        prefixo = re.sub(r"[^A-Za-z0-9_-]+", "", str(prefixo or "").upper()).strip("_-")
        return prefixo[:20] or "REL"

    def proximo_numero_relatorio(self, prefixo, emitido_em=None):
        """Informa o próximo número sem reservar nem alterar a sequência."""
        prefixo = self._normalizar_prefixo_relatorio(prefixo)
        emitido_em = emitido_em or datetime.now()
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT ultima_sequencia AS ultima FROM relatorios_sequencias "
                "WHERE prefixo = ? AND ano = ?",
                (prefixo, emitido_em.year),
            ).fetchone()
        sequencia = int(linha["ultima"]) + 1 if linha else 1
        return f"{prefixo}-{sequencia:03d}-{emitido_em.year % 100:02d}"

    def emitir_relatorio(self, prefixo, pn, sn, renderizar):
        """Reserva a sequência anual e persiste a versão imutável do relatório.

        ``renderizar`` recebe o número e a data de emissão já definidos. Assim,
        a reimpressão usa o mesmo HTML, número e horário da primeira emissão.
        """
        prefixo = self._normalizar_prefixo_relatorio(prefixo)
        emitido_em = datetime.now()
        ano = emitido_em.year
        with self._conectar() as conexao:
            # Evita duplicidade de sequência quando duas emissões ocorrem juntas.
            conexao.execute("BEGIN IMMEDIATE")
            conexao.execute(
                """
                INSERT INTO relatorios_sequencias (prefixo, ano, ultima_sequencia)
                VALUES (?, ?, 0)
                ON CONFLICT(prefixo, ano) DO NOTHING
                """,
                (prefixo, ano),
            )
            conexao.execute(
                """
                UPDATE relatorios_sequencias
                SET ultima_sequencia = ultima_sequencia + 1
                WHERE prefixo = ? AND ano = ?
                """,
                (prefixo, ano),
            )
            linha = conexao.execute(
                "SELECT ultima_sequencia AS ultima FROM relatorios_sequencias "
                "WHERE prefixo = ? AND ano = ?",
                (prefixo, ano),
            ).fetchone()
            sequencia = int(linha["ultima"])
            numero = f"{prefixo}-{sequencia:03d}-{ano % 100:02d}"
            conteudo_html = _garantir_campo_sha(renderizar(numero, emitido_em))
            sha256 = calcular_sha256_relatorio(conteudo_html)
            conteudo_html = inserir_sha256_relatorio(conteudo_html, sha256)
            conexao.execute(
                """
                INSERT INTO relatorios_emitidos
                (numero, prefixo, ano, sequencia, emitido_em, pn, serial_number, conteudo_html, sha256, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    numero, prefixo, ano, sequencia, emitido_em.isoformat(timespec="minutes"),
                    self._normalizar_pn(pn), self._normalizar_sn(sn), conteudo_html, sha256,
                    _timestamp_sincronizacao(),
                ),
            )
        return {"numero": numero, "emitido_em": emitido_em, "conteudo_html": conteudo_html, "sha256": sha256}

    def buscar_relatorios_emitidos(self, termo="", ano=None, mes=None, limite=100):
        """Lista relatórios emitidos para consulta e reimpressão."""
        termo = str(termo or "").strip()
        if ano is not None:
            ano = int(ano)
        if mes is not None:
            mes = int(mes)
            if mes not in range(1, 13):
                raise ValueError("Mês do relatório inválido.")
        filtros, parametros = [], []
        if ano is not None:
            filtros.append("ano = ?")
            parametros.append(ano)
        if mes is not None:
            filtros.append("CAST(substr(emitido_em, 6, 2) AS INTEGER) = ?")
            parametros.append(mes)
        with self._conectar() as conexao:
            if termo:
                termo = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                filtros.insert(0, "(numero LIKE ? ESCAPE '\\' OR pn LIKE ? ESCAPE '\\' OR serial_number LIKE ? ESCAPE '\\')")
                parametros[0:0] = [f"%{termo}%", f"%{termo}%", f"%{termo}%"]
                linhas = conexao.execute(
                    "SELECT id, numero, emitido_em, pn, serial_number FROM relatorios_emitidos "
                    f"WHERE {' AND '.join(filtros)} ORDER BY ano DESC, sequencia DESC LIMIT ?",
                    (*parametros, limite),
                ).fetchall()
            else:
                clausula = f"WHERE {' AND '.join(filtros)}" if filtros else ""
                linhas = conexao.execute(
                    "SELECT id, numero, emitido_em, pn, serial_number FROM relatorios_emitidos "
                    f"{clausula} ORDER BY ano DESC, sequencia DESC LIMIT ?",
                    (*parametros, limite),
                ).fetchall()
        return [dict(linha) for linha in linhas]

    def anos_relatorios_emitidos(self):
        with self._conectar() as conexao:
            linhas = conexao.execute(
                "SELECT DISTINCT ano FROM relatorios_emitidos ORDER BY ano DESC"
            ).fetchall()
        return [int(linha["ano"]) for linha in linhas]

    def remover_relatorio_emitido(self, relatorio_id):
        """Exclui o relatório e registra a marca para sincronizá-lo entre computadores."""
        with self._conectar() as conexao:
            relatorio = conexao.execute(
                "SELECT numero, sha256 FROM relatorios_emitidos WHERE id = ?", (relatorio_id,)
            ).fetchone()
            if relatorio is None:
                return None
            conexao.execute("DELETE FROM relatorios_emitidos WHERE id = ?", (relatorio_id,))
            conexao.execute(
                """
                INSERT INTO relatorios_emitidos_excluidos (sha256, excluido_em)
                VALUES (?, ?)
                ON CONFLICT(sha256) DO UPDATE SET excluido_em = excluded.excluido_em
                """,
                (relatorio["sha256"], _timestamp_sincronizacao()),
            )
        return dict(relatorio)

    def obter_relatorio_emitido(self, relatorio_id):
        with self._conectar() as conexao:
            linha = conexao.execute(
                "SELECT id, numero, emitido_em, pn, serial_number, conteudo_html, sha256 "
                "FROM relatorios_emitidos WHERE id = ?",
                (relatorio_id,),
            ).fetchone()
        return dict(linha) if linha else None


def _logo_empresa_data_uri(caminho_logo):
    """Converte a logo selecionada em URI embutida para o relatório portátil."""
    if not caminho_logo:
        return ""

    tipos_mime = {
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }
    try:
        arquivo_logo = Path(caminho_logo)
        dados = arquivo_logo.read_bytes()
    except OSError:
        return ""
    tipo_mime = tipos_mime.get(arquivo_logo.suffix.lower())
    if not dados or tipo_mime is None:
        return ""
    return f"data:{tipo_mime};base64,{base64.b64encode(dados).decode('ascii')}"


def montar_relatorio_html(
    informacoes_peca,
    norma,
    parametros,
    resultado,
    unidade_arco,
    unidade_exposicao,
    grafico_base64,
    caminho_logo=None,
    numero_relatorio=None,
    emitido_em=None,
    medicoes_laminas=None,
    assinaturas=None,
    sha256=None,
):
    """Monta um relatório HTML autocontido, seguro para arquivamento e impressão."""
    def linhas_tabela(campos):
        linhas = []
        for rotulo, valor in campos:
            valor = str(valor).strip()
            linhas.append(
                f"<tr><th>{html.escape(texto_campo(str(rotulo)))}</th><td>{html.escape(valor or tr('no_information'))}</td></tr>"
            )
        return "\n".join(linhas) or f"<tr><td colspan='2'>{tr('no_information')}</td></tr>"

    def linhas_medicoes_laminas(medicoes):
        if not medicoes:
            return f"<tr><td colspan='6'>{html.escape(tr('no_information'))}</td></tr>"

        def formatar_exposicao(valor):
            """Exibe a exposição sem casas decimais artificiais."""
            return format(float(valor), ".15g")

        return "\n".join(
            "<tr>"
            f"<td>{int(medicao['indice'])}</td>"
            f"<td>{html.escape(str(medicao['lamina']))}</td>"
            f"<td>{formatar_exposicao(medicao['exposicao'])}</td>"
            f"<td>{float(medicao['altura_lida']):.4f}</td>"
            f"<td>{float(medicao['desvio']):+.4f}</td>"
            f"<td>{float(medicao['altura_compensada']):.4f}</td>"
            "</tr>"
            for medicao in medicoes
        )

    resultados = [
        (tr("saturation_time"), f"{resultado['t_sat']:.2f} {unidade_exposicao}"),
        (tr("intensity"), f"{resultado['h_sat']:.4f} {unidade_arco}"),
        (tr("point_2t"), f"{resultado['t_2sat']:.2f} {unidade_exposicao}"),
        (tr("height_2t"), f"{resultado['h_2sat']:.4f} {unidade_arco}"),
        (tr("fit"), f"{resultado['r2']:.4f}"),
        (tr("measurements"), str(len(resultado['h_data_compensada']))),
    ]
    validacao = resultado.get("validacao")
    if validacao:
        if validacao["valida"]:
            status_validacao = tr("curve_valid")
        else:
            motivos = "; ".join(tr(motivo) for motivo in validacao["motivos"])
            status_validacao = tr("curve_invalid", reasons=motivos)
        resultados.append((tr("curve_validation"), status_validacao))
        resultados.append((tr("curve_2t_increase"), f"{validacao['aumento_2t'] * 100:.2f}%"))
    data_emissao = (emitido_em or datetime.now()).strftime("%d/%m/%Y %H:%M")
    logo_empresa = _logo_empresa_data_uri(caminho_logo)
    rotulo_pagina = html.escape(tr("report_page"))
    logo_html = (
        f'<img class="logo-empresa" src="{logo_empresa}" alt="{html.escape(tr("company_logo"))}">'
        if logo_empresa
        else ""
    )
    return f"""<!doctype html>
<html lang="{html_language()}">
<head>
<meta charset="utf-8">
<title>{tr('html_report_heading')}</title>
<style>
    @page {{ size: A4; margin: 12mm; }}
    body {{ color: #172033; font: 10.5pt Arial, sans-serif; margin: 0; }}
    .cabecalho {{ align-items: center; border: 1.5px solid #2f80c4; border-radius: 5px; display: flex; gap: 18px; margin-bottom: 18px; min-height: 92px; padding: 12px 16px; }}
    .cabecalho-conteudo {{ flex: 1; min-width: 0; }}
    h1 {{ color: #153e67; font-size: 18pt; margin: 0 0 4px; }}
    .logo-empresa {{ border-right: 1px solid #b7c9da; flex: 0 0 165px; height: 92px; object-fit: contain; order: -1; padding-right: 18px; width: 165px; }}
    h2 {{ border-bottom: 2px solid #2f80c4; color: #153e67; font-size: 12pt; margin: 20px 0 7px; padding-bottom: 3px; }}
    .subtitle {{ color: #52606d; margin: 0; }}
    .meta {{ color: #52606d; font-size: 8.5pt; margin-top: 10px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 5px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #eef5fb; font-weight: bold; width: 38%; }}
    .norma {{ background: #f1f8f4; border-left: 4px solid #2e9b62; padding: 8px; white-space: pre-line; }}
    .grafico {{ border: 1px solid #cbd5e1; box-sizing: border-box; margin-top: 8px; max-width: 100%; padding: 8px; width: 100%; }}
    .aviso {{ background: #fff8e5; border-left: 4px solid #e0a020; margin-top: 18px; padding: 10px; }}
    .medicoes-laminas th {{ width: auto; text-align: center; }}
    .medicoes-laminas td {{ text-align: center; }}
    .medicoes-laminas td:nth-child(2) {{ text-align: left; }}
    .formula-compensacao {{ color: #52606d; font-size: 9pt; margin: 0 0 8px; }}
    .assinaturas {{ margin-top: 22px; }}
    .assinaturas-grade {{ display: flex; gap: 34px; margin-top: 30px; }}
    .assinatura {{ flex: 1; min-width: 0; text-align: center; }}
    .linha-assinatura {{ border-top: 1px solid #172033; margin: 0 auto 7px; width: 90%; }}
    .integridade-relatorio {{ background: #f5f8fb; border: 1px solid #cbd5e1; font-size: 8.5pt; margin-top: 22px; padding: 8px 10px; }}
    .integridade-relatorio code {{ display: block; font-family: Consolas, monospace; margin-top: 4px; overflow-wrap: anywhere; }}
    .integridade-relatorio p {{ color: #52606d; margin: 5px 0 0; }}
    .pagina-relatorio {{ box-sizing: border-box; break-after: page; display: flex; flex-direction: column; min-height: 273mm; page-break-after: always; }}
    .pagina-relatorio:last-child {{ break-after: auto; page-break-after: auto; }}
    .rodape-pagina {{ color: #52606d; font: 8pt Arial, sans-serif; margin-top: auto; padding-top: 5mm; text-align: right; }}
</style>
</head>
<body>
<main>
<section class="pagina-relatorio">
<header class="cabecalho">
    {logo_html}
    <div class="cabecalho-conteudo">
        <h1>{tr('html_report_heading')}</h1>
        <p class="subtitle">{tr('report_subtitle')}</p>
        {f'<p class="meta"><strong>{html.escape(tr("report_number"))}:</strong> {html.escape(numero_relatorio)}</p>' if numero_relatorio else ''}
        <p class="meta">{tr('issued', date=data_emissao)}</p>
    </div>
</header>
<h2>{tr('piece_information')}</h2>
<table>{linhas_tabela(informacoes_peca.items())}</table>
<h2>{tr('standard_to_meet')}</h2>
<div class="norma">{html.escape(str(norma).strip() or tr('no_information'))}</div>
<h2>{tr('process_parameters')}</h2>
<table>{linhas_tabela(parametros.items())}</table>
<footer class="rodape-pagina">{rotulo_pagina} 1</footer>
</section>
<section class="pagina-relatorio">
<section class="resultado-curva">
    <h2>{tr('curve_results')}</h2>
    <table>{linhas_tabela(resultados)}</table>
    <h2>{tr('saturation_chart')}</h2>
    <img class="grafico" src="data:image/png;base64,{grafico_base64}" alt="{tr('saturation_chart')}">
</section>
<footer class="rodape-pagina">{rotulo_pagina} 2</footer>
</section>
<section class="pagina-relatorio">
<section class="medicoes-laminas">
    <h2>{tr('strip_measurements_table')}</h2>
    <p class="formula-compensacao">{tr('strip_compensation_formula')}</p>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>{tr('blade_id')}</th>
                <th>{tr('exposure')} ({html.escape(unidade_exposicao)})</th>
                <th>{tr('reading_after_exposure')} ({html.escape(unidade_arco)})</th>
                <th>{tr('deviation')} ({html.escape(unidade_arco)})</th>
                <th>{tr('compensated_value')} ({html.escape(unidade_arco)})</th>
            </tr>
        </thead>
        <tbody>{linhas_medicoes_laminas(medicoes_laminas)}</tbody>
    </table>
    <section class="assinaturas">
        <h2>{tr('signatures')}</h2>
        <div class="assinaturas-grade">
            <div class="assinatura">
                <div class="linha-assinatura"></div>
                <strong>{tr('operator')}</strong>
            </div>
            <div class="assinatura">
                <div class="linha-assinatura"></div>
                <strong>{tr('quality_representative')}</strong>
            </div>
        </div>
    </section>
    <section class="integridade-relatorio">
        <strong>{tr('integrity_sha256')}</strong>
        <code data-report-sha="true">{html.escape(sha256 or _SHA_PLACEHOLDER)}</code>
        <p>{tr('integrity_sha256_note')}</p>
    </section>
</section>
<footer class="rodape-pagina">{rotulo_pagina} 3</footer>
</section>
</main>
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

    def exibir_janela_em_primeiro_plano():
        """Garante a abertura à frente após o Windows criar a janela."""
        if not janela.winfo_exists():
            return
        janela.deiconify()
        janela.attributes("-topmost", True)
        janela.lift()
        janela.focus_force()

        def restaurar_empilhamento_normal():
            if not janela.winfo_exists():
                return
            janela.attributes("-topmost", False)
            janela.lift()
            janela.focus_force()

        # Mantém a janela acima apenas durante a abertura. Em seguida ela
        # volta ao comportamento normal do Windows, inclusive minimizar.
        janela.after(900, restaurar_empilhamento_normal)

    # A criação visual ocorre após o retorno ao loop do Tk. Adiar esta ação
    # impede que a janela principal a cubra ao concluir a própria renderização.
    janela.after(200, exibir_janela_em_primeiro_plano)
    # A janela permanece não modal para que a barra de título do Windows
    # ofereça o controle padrão de minimizar e o usuário possa consultar a
    # curva principal enquanto administra os dados e o relatório.
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
    criar_campo_texto(area_peca, "Router", 0, 0, campos_peca)
    criar_campo_texto(area_peca, "Peça / PN", 0, 1, campos_peca)
    criar_campo_texto(area_peca, "SN da peça", 1, 0, campos_peca)
    criar_campo_texto(area_peca, "Referencia-CMM", 1, 1, campos_peca)
    criar_campo_texto(area_peca, "Reparo", 2, 0, campos_peca)
    criar_campo_texto(area_peca, "Esfera", 2, 1, campos_peca)

    norma_var = ctk.StringVar()
    campo_norma = ctk.CTkFrame(area_peca, fg_color="transparent")
    campo_norma.grid(row=4, column=0, columnspan=2, padx=0, pady=(3, 5), sticky="ew")
    campo_norma.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(campo_norma, text=tr("standard")).grid(row=0, column=0, pady=(0, 1), sticky="w")
    ctk.CTkComboBox(campo_norma, variable=norma_var, values=normas_relatorio(), height=30).grid(row=1, column=0, sticky="ew")

    campos_medidas_peca = {}
    criar_campo_medida(area_peca, "Intensidade de peening", 3, 0, campos_medidas_peca)
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
            entrada.insert(0, dados_completos.get(rotulo, ""))
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
        curva = app.banco_pn.obter_curva(pn, sn)
        if curva is not None:
            app.carregar_curva_de_referencia(curva, dados.get("Router", ""), pn, sn)
        preencher(dados)
        busca_entry.delete(0, "end")
        busca_entry.insert(0, dados["Peça / PN"])
        app.dados_relatorio = dados
        app.lbl_status.configure(text=tr("pn_loaded", pn=dados["Peça / PN"]), text_color="#2ecc71")

    def salvar_atualizacao():
        try:
            dados = coletar_dados()
            curva = app.curva_atual_para_salvar()
            if curva is not None:
                curva.update(
                    {
                        "intensidade": dados["Intensidade de peening"],
                        "unidade_intensidade": dados["Unidade de Intensidade de peening"],
                    }
                )
            dados = app.banco_pn.salvar(dados, curva)
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

        try:
            medicoes_laminas = app.obter_medicoes_laminas_para_relatorio()
        except ValueError as err:
            app.lbl_status.configure(text=str(err), text_color="#e74c3c")
            return

        def valor_com_unidade(rotulo):
            valor = dados[rotulo]
            return f"{valor} {dados[f'Unidade de {rotulo}']}" if valor else ""

        parametros = {
            "Tipo de lâmina Almen": app._nome_tipo_lamina(),
            "Unidade de exposição": f"{app._nome_tipo_exposicao()} ({app.abreviacao_exposicao})",
            "Unidade da altura do arco": app.unidade_arco,
            **{rotulo: valor_com_unidade(rotulo) for rotulo in ("Intensidade de peening", "Dureza")},
            "Esfera": dados["Esfera"],
            **{
                rotulo: dados[rotulo] if rotulo in CAMPO_TEXTO_RELATORIO else valor_com_unidade(rotulo)
                for rotulo in CAMPOS_DADOS_EQUIPAMENTO_RELATORIO
            },
            "Desvios de lâmina cadastrados": ", ".join(
                f"{nome}: {valor:+.4f} {app.unidade_arco}" for nome, valor in app.desvios_laminas.items()
            ) or tr("none_applied"),
            "Observações": dados["Observações"],
        }
        informacoes_peca = {
            rotulo: dados[rotulo]
            for rotulo in ("Router", "Peça / PN", "SN da peça", "Referencia-CMM", "Reparo")
        }
        buffer_grafico = BytesIO()
        destaque_atual = getattr(app, "_destaque_intensidade_atual", None)
        remover_destaque_faixa_intensidade(app.ax, destaque_atual)
        destaque = destacar_faixa_intensidade(
            app.ax,
            dados["Intensidade de peening"],
            dados["Unidade de Intensidade de peening"],
            app.unidade_arco,
            tr(
                "required_peening_intensity_legend",
                value=dados["Intensidade de peening"],
                unit=dados["Unidade de Intensidade de peening"],
            ),
        )
        try:
            app.fig.savefig(buffer_grafico, format="png", dpi=180, facecolor=app.fig.get_facecolor(), bbox_inches="tight")
        finally:
            remover_destaque_faixa_intensidade(app.ax, destaque)
            if destaque_atual is not None:
                intensidade_atual, unidade_atual = app._intensidade_destaque_exemplo
                app._destaque_intensidade_atual = destacar_faixa_intensidade(
                    app.ax,
                    intensidade_atual,
                    unidade_atual,
                    app.unidade_arco,
                    tr(
                        "required_peening_intensity_legend",
                        value=intensidade_atual,
                        unit=unidade_atual,
                    ),
                )
        data_emissao = datetime.now()
        numero_relatorio = app.banco_pn.proximo_numero_relatorio(app.prefixo_relatorio, data_emissao)
        nome_arquivo = nome_arquivo_pdf_relatorio(
            numero_relatorio,
            dados["Peça / PN"],
            dados["SN da peça"],
            data_emissao,
        )
        caminho = filedialog.asksaveasfilename(
            parent=janela,
            title=tr("save_report"),
            defaultextension=".pdf",
            filetypes=[(tr("pdf_file"), "*.pdf")],
            initialfile=nome_arquivo,
        )
        if not caminho:
            return
        try:
            grafico_base64 = base64.b64encode(buffer_grafico.getvalue()).decode("ascii")

            def renderizar(numero_relatorio, emitido_em):
                return montar_relatorio_html(
                    informacoes_peca,
                    dados["Norma"],
                    parametros,
                    app._ultimo_resultado,
                    app.unidade_arco,
                    app.abreviacao_exposicao,
                    grafico_base64,
                    app.logo_empresa_path,
                    numero_relatorio,
                    emitido_em,
                    medicoes_laminas,
                )

            emissao = app.banco_pn.emitir_relatorio(
                app.prefixo_relatorio,
                dados["Peça / PN"],
                dados["SN da peça"],
                renderizar,
            )
            converter_relatorio_html_para_pdf(emissao["conteudo_html"], caminho)
            app.lbl_status.configure(
                text=tr("report_generated_numbered", number=emissao["numero"]), text_color="#2ecc71"
            )
            janela.destroy()
        except OSError as err:
            app.lbl_status.configure(text=tr("save_report_error", message=err), text_color="#e74c3c")

    botao_buscar = ctk.CTkButton(busca_frame, text=tr("search"), width=100, command=atualizar_resultados)
    botao_buscar.grid(
        row=1, column=4, padx=(0, 14), pady=(0, 12)
    )
    add_tooltip(botao_buscar, tr("tooltip_search_pn"))
    resultado_busca.configure(command=carregar_pn)
    busca_entry.bind("<Return>", lambda _evento: atualizar_resultados())
    busca_entry.bind("<KeyRelease>", lambda _evento: atualizar_resultados())

    preencher(app.dados_relatorio)
    botoes_frame = ctk.CTkFrame(janela, fg_color="transparent")
    botoes_frame.grid(row=3, column=0, padx=24, pady=(0, 18), sticky="ew")
    botoes_frame.grid_columnconfigure(0, weight=1)
    botoes_frame.grid_columnconfigure(1, weight=1)
    botoes_frame.grid_columnconfigure(2, weight=2)
    save_pn_button = ctk.CTkButton(botoes_frame, text=tr("save_update_pn"), height=40, command=salvar_atualizacao)
    save_pn_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")
    add_tooltip(save_pn_button, tr("tooltip_save_update_pn"))
    delete_pn_button = ctk.CTkButton(
        botoes_frame, text=tr("delete_pn"), height=40, fg_color="#c0392b", hover_color="#e74c3c", command=excluir_pn
    )
    delete_pn_button.grid(row=0, column=1, padx=8, sticky="ew")
    add_tooltip(delete_pn_button, tr("tooltip_delete_pn"))
    generate_report_button = ctk.CTkButton(
        botoes_frame, text=tr("generate_html"), height=40, fg_color="#1f6fae", hover_color="#2f80c4", command=gerar
    )
    generate_report_button.grid(row=0, column=2, padx=(8, 0), sticky="ew")
    add_tooltip(generate_report_button, tr("tooltip_generate_html"))

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

    def inicializar_layout():
        """Exibe o início do formulário ao abrir, sem ocultar Router e PN."""
        ajustar_layout()
        formularios_frame._parent_canvas.yview_moveto(0)

    janela.after_idle(inicializar_layout)


def abrir_historico_relatorios(app):
    """Mostra as emissões arquivadas e abre a versão original para reimpressão."""
    janela = ctk.CTkToplevel(app)
    janela.title(tr("generated_reports"))
    janela.geometry("860x620")
    janela.minsize(700, 500)
    janela.transient(app)
    janela.grid_columnconfigure(0, weight=1)
    janela.grid_rowconfigure(4, weight=1)

    path_icon = resource_path("assets/icons/logo.ico")
    if os.path.exists(path_icon):
        janela.iconbitmap(path_icon)
        janela.after(
            300,
            lambda: janela.iconbitmap(path_icon) if janela.winfo_exists() else None,
        )

    ctk.CTkLabel(janela, text=tr("generated_reports"), font=ctk.CTkFont(size=20, weight="bold")).grid(
        row=0, column=0, padx=24, pady=(20, 8), sticky="w"
    )
    ctk.CTkLabel(
        janela,
        text=tr("current_month_reports_hint"),
        text_color="#52606d",
    ).grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
    filtro_frame = ctk.CTkFrame(janela, fg_color="transparent")
    filtro_frame.grid(row=2, column=0, padx=24, pady=(4, 4), sticky="ew")
    filtro_frame.grid_columnconfigure(4, weight=1)
    agora = datetime.now()
    anos = [agora.year, *[ano for ano in app.banco_pn.anos_relatorios_emitidos() if ano != agora.year]]
    ano_var = ctk.StringVar(value=str(agora.year))
    mes_var = ctk.StringVar(value=f"{agora.month:02d}")
    meses = [f"{mes:02d}" for mes in range(1, 13)]
    ctk.CTkLabel(filtro_frame, text=tr("report_year")).grid(row=0, column=0, padx=(0, 6), sticky="w")
    ano_menu = ctk.CTkOptionMenu(filtro_frame, variable=ano_var, values=[str(ano) for ano in anos], width=100)
    ano_menu.grid(row=0, column=1, padx=(0, 14), sticky="w")
    ctk.CTkLabel(filtro_frame, text=tr("report_month")).grid(row=0, column=2, padx=(0, 6), sticky="w")
    mes_menu = ctk.CTkOptionMenu(filtro_frame, variable=mes_var, values=meses, width=90)
    mes_menu.grid(row=0, column=3, padx=(0, 12), sticky="w")
    busca_frame = ctk.CTkFrame(janela, fg_color="transparent")
    busca_frame.grid(row=3, column=0, padx=24, pady=(4, 8), sticky="ew")
    busca_frame.grid_columnconfigure(0, weight=1)
    busca_entry = ctk.CTkEntry(busca_frame, placeholder_text=tr("report_search_placeholder"))
    busca_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
    lista = ctk.CTkScrollableFrame(janela, corner_radius=10)
    lista.grid(row=4, column=0, padx=24, pady=(0, 20), sticky="nsew")
    lista.grid_columnconfigure(0, weight=1)

    def reimprimir(relatorio_id):
        relatorio = app.banco_pn.obter_relatorio_emitido(relatorio_id)
        if not relatorio:
            app.lbl_status.configure(text=tr("report_not_found"), text_color="#e74c3c")
            return
        try:
            arquivo_html = enviar_relatorio_html_para_impressora(
                relatorio["conteudo_html"], user_data_file(f"reimpressao_{relatorio_id}.html")
            )
            app.lbl_status.configure(
                text=tr("report_reprint_ready", number=relatorio["numero"]), text_color="#2ecc71"
            )
            messagebox.showinfo(
                tr("reprint_report"),
                f"{tr('report_reprint_ready', number=relatorio['numero'])}\n\n{arquivo_html}",
                parent=janela,
            )
        except Exception as err:
            mensagem = tr("save_report_error", message=err)
            app.lbl_status.configure(text=mensagem, text_color="#e74c3c")
            messagebox.showerror(tr("reprint_report"), mensagem, parent=janela)

    def imprimir_em_pdf(relatorio_id):
        relatorio = app.banco_pn.obter_relatorio_emitido(relatorio_id)
        if not relatorio:
            app.lbl_status.configure(text=tr("report_not_found"), text_color="#e74c3c")
            return

        try:
            arquivo_html = abrir_relatorio_html_para_impressao(
                relatorio["conteudo_html"], user_data_file(f"imprimir_{relatorio_id}.html")
            )
            app.lbl_status.configure(
                text=tr("print_pdf_ready", number=relatorio["numero"]), text_color="#2ecc71"
            )
            messagebox.showinfo(
                tr("print_pdf"),
                f"{tr('print_pdf_ready', number=relatorio['numero'])}\n\n{arquivo_html}",
                parent=janela,
            )
        except Exception as err:
            mensagem = tr("print_pdf_error", message=err)
            app.lbl_status.configure(text=mensagem, text_color="#e74c3c")
            messagebox.showerror(tr("print_pdf"), mensagem, parent=janela)

    def exportar_pdf(relatorio_id):
        relatorio = app.banco_pn.obter_relatorio_emitido(relatorio_id)
        if not relatorio:
            app.lbl_status.configure(text=tr("report_not_found"), text_color="#e74c3c")
            return

        destino = filedialog.asksaveasfilename(
            parent=janela,
            title=tr("export_pdf"),
            initialfile=tr("numbered_report_file", number=relatorio["numero"]),
            defaultextension=".pdf",
            filetypes=[(tr("pdf_file"), "*.pdf")],
        )
        if not destino:
            return

        try:
            arquivo_pdf = converter_relatorio_html_para_pdf(relatorio["conteudo_html"], destino)
            app.lbl_status.configure(
                text=tr("pdf_export_ready", number=relatorio["numero"]), text_color="#2ecc71"
            )
            messagebox.showinfo(
                tr("export_pdf"),
                f"{tr('pdf_export_ready', number=relatorio['numero'])}\n\n{arquivo_pdf}",
                parent=janela,
            )
        except Exception as err:
            mensagem = tr("pdf_export_error", message=err)
            app.lbl_status.configure(text=mensagem, text_color="#e74c3c")
            messagebox.showerror(tr("export_pdf"), mensagem, parent=janela)

    def excluir(relatorio_id, numero):
        if not messagebox.askyesno(
            tr("delete_report"), tr("delete_report_confirmation", number=numero), parent=janela
        ):
            return
        relatorio = app.banco_pn.remover_relatorio_emitido(relatorio_id)
        if not relatorio:
            app.lbl_status.configure(text=tr("report_not_found"), text_color="#e74c3c")
            atualizar()
            return
        app.lbl_status.configure(text=tr("report_deleted", number=relatorio["numero"]), text_color="#2ecc71")
        atualizar()

        # Envia a marca de exclusão logo após a confirmação, sem bloquear a
        # janela. Se estiver offline, ela permanece no banco local e a próxima
        # sincronização automática/manual a reenviará.
        def sincronizar_exclusao():
            try:
                from curvsat.services.license import sync_active_system_data
                sync_active_system_data()
            except Exception:
                pass

        threading.Thread(target=sincronizar_exclusao, daemon=True).start()

    def filtros_ativos():
        # A busca nominal é uma alternativa ao período atual e permite localizar
        # imediatamente relatórios antigos por número, PN ou serial.
        if busca_entry.get().strip():
            return None, None
        return int(ano_var.get()), int(mes_var.get())

    def atualizar():
        for widget in lista.winfo_children():
            widget.destroy()
        ano, mes = filtros_ativos()
        relatorios = app.banco_pn.buscar_relatorios_emitidos(busca_entry.get(), ano=ano, mes=mes)
        if not relatorios:
            ctk.CTkLabel(lista, text=tr("no_generated_reports")).grid(row=0, column=0, padx=14, pady=18, sticky="w")
            return
        for indice, relatorio in enumerate(relatorios):
            cor_destaque = "#eaf4ff" if indice % 2 == 0 else "#f5f9fd"
            item = ctk.CTkFrame(lista, corner_radius=8, fg_color=cor_destaque)
            item.grid(row=indice, column=0, padx=4, pady=4, sticky="ew")
            item.grid_columnconfigure(0, weight=1)
            detalhe = " | ".join(filter(None, [relatorio["pn"], relatorio["serial_number"]])) or tr("no_information")
            ctk.CTkLabel(
                item,
                text=f"{relatorio['numero']}\n{detalhe} — {relatorio['emitido_em'].replace('T', ' ')}",
                justify="left",
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=9, sticky="ew")
            export_button = ctk.CTkButton(
                item, text="\U0001F4E5", width=52, height=42, font=ctk.CTkFont(size=22),
                command=lambda relatorio_id=relatorio["id"]: exportar_pdf(relatorio_id),
            )
            export_button.grid(row=0, column=1, padx=(10, 5), pady=9)
            add_tooltip(export_button, tr("tooltip_export_pdf"))
            pdf_button = ctk.CTkButton(
                item, text="\U0001F4C4", width=52, height=42, font=ctk.CTkFont(size=22),
                command=lambda relatorio_id=relatorio["id"]: imprimir_em_pdf(relatorio_id),
            )
            pdf_button.grid(row=0, column=2, padx=5, pady=9)
            add_tooltip(pdf_button, tr("tooltip_print_pdf"))
            reprint_button = ctk.CTkButton(
                item, text="\U0001F5A8", width=52, height=42, font=ctk.CTkFont(size=22),
                command=lambda relatorio_id=relatorio["id"]: reimprimir(relatorio_id),
            )
            reprint_button.grid(row=0, column=3, padx=5, pady=9)
            add_tooltip(reprint_button, tr("tooltip_reprint_report"))
            delete_button = ctk.CTkButton(
                item,
                text="\U0001F5D1",
                width=52,
                height=42,
                font=ctk.CTkFont(size=22),
                fg_color="#c0392b",
                hover_color="#e74c3c",
                command=lambda relatorio_id=relatorio["id"], numero=relatorio["numero"]: excluir(relatorio_id, numero),
            )
            delete_button.grid(row=0, column=4, padx=(5, 10), pady=9)
            add_tooltip(delete_button, tr("tooltip_delete_report"))

    search_button = ctk.CTkButton(busca_frame, text=tr("search"), width=105, command=atualizar)
    search_button.grid(row=0, column=1)
    add_tooltip(search_button, tr("tooltip_search_reports"))
    busca_entry.bind("<Return>", lambda _evento: atualizar())
    busca_entry.bind("<KeyRelease>", lambda _evento: atualizar())
    ano_menu.configure(command=lambda _valor: atualizar())
    mes_menu.configure(command=lambda _valor: atualizar())
    atualizar()
