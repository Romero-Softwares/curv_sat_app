import os, sys
import tkinter as tk
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
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

# ==============================================================================
# 1. LÓGICA DO SPLASH SCREEN (Executada ANTES dos imports pesados)
# ==============================================================================
splash = None
if __name__ == "__main__":
    splash = tk.Tk()
    splash.overrideredirect(True)  # Remove a barra de título e botões de fechar
    
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    
    try:
        # Usamos PIL para suportar .jpg
        from PIL import Image, ImageTk
        img_path = resource_path("assets/splash.jpg")
        
        if os.path.exists(img_path):
            img = Image.open(img_path)
            splash_width, splash_height = img.size
            
            # Centraliza com base no tamanho real da imagem
            pos_x = int((screen_width / 2) - (splash_width / 2))
            pos_y = int((screen_height / 2) - (splash_height / 2))
            splash.geometry(f"{splash_width}x{splash_height}+{pos_x}+{pos_y}")
            
            splash_image = ImageTk.PhotoImage(img)
            lbl_img = tk.Label(splash, image=splash_image, bg="black", borderwidth=0)
            lbl_img.image = splash_image  # Salva a referência
            lbl_img.pack(fill="both", expand=True)
        else:
            splash.geometry(f"400x150+{int(screen_width/2 - 200)}+{int(screen_height/2 - 75)}")
            tk.Label(splash, text="Carregando Curv Saturation...", font=("Arial", 14)).pack(expand=True)
            
    except ImportError:
        # Fallback caso a biblioteca Pillow não esteja disponível
        splash.geometry(f"400x150+{int(screen_width/2 - 200)}+{int(screen_height/2 - 75)}")
        tk.Label(splash, text="Carregando...", font=("Arial", 14)).pack(expand=True)
        
    splash.update()  # Força a exibição IMEDIATA da janela na tela

# ==============================================================================
# 2. IMPORTS PESADOS (Carregam enquanto a imagem já está na tela)
# ==============================================================================
import customtkinter as ctk
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pathlib import Path
import tempfile

from reports import BancoDadosPN, abrir_relatorio, criar_dados_relatorio, montar_relatorio_html as montar_relatorio_html_modulo
from technical_references import abrir_referencias_tecnicas
from i18n import LANGUAGES, load_language, save_language, tr

# ==============================================================================
# 3. RESTANTE DO SEU CÓDIGO ORIGINAL INTACTO
# ==============================================================================

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

MM_POR_POLEGADA = 25.4
UNIDADES_FLECHA = {"mm": "unit_mm", "in": "unit_in"}
UNIDADES_EXPOSICAO = {
    "seconds": ("s", "exposure_seconds"),
    "passes": ("pass", "exposure_passes"),
    "rotations": ("rot", "exposure_rotations"),
    "cycles": ("ciclos", "exposure_cycles"),
    "inverse_feed": ("inv. avanço", "exposure_inverse_feed"),
}
TIPOS_LAMINA = {"N": "almen_type_n", "A": "almen_type_a", "C": "almen_type_c"}

CAMPO_UNIDADE_RELATORIO = {
    "Altura do arco": ("mm", "in"),
    "Esfera": ("SAE (S)", "mm", "in"),
    "Dureza": ("HRC", "HV", "HB", "HS"),
    "Distância": ("mm", "cm", "in"),
    "Ângulo": ("°", "rad"),
    "Pressão": ("bar", "psi", "MPa", "kgf/cm²"),
}

CAMPO_TEXTO_RELATORIO = ("Peça / PN", "SN da peça", "Referência", "Reparo", "Equipamento", "Bico", "Injetor")
CAMPOS_DADOS_EQUIPAMENTO_RELATORIO = ("Equipamento", "Bico", "Injetor", "Distância", "Ângulo", "Pressão")


def almen_model(t, A, b):
    """Modelo exponencial de saturação usado para o ajuste SAE J2597."""
    return A * (1.0 - np.exp(-b * t))


def converter_flecha(valor, unidade_origem, unidade_destino):
    """Converte a altura de arco entre milímetros e polegadas."""
    if unidade_origem not in UNIDADES_FLECHA or unidade_destino not in UNIDADES_FLECHA:
        raise ValueError(tr("invalid_arc_unit"))
    if unidade_origem == unidade_destino:
        return float(valor)
    if unidade_origem == "mm":
        return float(valor) / MM_POR_POLEGADA
    return float(valor) * MM_POR_POLEGADA


