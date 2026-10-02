import customtkinter as ctk
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuração visual do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# Modelo exponencial SAE J2597
def almen_model(t, A, b):
    return A * (1.0 - np.exp(-b * t))


class AlmenApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Calculador de Curva de Saturação Almen - SAE J2597 / J443")
        self.geometry("1100x680")
        self.minsize(950, 600)

        self.rows = []  # Armazena tuplas (CTkEntry tempo, CTkEntry altura)

        self._build_ui()
        self._load_sample_data()
        self.calcular_e_plotar()

    def _build_ui(self):
        # Grid principal: esquerda (controles/tabela) | direita (gráfico)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------
        # PAINEL ESQUERDO: ENTRADA DE DADOS & RESULTADOS
        # ---------------------------------------------------------
        left_frame = ctk.CTkFrame(self, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            left_frame,
            text="Medições da Tira Almen",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        ctk.CTkButton(btn_frame, text="+ Linha", width=80, command=self.add_row).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="- Linha", width=80, fg_color="#c0392b", hover_color="#e74c3c", command=self.remove_row).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Exemplo", width=80, fg_color="#7f8c8d", hover_color="#95a5a6", command=self._load_sample_data).pack(side="left", padx=2)

        # Área de scroll para tabela de dados
        self.scroll_table = ctk.CTkScrollableFrame(left_frame, label_text="Tempo (s)  |  Altura Arco (mm)")
        self.scroll_table.grid(row=2, column=0, padx=15, pady=5, sticky="nsew")
        self.scroll_table.grid_columnconfigure((0, 1), weight=1)

        btn_calc = ctk.CTkButton(
            left_frame,
            text="Calcular e Gerar Gráfico",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            command=self.calcular_e_plotar,
        )
        btn_calc.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        # Painel de card de resultados
        res_frame = ctk.CTkFrame(left_frame, fg_color="#1e1e1e", corner_radius=8)
        res_frame.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        res_frame.grid_columnconfigure((0, 1), weight=1)

        self.lbl_tsat = ctk.CTkLabel(res_frame, text="Tempo Sat. (T): --", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_tsat.grid(row=0, column=0, padx=10, pady=6, sticky="w")

        self.lbl_hsat = ctk.CTkLabel(res_frame, text="Intensidade H(T): --", font=ctk.CTkFont(size=13, weight="bold", color="#2ecc71"))
        self.lbl_hsat.grid(row=0, column=1, padx=10, pady=6, sticky="w")

        self.lbl_t2sat = ctk.CTkLabel(res_frame, text="Ponto (2T): --", font=ctk.CTkFont(size=12))
        self.lbl_t2sat.grid(row=1, column=0, padx=10, pady=4, sticky="w")

        self.lbl_h2sat = ctk.CTkLabel(res_frame, text="Altura H(2T): --", font=ctk.CTkFont(size=12))
        self.lbl_h2sat.grid(row=1, column=1, padx=10, pady=4, sticky="w")

        self.lbl_r2 = ctk.CTkLabel(res_frame, text="Ajuste R²: --", font=ctk.CTkFont(size=12, color="#3498db"))
        self.lbl_r2.grid(row=2, column=0, columnspan=2, padx=10, pady=(4, 8), sticky="w")

        self.lbl_status = ctk.CTkLabel(left_frame, text="", font=ctk.CTkFont(size=11), text_color="#e74c3c")
        self.lbl_status.grid(row=5, column=0, padx=15, pady=(0, 5))

        # ---------------------------------------------------------
        # PAINEL DIREITO: INTEGRAÇÃO MATPLOTLIB
        # ---------------------------------------------------------
        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Matplotlib figura dark
        self.fig, self.ax = plt.subplots(figsize=(6, 5), facecolor="#2b2b2b")
        self._format_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _format_axes(self):
        self.ax.set_facecolor("#1e1e1e")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("#555555")
        self.ax.grid(True, linestyle="--", alpha=0.3, color="gray")

    def add_row(self, t_val="", h_val=""):
        row_idx = len(self.rows)

        entry_t = ctk.CTkEntry(self.scroll_table, placeholder_text="Tempo (s)", width=120)
        entry_t.grid(row=row_idx, column=0, padx=5, pady=4, sticky="ew")
        if t_val != "":
            entry_t.insert(0, str(t_val))

        entry_h = ctk.CTkEntry(self.scroll_table, placeholder_text="Altura (mm)", width=120)
        entry_h.grid(row=row_idx, column=1, padx=5, pady=4, sticky="ew")
        if h_val != "":
            entry_h.insert(0, str(h_val))

        self.rows.append((entry_t, entry_h))

    def remove_row(self):
        if len(self.rows) > 0:
            entry_t, entry_h = self.rows.pop()
            entry_t.destroy()
            entry_h.destroy()

    def _load_sample_data(self):
        while len(self.rows) > 0:
            self.remove_row()

        amostras = [(0.5, 0.11), (1.0, 0.17), (2.0, 0.22), (4.0, 0.24), (8.0, 0.245)]
        for t, h in amostras:
            self.add_row(t, h)

    def _obter_dados_entradas(self):
        t_list, h_list = [], []
        for entry_t, entry_h in self.rows:
            val_t = entry_t.get().strip()
            val_h = entry_h.get().strip()
            if val_t and val_h:
                t_list.append(float(val_t.replace(",", ".")))
                h_list.append(float(val_h.replace(",", ".")))

        if len(t_list) < 3:
            raise ValueError("Insira pelo menos 3 pontos válidos para ajustar a curva.")

        return np.array(t_list), np.array(h_list)

    def calcular_e_plotar(self):
        self.lbl_status.configure(text="")
        try:
            t_data, h_data = self._obter_dados_entradas()

            # Regressão não linear SAE J2597
            popt, _ = curve_fit(almen_model, t_data, h_data, p0=[max(h_data), 0.1], bounds=(0, np.inf))
            A, b = popt

            # Cálculo de saturação (regra dos 10%)
            T_sat = np.log(10) / b
            H_sat = almen_model(T_sat, A, b)
            T_2sat = 2 * T_sat
            H_2sat = almen_model(T_2sat, A, b)

            # R²
            res = h_data - almen_model(t_data, A, b)
            r2 = 1 - (np.sum(res**2) / np.sum((h_data - np.mean(h_data)) ** 2))

            # Atualização dos cards de resultados
            self.lbl_tsat.configure(text=f"Tempo Sat. (T): {T_sat:.2f} s")
            self.lbl_hsat.configure(text=f"Intensidade H(T): {H_sat:.4f} mm")
            self.lbl_t2sat.configure(text=f"Ponto (2T): {T_2sat:.2f} s")
            self.lbl_h2sat.configure(text=f"Altura H(2T): {H_2sat:.4f} mm")
            self.lbl_r2.configure(text=f"Qualidade Ajuste (R²): {r2:.4f}")

            # Plotagem do gráfico
            self.ax.clear()
            self._format_axes()

            t_smooth = np.linspace(0, max(t_data) * 1.15, 300)
            h_smooth = almen_model(t_smooth, A, b)

            self.ax.scatter(t_data, h_data, color="#e74c3c", s=50, zorder=5, label="Pontos Medidos")
            self.ax.plot(t_smooth, h_smooth, color="#3498db", linewidth=2, label=f"Curva SAE J2597 ($R^2={r2:.3f}$)")

            # Ponto T
            self.ax.plot(T_sat, H_sat, "go", markersize=8, label=f"Saturação T ({T_sat:.2f}s, {H_sat:.3f}mm)")
            self.ax.vlines(T_sat, 0, H_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)
            self.ax.hlines(H_sat, 0, T_sat, colors="#2ecc71", linestyles="dashed", alpha=0.7)

            # Ponto 2T
            self.ax.plot(T_2sat, H_2sat, "mo", markersize=6, label=f"Ponto 2T ({T_2sat:.2f}s, {H_2sat:.3f}mm)")
            self.ax.vlines(T_2sat, 0, H_2sat, colors="#e056fd", linestyles="dotted", alpha=0.7)

            self.ax.set_title("Curva de Saturação Almen", fontsize=12, pad=10)
            self.ax.set_xlabel("Tempo de Exposição (s)")
            self.ax.set_ylabel("Altura de Arco / Flecha (mm)")
            self.ax.set_xlim(0, max(t_smooth))
            self.ax.set_ylim(0, max(h_smooth) * 1.15)
            self.ax.legend(loc="lower right", facecolor="#2b2b2b", edgecolor="none", labelcolor="white", fontsize=8)

            self.canvas.draw()

        except Exception as err:
            self.lbl_status.configure(text=f"Erro: {str(err)}")


if __name__ == "__main__":
    app = AlmenApp()
    app.mainloop()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        