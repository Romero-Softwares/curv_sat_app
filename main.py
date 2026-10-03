import customtkinter as ctk
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from technical_references import abrir_referencias_tecnicas


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

MM_POR_POLEGADA = 25.4
UNIDADES_FLECHA = {"mm": "Milímetros (mm)", "in": "Polegadas (in)"}
UNIDADES_EXPOSICAO = {
    "Segundos": "s",
    "Passes": "pass",
    "Rotações": "rot",
    "Ciclos": "ciclos",
    "Inverso do avanço": "inv. avanço",
}
REFERENCIAS_SAE = (
    "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\n"
    "SAE J2597_201709 — Computer Generated Shot Peening Saturation Curves"
)
AVISO_NORMATIVO = "Referências SAE registradas; a conformidade exige validação do processo e dos dados do ensaio."


def almen_model(t, A, b):
    """Modelo exponencial de saturação usado para o ajuste SAE J2597."""
    return A * (1.0 - np.exp(-b * t))


def converter_flecha(valor, unidade_origem, unidade_destino):
    """Converte a altura de arco entre milímetros e polegadas."""
    if unidade_origem not in UNIDADES_FLECHA or unidade_destino not in UNIDADES_FLECHA:
        raise ValueError("Unidade de flecha inválida.")
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
        raise ValueError("O desvio da lâmina deve ser um número finito.")
    try:
        desvios_lamina = np.broadcast_to(desvios_lamina, alturas.shape)
    except ValueError as err:
        raise ValueError("Informe um desvio para cada flecha medida.") from err
    alturas_compensadas = alturas - desvios_lamina
    if np.any(alturas_compensadas < 0):
        raise ValueError("O desvio informado torna alguma flecha compensada negativa.")
    return alturas_compensadas


def calcular_saturacao(t_data, h_data, desvio_lamina=0.0):
    """Ajusta a curva compensada e determina T e 2T pela regra dos 10%."""
    t_data = np.asarray(t_data, dtype=float)
    h_data = np.asarray(h_data, dtype=float)

    if t_data.ndim != 1 or h_data.ndim != 1 or len(t_data) != len(h_data):
        raise ValueError("Tempo e altura devem ser vetores do mesmo tamanho.")
    if not np.isfinite(t_data).all() or not np.isfinite(h_data).all():
        raise ValueError("Tempo e altura devem conter apenas números finitos.")
    if np.any(t_data < 0):
        raise ValueError("Os tempos de exposição não podem ser negativos.")
    if np.any(h_data < 0):
        raise ValueError("As alturas de arco não podem ser negativas.")
    h_data_compensada = compensar_desvio_lamina(h_data, desvio_lamina)
    if len(t_data) < 4:
        raise ValueError("A curva exige pelo menos 4 medições válidas.")
    if np.count_nonzero(h_data_compensada) < 4:
        raise ValueError("A curva exige pelo menos 4 alturas de arco não nulas.")
    if len(np.unique(t_data)) < 2:
        raise ValueError("Informe pelo menos dois valores de exposição distintos.")
    if np.ptp(h_data_compensada) == 0:
        raise ValueError("As alturas precisam variar para calcular a saturação.")

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
        raise ValueError("Não foi possível determinar uma taxa de saturação positiva.")

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


class AlmenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Calculador de Curva de Saturação Almen")
        self.geometry("1120x700")
        self.minsize(950, 600)

        self.rows = []
        self.unidade_flecha = "mm"
        self.tipo_lamina = "A - padrão"
        self.tipo_exposicao = "Segundos"
        self.desvios_laminas = {"Lâmina 1": 0.0}

        self._build_ui()
        self._load_sample_data()
        self.calcular_e_plotar()

    @property
    def abreviacao_exposicao(self):
        return UNIDADES_EXPOSICAO[self.tipo_exposicao]

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
            text="Medições da Lâmina Almen",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text="+ Linha", width=76, command=self.add_row).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame,
            text="- Linha",
            width=76,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self.remove_row,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame,
            text="Exemplo",
            width=76,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._load_sample_data,
        ).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Configurações", width=112, command=self.abrir_configuracoes).pack(
            side="right", padx=2
        )

        self.scroll_table = ctk.CTkScrollableFrame(left_frame, label_text="")
        self.scroll_table.grid(row=2, column=0, padx=15, pady=5, sticky="nsew")
        self.scroll_table.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            left_frame,
            text="Calcular e Gerar Gráfico",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self.calcular_e_plotar,
        ).grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        res_frame = ctk.CTkFrame(left_frame, fg_color="#1e1e1e", corner_radius=8)
        res_frame.grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")
        res_frame.grid_columnconfigure((0, 1), weight=1)
        self.lbl_tsat = ctk.CTkLabel(res_frame, text="Tempo Sat. (T): --", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_tsat.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")
        self.lbl_hsat = ctk.CTkLabel(
            res_frame, text="Intensidade H(T): --", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2ecc71"
        )
        self.lbl_hsat.grid(row=0, column=1, padx=10, pady=(5, 2), sticky="w")
        self.lbl_t2sat = ctk.CTkLabel(res_frame, text="Ponto (2T): --", font=ctk.CTkFont(size=12))
        self.lbl_t2sat.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        self.lbl_h2sat = ctk.CTkLabel(res_frame, text="Altura H(2T): --", font=ctk.CTkFont(size=12))
        self.lbl_h2sat.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        self.lbl_r2 = ctk.CTkLabel(res_frame, text="Ajuste R²: --", font=ctk.CTkFont(size=12), text_color="#3498db")
        self.lbl_r2.grid(row=2, column=0, padx=10, pady=(2, 5), sticky="w")
        self.lbl_compensacao = ctk.CTkLabel(
            res_frame,
            text="Desvios: --",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_compensacao.grid(row=2, column=1, padx=10, pady=(2, 5), sticky="w")
        self.lbl_status = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=11), text_color="#e74c3c")
        self.lbl_status.grid(row=5, column=0, padx=15, pady=(0, 10))

        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        self.fig, self.ax = plt.subplots(figsize=(6, 5), facecolor="#2b2b2b")
        self._format_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        referencia_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#1f344a")
        referencia_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        referencia_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            referencia_frame,
            text="REFERÊNCIAS NORMATIVAS DO SISTEMA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#b8dcff",
        ).grid(row=0, column=0, padx=14, pady=(8, 0), sticky="w")
        ctk.CTkLabel(
            referencia_frame,
            text=REFERENCIAS_SAE,
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color="#f3f7fb",
        ).grid(row=1, column=0, padx=14, pady=(2, 0), sticky="w")
        ctk.CTkLabel(
            referencia_frame,
            text=AVISO_NORMATIVO,
            justify="left",
            font=ctk.CTkFont(size=10),
            text_color="#d7e4f2",
        ).grid(row=2, column=0, padx=14, pady=(2, 8), sticky="w")
        ctk.CTkButton(
            referencia_frame,
            text="Tabelas técnicas",
            width=140,
            command=lambda: abrir_referencias_tecnicas(self),
        ).grid(row=1, column=1, rowspan=2, padx=14, pady=8, sticky="e")
        self._atualizar_textos_unidade()

    def _format_axes(self):
        self.ax.set_facecolor("#1e1e1e")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("#555555")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="gray")

    def _atualizar_textos_unidade(self):
        self.scroll_table.configure(
            label_text=(
                f"Exposição ({self.abreviacao_exposicao})  |  "
                f"Altura da flecha ({self.unidade_flecha})  |  Lâmina / desvio"
            )
        )
        for row in self.rows:
            row["tempo"].configure(placeholder_text=f"Exposição ({self.abreviacao_exposicao})")
            row["altura"].configure(placeholder_text=f"Flecha ({self.unidade_flecha})")

    def _opcoes_lamina(self):
        return ["Sem desvio", *self.desvios_laminas]

    def _atualizar_opcoes_lamina(self):
        opcoes = self._opcoes_lamina()
        for row in self.rows:
            escolha_atual = row["lamina_var"].get()
            row["menu_lamina"].configure(values=opcoes)
            if escolha_atual not in opcoes:
                row["lamina_var"].set("Sem desvio")

    def add_row(self, t_val="", h_val="", lamina_nome=None):
        row_idx = len(self.rows)
        entry_t = ctk.CTkEntry(self.scroll_table, placeholder_text=f"Exposição ({self.abreviacao_exposicao})", width=120)
        entry_t.grid(row=row_idx, column=0, padx=5, pady=4, sticky="ew")
        if t_val != "":
            entry_t.insert(0, str(t_val))
        entry_h = ctk.CTkEntry(self.scroll_table, placeholder_text=f"Flecha ({self.unidade_flecha})", width=120)
        entry_h.grid(row=row_idx, column=1, padx=5, pady=4, sticky="ew")
        if h_val != "":
            entry_h.insert(0, str(h_val))
        lamina_var = ctk.StringVar(value=lamina_nome or "Sem desvio")
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
        for tempo, altura in [(0.5, 0.11), (1.0, 0.17), (2.0, 0.22), (4.0, 0.24), (8.0, 0.245)]:
            self.add_row(tempo, altura)

    def _obter_dados_entradas(self):
        tempos, alturas, desvios = [], [], []
        for indice, row in enumerate(self.rows, start=1):
            entry_t, entry_h = row["tempo"], row["altura"]
            val_t, val_h = entry_t.get().strip(), entry_h.get().strip()
            if not val_t and not val_h:
                continue
            if not val_t or not val_h:
                raise ValueError(f"Preencha exposição e flecha na linha {indice}.")
            try:
                tempos.append(float(val_t.replace(",", ".")))
                alturas.append(float(val_h.replace(",", ".")))
                desvios.append(self.desvios_laminas.get(row["lamina_var"].get(), 0.0))
            except ValueError as err:
                raise ValueError(f"Use números válidos na linha {indice}.") from err
        return np.array(tempos), np.array(alturas), np.array(desvios)

    def abrir_configuracoes(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Configurações da curva")
        janela.geometry("980x650")
        janela.minsize(850, 540)
        janela.transient(self)
        janela.grab_set()
        janela.grid_columnconfigure(0, weight=1)
        janela.grid_columnconfigure(1, weight=1)
        janela.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(janela, text="Configurações", font=ctk.CTkFont(size=19, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(24, 14), sticky="w"
        )
        unidade_var = ctk.StringVar(value=UNIDADES_FLECHA[self.unidade_flecha])
        lamina_var = ctk.StringVar(value=self.tipo_lamina)
        exposicao_var = ctk.StringVar(value=self.tipo_exposicao)

        painel_esquerdo = ctk.CTkFrame(janela, corner_radius=10)
        painel_esquerdo.grid(row=1, column=0, padx=(24, 8), pady=(0, 16), sticky="nsew")
        painel_esquerdo.grid_columnconfigure(0, weight=1)
        painel_esquerdo.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            painel_esquerdo,
            text="Parâmetros gerais",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")
        self._adicionar_opcao_config(
            painel_esquerdo, 1, "Unidade da altura da flecha", unidade_var, list(UNIDADES_FLECHA.values())
        )
        self._adicionar_opcao_config(
            painel_esquerdo, 2, "Tipo da lâmina Almen", lamina_var, ["N - fina", "A - padrão", "C - espessa"]
        )
        self._adicionar_opcao_config(
            painel_esquerdo, 3, "Unidade de exposição", exposicao_var, list(UNIDADES_EXPOSICAO)
        )

        normas_frame = ctk.CTkFrame(painel_esquerdo, fg_color="#1f344a", corner_radius=8)
        normas_frame.grid(row=7, column=0, padx=16, pady=(14, 16), sticky="nsew")
        normas_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            normas_frame,
            text="Referências normativas registradas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkLabel(
            normas_frame,
            text=REFERENCIAS_SAE,
            justify="left",
            wraplength=390,
            text_color="#ffffff",
        ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")
        ctk.CTkLabel(
            normas_frame,
            text=AVISO_NORMATIVO,
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
            text=f"Desvios individuais por lâmina ({self.unidade_flecha})",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")
        ctk.CTkLabel(
            painel_direito,
            text=(
                "Cadastre uma linha para cada lâmina que possua desvio próprio. "
                "Informe o desvio como medição indicada − valor real; ele será subtraído "
                "somente da flecha associada àquela lâmina."
            ),
            justify="left",
            wraplength=400,
            text_color="#4a5568",
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        area_desvios = ctk.CTkScrollableFrame(painel_direito, height=180)
        area_desvios.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="nsew")
        area_desvios.grid_columnconfigure(1, weight=1)
        area_desvios.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(area_desvios, text="#", text_color="#a0a0a0").grid(row=0, column=0, padx=(8, 4), pady=(5, 2))
        ctk.CTkLabel(area_desvios, text="Identificação da lâmina", text_color="#a0a0a0").grid(
            row=0, column=1, padx=4, pady=(5, 2), sticky="w"
        )
        ctk.CTkLabel(area_desvios, text="Desvio", text_color="#a0a0a0").grid(
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
            nome_var = ctk.StringVar(value=nome or f"Lâmina {indice}")
            valor_var = ctk.StringVar(value=str(valor))
            nome_entry = ctk.CTkEntry(area_desvios, textvariable=nome_var, placeholder_text=f"Lâmina {indice}")
            valor_entry = ctk.CTkEntry(area_desvios, textvariable=valor_var, placeholder_text="Ex.: 0,005")
            linha = {
                "indice": indice_widget,
                "nome": nome_var,
                "valor": valor_var,
                "widgets": [indice_widget, nome_entry, valor_entry],
            }
            remover_button = ctk.CTkButton(
                area_desvios,
                text="Remover",
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
            text="+ Adicionar lâmina / desvio",
            command=adicionar_linha_desvio,
        ).grid(row=3, column=0, padx=16, pady=(0, 16), sticky="w")

        def aplicar():
            novos_desvios = {}
            for indice, linha in enumerate(linhas_desvio, start=1):
                nome = linha["nome"].get().strip()
                if not nome:
                    self.lbl_status.configure(text=f"Erro: informe a identificação da lâmina {indice}.")
                    return
                if nome.casefold() == "sem desvio" or nome.casefold() in {item.casefold() for item in novos_desvios}:
                    self.lbl_status.configure(text="Erro: use identificações únicas e diferentes de 'Sem desvio'.")
                    return
                try:
                    desvio = float(linha["valor"].get().strip().replace(",", "."))
                except ValueError:
                    self.lbl_status.configure(text=f"Erro: informe um desvio numérico válido na lâmina {indice}.")
                    return
                if not np.isfinite(desvio):
                    self.lbl_status.configure(text="Erro: os desvios das lâminas devem ser finitos.")
                    return
                novos_desvios[nome] = desvio

            nova_unidade = next(codigo for codigo, nome in UNIDADES_FLECHA.items() if nome == unidade_var.get())
            self.desvios_laminas = {
                nome: converter_flecha(desvio, self.unidade_flecha, nova_unidade)
                for nome, desvio in novos_desvios.items()
            }
            self._converter_entradas_flecha(nova_unidade)
            self.tipo_lamina = lamina_var.get()
            self.tipo_exposicao = exposicao_var.get()
            self._atualizar_textos_unidade()
            self._atualizar_opcoes_lamina()
            janela.destroy()
            self.calcular_e_plotar()

        ctk.CTkButton(janela, text="Aplicar configurações", command=aplicar).grid(
            row=2, column=0, columnspan=2, padx=24, pady=(0, 24), sticky="ew"
        )

    @staticmethod
    def _adicionar_opcao_config(janela, linha, texto, variavel, valores):
        ctk.CTkLabel(janela, text=texto).grid(row=linha * 2 - 1, column=0, padx=24, pady=(6, 2), sticky="w")
        ctk.CTkOptionMenu(janela, variable=variavel, values=valores).grid(row=linha * 2, column=0, padx=24, pady=(0, 5), sticky="ew")

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
        try:
            t_data, h_data, desvios = self._obter_dados_entradas()
            resultado = calcular_saturacao(t_data, h_data, desvios)
            A, b = resultado["A"], resultado["b"]
            t_sat, h_sat = resultado["t_sat"], resultado["h_sat"]
            t_2sat, h_2sat, r2 = resultado["t_2sat"], resultado["h_2sat"], resultado["r2"]
            h_data_compensada = resultado["h_data_compensada"]

            self.lbl_tsat.configure(text=f"Tempo Sat. (T): {t_sat:.2f} {self.abreviacao_exposicao}")
            self.lbl_hsat.configure(text=f"Intensidade H(T): {h_sat:.4f} {self.unidade_flecha} {self.tipo_lamina[0]}")
            self.lbl_t2sat.configure(text=f"Ponto (2T): {t_2sat:.2f} {self.abreviacao_exposicao}")
            self.lbl_h2sat.configure(text=f"Altura H(2T): {h_2sat:.4f} {self.unidade_flecha}")
            self.lbl_r2.configure(text=f"Ajuste R²: {r2:.4f}")
            desvios_aplicados = desvios[np.abs(desvios) > np.finfo(float).eps]
            if len(desvios_aplicados):
                self.lbl_compensacao.configure(
                    text=(
                        f"Desvios: {len(desvios_aplicados)}/{len(desvios)} "
                        f"({np.min(desvios_aplicados):+.4f} a {np.max(desvios_aplicados):+.4f} "
                        f"{self.unidade_flecha})"
                    )
                )
            else:
                self.lbl_compensacao.configure(text="Desvios: nenhum aplicado")

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
                label="Pontos medidos compensados",
            )
            self.ax.plot(t_smooth, h_smooth, color="#3498db", linewidth=2, label=f"Curva ajustada ($R^2={r2:.3f}$)")
            self.ax.plot(t_sat, h_sat, "go", markersize=8, label=f"Saturação T ({t_sat:.2f} {self.abreviacao_exposicao})")
            self.ax.vlines(t_sat, 0, h_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)
            self.ax.hlines(h_sat, 0, t_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)
            self.ax.plot(t_2sat, h_2sat, "mo", markersize=6, label=f"Ponto 2T ({t_2sat:.2f} {self.abreviacao_exposicao})")
            self.ax.vlines(t_2sat, 0, h_2sat, colors="#e056fd", linestyles="dotted", alpha=0.7)
            self.ax.set_title("Curva de Saturação Almen", fontsize=12, pad=10)
            self.ax.set_xlabel(f"Exposição ({self.abreviacao_exposicao})")
            self.ax.set_ylabel(f"Altura de arco / flecha ({self.unidade_flecha})")
            self.ax.set_xlim(0, max(t_smooth))
            self.ax.set_ylim(0, max(h_smooth) * 1.15)
            self.ax.legend(loc="lower right", facecolor="#2b2b2b", edgecolor="none", labelcolor="white", fontsize=8)
            self.canvas.draw()
        except Exception as err:
            self.lbl_status.configure(text=f"Erro: {err}")


if __name__ == "__main__":
    app = AlmenApp()
    app.mainloop()