def compensar_desvio_lamina(alturas, desvio_lamina=0.0):
    """Compensa desvios por lâmina definidos como medição indicada menos valor real."""
    alturas = np.asarray(alturas, dtype=float)
    desvios_lamina = np.asarray(desvio_lamina, dtype=float)
    if not np.isfinite(desvios_lamina).all():
        raise ValueError(tr("deviation_not_finite"))
    try:
        desvios_lamina = np.broadcast_to(desvios_lamina, alturas.shape)
    except ValueError as err:
        raise ValueError(tr("deviation_per_height")) from err
    alturas_compensadas = alturas - desvios_lamina
    if np.any(alturas_compensadas < 0):
        raise ValueError(tr("negative_compensated"))
    return alturas_compensadas


def calcular_saturacao(t_data, h_data, desvio_lamina=0.0):
    """Ajusta a curva compensada e determina T e 2T pela regra dos 10%."""
    t_data = np.asarray(t_data, dtype=float)
    h_data = np.asarray(h_data, dtype=float)

    if t_data.ndim != 1 or h_data.ndim != 1 or len(t_data) != len(h_data):
        raise ValueError(tr("data_vectors"))
    if not np.isfinite(t_data).all() or not np.isfinite(h_data).all():
        raise ValueError(tr("data_finite"))
    if np.any(t_data < 0):
        raise ValueError(tr("exposure_negative"))
    if np.any(h_data < 0):
        raise ValueError(tr("arc_negative"))
    h_data_compensada = compensar_desvio_lamina(h_data, desvio_lamina)
    if len(t_data) < 4:
        raise ValueError(tr("min_measurements"))
    if np.count_nonzero(h_data_compensada) < 4:
        raise ValueError(tr("min_nonzero_arc"))
    if len(np.unique(t_data)) < 2:
        raise ValueError(tr("distinct_exposure"))
    if np.ptp(h_data_compensada) == 0:
        raise ValueError(tr("varying_arc"))

    popt, _ = curve_fit(
        almen_model,
        t_data,
        h_data_compensada,
        p0=[float(np.max(h_data_compensada)), 0.1],
        bounds=(0, np.inf),
        maxfev=10_000,
    )
    A, b = popt
    if b <= np.finfo(float).eps:
        raise ValueError(tr("saturation_rate"))

    t_sat = np.log(10) / b
    h_sat = almen_model(t_sat, A, b)
    t_2sat = 2 * t_sat
    h_2sat = almen_model(t_2sat, A, b)

    residuos = h_data_compensada - almen_model(t_data, A, b)
    variacao_total = np.sum((h_data_compensada - np.mean(h_data_compensada)) ** 2)
    r2 = 1 - (np.sum(residuos**2) / variacao_total)

    return {
        "A": A,
        "b": b,
        "t_sat": t_sat,
        "h_sat": h_sat,
        "t_2sat": t_2sat,
        "h_2sat": h_2sat,
        "r2": r2,
        "desvios_lamina": np.broadcast_to(np.asarray(desvio_lamina, dtype=float), h_data.shape).copy(),
        "h_data_compensada": h_data_compensada,
    }


def montar_relatorio_html(informacoes_peca, norma, parametros, resultado, unidade_flecha, unidade_exposicao, grafico_base64):
    """Monta um relatório HTML autocontido, seguro para arquivamento e impressão."""
    def linhas_tabela(campos):
        linhas = []
        for rotulo, valor in campos:
            valor = str(valor).strip()
            linhas.append(
                f"<tr><th>{html.escape(str(rotulo))}</th><td>{html.escape(valor or 'Não informado.')}</td></tr>"
            )
        return "\n".join(linhas) or "<tr><td colspan='2'>Não informado.</td></tr>"

    resultados = [
        ("Tempo de saturação (T)", f"{resultado['t_sat']:.2f} {unidade_exposicao}"),
        ("Intensidade H(T)", f"{resultado['h_sat']:.4f} {unidade_flecha}"),
        ("Ponto 2T", f"{resultado['t_2sat']:.2f} {unidade_exposicao}"),
        ("Altura H(2T)", f"{resultado['h_2sat']:.4f} {unidade_flecha}"),
        ("Coeficiente de ajuste R²", f"{resultado['r2']:.4f}"),
        ("Medições utilizadas", str(len(resultado['h_data_compensada']))),
    ]
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório de Curva de Saturação Almen</title>
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
<h1>Relatório de Curva de Saturação Almen</h1>
<p class="subtitle">Registro técnico de ensaio e parâmetros do processo</p>
<p class="meta">Emitido em {data_emissao}</p>

<h2>Informações da peça</h2>
<table>{linhas_tabela(informacoes_peca.items())}</table>

<h2>Norma a ser atendida</h2>
<div class="norma">{html.escape(norma or 'Não informada.')}</div>

<h2>Parâmetros do processo</h2>
<table>{linhas_tabela(parametros.items())}</table>

<h2>Resultados da curva</h2>
<table>{linhas_tabela(resultados)}</table>

<h2>Gráfico de saturação</h2>
<img class="grafico" alt="Gráfico da curva de saturação Almen" src="data:image/png;base64,{grafico_base64}">

<div class="aviso">{html.escape(AVISO_NORMATIVO)}</div>
</body>
</html>"""


# Mantém a compatibilidade da API pública enquanto a implementação vive em reports.py.
montar_relatorio_html = montar_relatorio_html_modulo


class AlmenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.idioma = load_language()
        self.title(self.t("app_title"))
        self.geometry("1120x700")
        self.minsize(950, 600)

        self.rows = []
        self.unidade_flecha = "mm"
        self.tipo_lamina = "A"
        self.tipo_exposicao = "seconds"
        self.desvios_laminas = {"Lâmina 1": 0.0}
        self._arquivo_impressao = None
        self._ultimo_resultado = None
        self.dados_relatorio = {
            **{rotulo: "" for rotulo in CAMPO_TEXTO_RELATORIO},
            **{rotulo: "" for rotulo in CAMPO_UNIDADE_RELATORIO},
            **{f"Unidade de {rotulo}": unidades[0] for rotulo, unidades in CAMPO_UNIDADE_RELATORIO.items()},
            "Norma": "SAE J443 e SAE J2597",
            "Observações": "",
        }

        self.banco_pn = BancoDadosPN()
        self.dados_relatorio = criar_dados_relatorio()
        self._build_ui()
        self._load_sample_data()
        self.calcular_e_plotar()
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        
        caminho_icone = resource_path(relative_path="assets/icons/logo.ico")
        try:
            if os.path.exists(caminho_icone):
                self.iconbitmap(default=caminho_icone)
                self.iconbitmap(caminho_icone)
        except Exception:
            pass

    def ao_fechar(self):
        print("Encerrando o aplicativo e limpando processos...")
        self.destroy()
        os._exit(0)

    def t(self, key, **values):
        return tr(key, self.idioma, **values)

    def _recriar_interface(self):
        """Atualiza a interface ao trocar o idioma, preservando as medições."""
        dados_linhas = [
            (linha["tempo"].get(), linha["altura"].get(), linha["lamina_var"].get())
            for linha in self.rows
        ]
        for widget in self.winfo_children():
            widget.destroy()
        if hasattr(self, "fig"):
            plt.close(self.fig)
        self.rows = []
        self.title(self.t("app_title"))
        self._build_ui()
        for tempo, altura, lamina in dados_linhas:
            self.add_row(tempo, altura, lamina)
        self.calcular_e_plotar()

    @property
    def abreviacao_exposicao(self):
        return UNIDADES_EXPOSICAO[self.tipo_exposicao][0]

    def _nome_unidade_flecha(self, unidade=None):
        return self.t(UNIDADES_FLECHA[unidade or self.unidade_flecha])

    def _nome_tipo_lamina(self, tipo=None):
        return self.t(TIPOS_LAMINA[tipo or self.tipo_lamina])

    def _nome_tipo_exposicao(self, tipo=None):
        return self.t(UNIDADES_EXPOSICAO[tipo or self.tipo_exposicao][1])

    def _codigo_por_nome(self, opcoes, nome):
        return next(codigo for codigo, chave in opcoes.items() if self.t(chave if isinstance(chave, str) else chave[1]) == nome)

    def _build_ui(self):
        # O painel de dados permanece estável; o gráfico recebe toda a largura excedente.
        self.grid_columnconfigure(0, weight=0, minsize=420)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        left_frame = ctk.CTkFrame(self, width=420, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        left_frame.grid_propagate(False)
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame,
            text=self.t("measurements"),
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text=self.t("add_row"), width=76, command=self.add_row).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame,
            text=self.t("remove_row"),
            width=76,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self.remove_row,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame,
            text=self.t("example"),
            width=76,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._load_sample_data,
        ).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text=self.t("settings"), width=112, command=self.abrir_configuracoes).pack(
            side="right", padx=2
        )

        self.scroll_table = ctk.CTkScrollableFrame(left_frame, label_text="")
        self.scroll_table.grid(row=2, column=0, padx=15, pady=5, sticky="nsew")
        self.scroll_table.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            left_frame,
            text=self.t("calculate"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self.calcular_e_plotar,
        ).grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        ctk.CTkButton(
            left_frame,
            text=self.t("generate_report"),
            height=34,
            fg_color="#1f6fae",
            hover_color="#2f80c4",
            command=self.abrir_relatorio,
        ).grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")

        res_frame = ctk.CTkFrame(left_frame, fg_color="#1e1e1e", corner_radius=8)
        res_frame.grid(row=5, column=0, padx=15, pady=(0, 10), sticky="ew")
        res_frame.grid_columnconfigure((0, 1), weight=1)
        self.lbl_tsat = ctk.CTkLabel(res_frame, text=f"{self.t('saturation_time')}: --", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_tsat.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
        self.lbl_hsat = ctk.CTkLabel(
            res_frame, text=f"{self.t('intensity')}: --", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2ecc71"
        )
        self.lbl_hsat.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
        self.lbl_t2sat = ctk.CTkLabel(res_frame, text=f"{self.t('point_2t')}: --", font=ctk.CTkFont(size=12))
        self.lbl_t2sat.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        self.lbl_h2sat = ctk.CTkLabel(res_frame, text=f"{self.t('height_2t')}: --", font=ctk.CTkFont(size=12))
        self.lbl_h2sat.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        self.lbl_r2 = ctk.CTkLabel(res_frame, text=f"{self.t('fit')}: --", font=ctk.CTkFont(size=12), text_color="#3498db")
        self.lbl_r2.grid(row=2, column=0, padx=10, pady=(2, 5), sticky="w")
        self.lbl_compensacao = ctk.CTkLabel(
            res_frame,
            text=f"{self.t('deviations')}: --",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_compensacao.grid(row=2, column=1, padx=10, pady=(2, 5), sticky="w")
        self.lbl_status = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=11), text_color="#e74c3c")
        self.lbl_status.grid(row=6, column=0, padx=15, pady=(0, 10))

        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        self.fig, self.ax = plt.subplots(figsize=(6, 5), facecolor="#ffffff")
        self._format_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.print_button = ctk.CTkButton(
            self.canvas.get_tk_widget(),
            text=self.t("print_chart"),
            width=150,
            command=self.imprimir_grafico,
        )
        self.print_button.place(relx=1.0, x=-14, y=14, anchor="ne")

        referencia_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#1f344a")
        referencia_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        referencia_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            referencia_frame,
            text=self.t("system_references"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#b8dcff",
        ).grid(row=0, column=0, padx=14, pady=(8, 0), sticky="w")
        ctk.CTkLabel(
            referencia_frame,
            text=self.t("references_sae"),
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color="#f3f7fb",
        ).grid(row=1, column=0, padx=14, pady=(2, 0), sticky="w")
        ctk.CTkLabel(
            referencia_frame,
            text=self.t("normative_notice"),
            justify="left",
            font=ctk.CTkFont(size=10),
            text_color="#d7e4f2",
        ).grid(row=2, column=0, padx=14, pady=(2, 8), sticky="w")
        ctk.CTkButton(
            referencia_frame,
            text=self.t("technical_tables"),
            width=140,
            command=lambda: abrir_referencias_tecnicas(self),
        ).grid(row=1, column=1, rowspan=2, padx=14, pady=8, sticky="e")
        self._atualizar_textos_unidade()

    def _format_axes(self):
        self.fig.set_facecolor("#ffffff")
        self.ax.set_facecolor("#f8fafc")
        self.ax.tick_params(colors="#334155")
        self.ax.xaxis.label.set_color("#1e293b")
        self.ax.yaxis.label.set_color("#1e293b")
        self.ax.title.set_color("#0f172a")
        for spine in self.ax.spines.values():
            spine.set_color("#cbd5e1")
            
        # Ativa a grade principal e menor para cobrir todas as subdivisões das escalas
        self.ax.grid(True, which='both', linestyle="--", color="#cbd5e1", zorder=1)
        
        # Opcional: ativa divisões automáticas mais densas nas escalas
        from matplotlib.ticker import AutoMinorLocator
        self.ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        self.ax.yaxis.set_minor_locator(AutoMinorLocator(2))

        #self.ax.grid(True, linestyle="--", color="#cbd5e1", zorder=1)
        #self.ax.grid(True, linestyle="--", alpha=0.55, color="#cbd5e1")

    def _atualizar_textos_unidade(self):
        self.scroll_table.configure(
            label_text=(
                f"{self.t('exposure')} ({self.abreviacao_exposicao})  |  "
                f"{self.t('arc_height')} ({self.unidade_flecha})  |  {self.t('blade_deviation')}"
            )
        )
        for row in self.rows:
            row["tempo"].configure(placeholder_text=f"{self.t('exposure')} ({self.abreviacao_exposicao})")
            row["altura"].configure(placeholder_text=f"{self.t('arc_height')} ({self.unidade_flecha})")

    def _opcoes_lamina(self):
        return [self.t("no_deviation"), *self.desvios_laminas]

    def _atualizar_opcoes_lamina(self):
        opcoes = self._opcoes_lamina()
        for row in self.rows:
            escolha_atual = row["lamina_var"].get()
            row["menu_lamina"].configure(values=opcoes)
            if escolha_atual not in opcoes:
                row["lamina_var"].set(self.t("no_deviation"))

    def add_row(self, t_val="", h_val="", lamina_nome=None):
        row_idx = len(self.rows)
        entry_t = ctk.CTkEntry(self.scroll_table, placeholder_text=f"{self.t('exposure')} ({self.abreviacao_exposicao})", width=120)
        entry_t.grid(row=row_idx, column=0, padx=5, pady=4, sticky="ew")
        if t_val != "":
            entry_t.insert(0, str(t_val))
        entry_h = ctk.CTkEntry(self.scroll_table, placeholder_text=f"{self.t('arc_height')} ({self.unidade_flecha})", width=120)
        entry_h.grid(row=row_idx, column=1, padx=5, pady=4, sticky="ew")
        if h_val != "":
            entry_h.insert(0, str(h_val))
        lamina_var = ctk.StringVar(value=lamina_nome or self.t("no_deviation"))
        menu_lamina = ctk.CTkOptionMenu(
            self.scroll_table,
            variable=lamina_var,
            values=self._opcoes_lamina(),
            width=120,
        )
        menu_lamina.grid(row=row_idx, column=2, padx=5, pady=4, sticky="ew")
        self.rows.append(
            {"tempo": entry_t, "altura": entry_h, "lamina_var": lamina_var, "menu_lamina": menu_lamina}
        )

    def remove_row(self):
        if self.rows:
            row = self.rows.pop()
            row["tempo"].destroy()
            row["altura"].destroy()
            row["menu_lamina"].destroy()

    def _load_sample_data(self):
        while self.rows:
            self.remove_row()
        for tempo, altura in [(0.5, 0.11), (1.0, 0.17), (2.0, 0.22), (4.0, 0.24)]:
            self.add_row(tempo, altura)

    def _obter_dados_entradas(self):
        tempos, alturas, desvios = [], [], []
        for indice, row in enumerate(self.rows, start=1):
            entry_t, entry_h = row["tempo"], row["altura"]
            val_t, val_h = entry_t.get().strip(), entry_h.get().strip()
            if not val_t and not val_h:
                continue
            if not val_t or not val_h:
                raise ValueError(self.t("row_incomplete", index=indice))
            try:
                tempos.append(float(val_t.replace(",", ".")))
                alturas.append(float(val_h.replace(",", ".")))
                desvios.append(self.desvios_laminas.get(row["lamina_var"].get(), 0.0))
            except ValueError as err:
                raise ValueError(self.t("invalid_numbers", index=indice)) from err
        return np.array(tempos), np.array(alturas), np.array(desvios)

    def abrir_relatorio(self):
        """Abre a área de preenchimento e geração do relatório técnico."""
        abrir_relatorio(self)
        return

    def abrir_configuracoes(self):
        janela = ctk.CTkToplevel(self)
        janela.title(self.t("settings_title"))
        janela.geometry("1140x520")
        janela.minsize(1140, 520)
        janela.transient(self)
        janela.grab_set()
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_columnconfigure(1, weight=1)
        janela.grid_rowconfigure(1, weight=1)
        
        path_icon = resource_path("assets/icons/logo.ico")
        if os.path.exists(path_icon):
            janela.iconbitmap(path_icon)

        # Garantia para o Windows (caso o ícone demore a aparecer)
        janela.after(300, lambda: janela.iconbitmap(
            path_icon) if janela.winfo_exists() else None)

        ctk.CTkLabel(janela, text=self.t("settings"), font=ctk.CTkFont(size=19, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(24, 14), sticky="w"
        )
        unidade_var = ctk.StringVar(value=self._nome_unidade_flecha())
        lamina_var = ctk.StringVar(value=self._nome_tipo_lamina())
        exposicao_var = ctk.StringVar(value=self._nome_tipo_exposicao())
        idioma_var = ctk.StringVar(value=LANGUAGES[self.idioma])

        painel_esquerdo = ctk.CTkFrame(janela, corner_radius=10)
        painel_esquerdo.grid(row=1, column=0, padx=(24, 8), pady=(0, 16), sticky="nsew")
        painel_esquerdo.grid_columnconfigure(0, weight=1)
        painel_esquerdo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            painel_esquerdo,
            text=self.t("general_parameters"),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")
        self._adicionar_opcao_config(
            painel_esquerdo, 1, 0, self.t("language"), idioma_var, list(LANGUAGES.values())
        )
        self._adicionar_opcao_config(
            painel_esquerdo, 1, 1, self.t("arc_unit"), unidade_var, [self.t(chave) for chave in UNIDADES_FLECHA.values()]
        )
        self._adicionar_opcao_config(
            painel_esquerdo, 2, 0, self.t("almen_type"), lamina_var, [self.t(chave) for chave in TIPOS_LAMINA.values()]
        )
        self._adicionar_opcao_config(
            painel_esquerdo, 2, 1, self.t("exposure_unit"), exposicao_var, [self.t(item[1]) for item in UNIDADES_EXPOSICAO.values()]
        )

        normas_frame = ctk.CTkFrame(painel_esquerdo, fg_color="#1f344a", corner_radius=8)
        # Os controles ocupam duas linhas visuais cada (rótulo + seletor).
        # Manter as normas na linha 5 evita que o painel cubra a segunda
        # linha de opções e impede que uma área vazia separe os campos.
        normas_frame.grid(row=5, column=0, columnspan=2, padx=16, pady=(10, 16), sticky="ew")
        normas_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            normas_frame,
            text=self.t("registered_references"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            normas_frame,
            text=self.t("references_sae"),
            justify="left",
            wraplength=390,
            text_color="#ffffff",
        ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")
        ctk.CTkLabel(
            normas_frame,
            text=self.t("normative_notice"),
            justify="left",
            wraplength=390,
            text_color="#d9ebff",
        ).grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        painel_direito = ctk.CTkFrame(janela, corner_radius=10)
        painel_direito.grid(row=1, column=1, padx=(8, 24), pady=(0, 16), sticky="nsew")
        painel_direito.grid_columnconfigure(0, weight=1)
        painel_direito.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            painel_direito,
            text=self.t("individual_deviations", unit=self.unidade_flecha),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")
        ctk.CTkLabel(
            painel_direito,
            text=self.t("deviation_help"),
            justify="left",
            wraplength=400,
            text_color="#4a5568",
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        area_desvios = ctk.CTkScrollableFrame(painel_direito, height=150)
        area_desvios._scrollbar.grid_forget()
        area_desvios.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="nsew")
        area_desvios.grid_columnconfigure(1, weight=1)
        area_desvios.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(area_desvios, text="#", text_color="#a0a0a0").grid(row=0, column=0, padx=(8, 4), pady=(5, 2))
        ctk.CTkLabel(area_desvios, text=self.t("blade_id"), text_color="#a0a0a0").grid(
            row=0, column=1, padx=4, pady=(5, 2), sticky="w"
        )
        ctk.CTkLabel(area_desvios, text=self.t("deviation"), text_color="#a0a0a0").grid(
            row=0, column=2, padx=4, pady=(5, 2), sticky="w"
        )

        linhas_desvio = []

        def reordenar_linhas_desvio():
            for indice, linha in enumerate(linhas_desvio, start=1):
                for widget in linha["widgets"]:
                    widget.grid_configure(row=indice)
                linha["indice"].configure(text=str(indice))

        def remover_linha_desvio(linha):
            for widget in linha["widgets"]:
                widget.destroy()
            linhas_desvio.remove(linha)
            reordenar_linhas_desvio()

        def adicionar_linha_desvio(nome="", valor="0"):
            indice = len(linhas_desvio) + 1
            indice_widget = ctk.CTkLabel(area_desvios, text=str(indice), width=22)
            nome_var = ctk.StringVar(value=nome or f"{self.t('blade')} {indice}")
            valor_var = ctk.StringVar(value=str(valor))
            nome_entry = ctk.CTkEntry(area_desvios, textvariable=nome_var, placeholder_text=f"{self.t('blade')} {indice}")
            valor_entry = ctk.CTkEntry(area_desvios, textvariable=valor_var, placeholder_text=self.t("deviation_placeholder"))
            linha = {
                "indice": indice_widget,
                "nome": nome_var,
                "valor": valor_var,
                "widgets": [indice_widget, nome_entry, valor_entry],
            }
            remover_button = ctk.CTkButton(
                area_desvios,
                text=self.t("remove"),
                width=76,
                fg_color="#c0392b",
                hover_color="#e74c3c",
                command=lambda linha_atual=linha: remover_linha_desvio(linha_atual),
            )
            linha["widgets"].append(remover_button)
            indice_widget.grid(row=indice, column=0, padx=(8, 4), pady=3)
            nome_entry.grid(row=indice, column=1, padx=4, pady=3, sticky="ew")
            valor_entry.grid(row=indice, column=2, padx=4, pady=3, sticky="ew")
            remover_button.grid(row=indice, column=3, padx=(4, 8), pady=3)
            linhas_desvio.append(linha)

        for nome, valor in self.desvios_laminas.items():
            adicionar_linha_desvio(nome, f"{valor:.6g}")

        ctk.CTkButton(
            painel_direito,
            text=self.t("add_blade"),
            command=adicionar_linha_desvio,
        ).grid(row=3, column=0, padx=16, pady=(0, 16), sticky="w")

        def aplicar():
            novos_desvios = {}
            for indice, linha in enumerate(linhas_desvio, start=1):
                nome = linha["nome"].get().strip()
                if not nome:
                    self.lbl_status.configure(text=self.t("blade_required", index=indice))
                    return
                if nome.casefold() == self.t("no_deviation").casefold() or nome.casefold() in {item.casefold() for item in novos_desvios}:
                    self.lbl_status.configure(text=self.t("unique_blades"))
                    return
                try:
                    desvio = float(linha["valor"].get().strip().replace(",", "."))
                except ValueError:
                    self.lbl_status.configure(text=self.t("invalid_deviation", index=indice))
                    return
                if not np.isfinite(desvio):
                    self.lbl_status.configure(text=self.t("finite_deviations"))
                    return
                novos_desvios[nome] = desvio

            nova_unidade = self._codigo_por_nome(UNIDADES_FLECHA, unidade_var.get())
            self.desvios_laminas = {
                nome: converter_flecha(desvio, self.unidade_flecha, nova_unidade)
                for nome, desvio in novos_desvios.items()
            }
            self._converter_entradas_flecha(nova_unidade)
            self.tipo_lamina = self._codigo_por_nome(TIPOS_LAMINA, lamina_var.get())
            self.tipo_exposicao = self._codigo_por_nome(UNIDADES_EXPOSICAO, exposicao_var.get())
            novo_idioma = next(codigo for codigo, nome in LANGUAGES.items() if nome == idioma_var.get())
            idioma_alterado = novo_idioma != self.idioma
            self.idioma = novo_idioma
            save_language(novo_idioma)
            self._atualizar_textos_unidade()
            self._atualizar_opcoes_lamina()
            janela.destroy()
            if idioma_alterado:
                self._recriar_interface()
            else:
                self.calcular_e_plotar()

        ctk.CTkButton(janela, text=self.t("apply_settings"), width=190, command=aplicar).grid(
            row=2, column=0, columnspan=2, padx=24, pady=(0, 24), sticky="e"
        )

    @staticmethod
    def _adicionar_opcao_config(janela, linha, coluna, texto, variavel, valores):
        ctk.CTkLabel(janela, text=texto).grid(
            row=linha * 2 - 1, column=coluna, padx=16, pady=(6, 2), sticky="w"
        )
        ctk.CTkOptionMenu(janela, variable=variavel, values=valores, width=210).grid(
            row=linha * 2, column=coluna, padx=16, pady=(0, 5), sticky="w"
        )

    def _converter_entradas_flecha(self, nova_unidade):
        if nova_unidade == self.unidade_flecha:
            return
        for row in self.rows:
            entry_h = row["altura"]
            texto = entry_h.get().strip()
            if not texto:
                continue
            try:
                convertido = converter_flecha(texto.replace(",", "."), self.unidade_flecha, nova_unidade)
            except ValueError:
                continue
            entry_h.delete(0, "end")
            entry_h.insert(0, f"{convertido:.6g}")
        self.unidade_flecha = nova_unidade

    def calcular_e_plotar(self):
        self.lbl_status.configure(text="")
        self._ultimo_resultado = None
        try:
            t_data, h_data, desvios = self._obter_dados_entradas()
            resultado = calcular_saturacao(t_data, h_data, desvios)
            self._ultimo_resultado = resultado
            A, b = resultado["A"], resultado["b"]
            t_sat, h_sat = resultado["t_sat"], resultado["h_sat"]
            t_2sat, h_2sat, r2 = resultado["t_2sat"], resultado["h_2sat"], resultado["r2"]
            h_data_compensada = resultado["h_data_compensada"]

            self.lbl_tsat.configure(text=f"{self.t('saturation_time')}: {t_sat:.2f} {self.abreviacao_exposicao}")
            self.lbl_hsat.configure(text=f"{self.t('intensity')}: {h_sat:.4f} {self.unidade_flecha} {self.tipo_lamina}")
            self.lbl_t2sat.configure(text=f"{self.t('point_2t')}: {t_2sat:.2f} {self.abreviacao_exposicao}")
            self.lbl_h2sat.configure(text=f"{self.t('height_2t')}: {h_2sat:.4f} {self.unidade_flecha}")
            self.lbl_r2.configure(text=f"{self.t('fit')}: {r2:.4f}")
            desvios_aplicados = desvios[np.abs(desvios) > np.finfo(float).eps]
            if len(desvios_aplicados):
                self.lbl_compensacao.configure(
                    text=(
                        f"{self.t('deviations')}: {len(desvios_aplicados)}/{len(desvios)} "
                        f"({np.min(desvios_aplicados):+.4f} a {np.max(desvios_aplicados):+.4f} "
                        f"{self.unidade_flecha})"
                    )
                )
            else:
                self.lbl_compensacao.configure(text=f"{self.t('deviations')}: {self.t('none_applied')}")

            self.ax.clear()
            self._format_axes()
            t_max_plot = max(float(np.max(t_data)) * 1.15, t_2sat * 1.05)
            t_smooth = np.linspace(0, t_max_plot, 300)
            h_smooth = almen_model(t_smooth, A, b)
            self.ax.scatter(
                t_data,
                h_data_compensada,
                color="#e74c3c",
                s=50,
                zorder=5,
                label=self.t("measured_points"),
            )
            self.ax.plot(t_smooth, h_smooth, color="#3498db", linewidth=2, label=self.t("fitted_curve", r2=r2))
            self.ax.plot(t_sat, h_sat, "go", markersize=8, label=self.t("saturation_point", value=t_sat, unit=self.abreviacao_exposicao))
            self.ax.vlines(t_sat, 0, h_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)
            self.ax.hlines(h_sat, 0, t_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)
            self.ax.plot(
                t_2sat,
                h_2sat,
                "mo",
                markersize=6,
                label=self.t("point_2t_legend", value=t_2sat, unit=self.abreviacao_exposicao),
            )
            self.ax.vlines(t_2sat, 0, h_2sat, colors="#e056fd", linestyles="dotted", alpha=0.7)
            self.ax.set_title(self.t("chart_title"), fontsize=12, pad=10)
            self.ax.set_xlabel(f"{self.t('exposure')} ({self.abreviacao_exposicao})")
            self.ax.set_ylabel(f"{self.t('arc_height')} ({self.unidade_flecha})")
            self.ax.set_xlim(0, max(t_smooth))
            self.ax.set_ylim(0, max(h_smooth) * 1.15)
            self.ax.legend(
                loc="lower right",
                facecolor="#ffffff",
                edgecolor="#cbd5e1",
                labelcolor="#1e293b",
                fontsize=8,
            )
            self.canvas.draw()
        except Exception as err:
            self.lbl_status.configure(text=self.t("error", message=err))

    def imprimir_grafico(self):
        """Gera uma imagem temporária do gráfico e aciona a impressão do Windows."""
        if os.name != "nt":
            self.lbl_status.configure(text=self.t("print_windows_only"))
            return

        try:
            caminho = Path(tempfile.gettempdir()) / "curva_saturacao_almen.png"
            self.fig.savefig(caminho, dpi=300, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
            self._arquivo_impressao = caminho
            os.startfile(str(caminho), "print")
            self.lbl_status.configure(text=self.t("chart_sent_to_printer"), text_color="#2ecc71")
        except OSError as err:
            self.lbl_status.configure(text=self.t("print_error", message=err))


# ==============================================================================
# 4. INICIALIZAÇÃO DO APP
# ==============================================================================
if __name__ == "__main__":
    
    # Destrói o splash screen assim que a janela principal estiver pronta
    if splash is not None:
        splash.destroy()

    app = AlmenApp()   
    app.mainloop()
