"""Gerador visual de chaves de ativação CurvSat.

Este programa é uma ferramenta do fornecedor. A chave privada usada para
assinar ativações não deve ser distribuída com o aplicativo do cliente.
"""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from license_service import LicenseError, create_activation_code


OUTPUT_FILENAME = "chave_ativacao.txt"


def application_directory() -> Path:
    """Retorna a pasta do .exe, ou a do script durante o desenvolvimento."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(relative_path: str) -> Path:
    """Localiza recursos tanto no fonte quanto no executável PyInstaller."""
    bundle_directory = Path(getattr(sys, "_MEIPASS", application_directory()))
    return bundle_directory / relative_path


DEFAULT_PRIVATE_KEY_FILE = resource_path("licensing/issuer_private_key.json")
DEFAULT_OUTPUT_FILE = application_directory() / OUTPUT_FILENAME


def _load_private_exponent(path: Path) -> int:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return int(content["private_exponent"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise LicenseError(f"Não foi possível ler a chave privada em '{path}'.") from error


def generate_activation_file(
    organization: str,
    expires: str | None = None,
    private_key_file: Path = DEFAULT_PRIVATE_KEY_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
) -> tuple[str, Path]:
    """Gera, assina e registra a chave de ativação em um arquivo de texto."""
    clean_installation_key = ""
    clean_organization = organization.strip()
    clean_expires = expires.strip() if expires else None
    activation_code = create_activation_code(
        clean_organization,
        _load_private_exponent(private_key_file),
        expires=clean_expires or None,
    )
    resolved_output = output_file.expanduser().resolve()
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(
        "Chave de ativação CurvSat\n"
        f"Organização: {clean_organization}\n"
        f"Chave de instalação: {clean_installation_key}\n"
        f"Validade: {clean_expires or 'Sem expiração'}\n\n"
        f"{activation_code}\n",
        encoding="utf-8",
    )
    return activation_code, resolved_output


class LicenseGeneratorWindow(ttk.Frame):
    """Interface gráfica para emissão de uma chave de ativação."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=24)
        self.master = master
        self.installation_key = tk.StringVar()
        self.organization = tk.StringVar()
        self.expires = tk.StringVar()
        self.status = tk.StringVar(value="Preencha os dados da licença.")
        self._build()

    def _build(self) -> None:
        self.master.title("Gerador de Chaves CurvSat")
        self.master.resizable(False, False)
        self.master.minsize(620, 330)
        self.grid(sticky="nsew")
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Gerador de Chave de Ativação", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            self,
            text="A chave gerada será salva como chave_ativacao.txt na mesma pasta deste executável.",
            wraplength=560,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 20))

        ttk.Label(self, text="Chave de instalação:").grid(row=2, column=0, sticky="w", pady=5)
        installation_entry = ttk.Entry(self, textvariable=self.installation_key, width=48)
        installation_entry.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(self, text="Empresa / organização:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.organization, width=48).grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(self, text="Validade (opcional):").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.expires, width=20).grid(row=4, column=1, sticky="w", pady=5)
        ttk.Label(self, text="Formato: AAAA-MM-DD").grid(row=5, column=1, sticky="w")

        ttk.Separator(self).grid(row=6, column=0, columnspan=2, sticky="ew", pady=18)
        ttk.Button(self, text="Gerar e salvar chave", command=self.generate).grid(
            row=6, column=1, sticky="e"
        )
        ttk.Label(self, textvariable=self.status, foreground="#155724", wraplength=560).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(14, 0)
        )
        self.focus_set()

    def generate(self) -> None:
        try:
            _, output_file = generate_activation_file(
                self.organization.get(),
                self.expires.get(),
            )
        except LicenseError as error:
            self.status.set("Não foi possível gerar a chave.")
            messagebox.showerror("Dados inválidos", str(error), parent=self.master)
            return
        except OSError as error:
            self.status.set("Não foi possível salvar o arquivo.")
            messagebox.showerror("Erro ao salvar", str(error), parent=self.master)
            return

        self.status.set(f"Chave salva em: {output_file}")
        messagebox.showinfo(
            "Chave gerada",
            f"A chave de ativação foi salva com sucesso em:\n{output_file}",
            parent=self.master,
        )


def launch_gui() -> int:
    root = tk.Tk()
    LicenseGeneratorWindow(root)
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera uma chave de ativação CurvSat assinada.")
    parser.add_argument("installation_key", nargs="?", help="Chave exibida nas configurações do cliente.")
    parser.add_argument("organization", nargs="?", help="Nome da empresa ou organização licenciada.")
    parser.add_argument("--expires", metavar="AAAA-MM-DD", help="Data opcional de expiração.")
    parser.add_argument("--private-key", type=Path, default=DEFAULT_PRIVATE_KEY_FILE, help="Arquivo privado do emissor.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Arquivo de texto de saída.")
    arguments = parser.parse_args()

    if not arguments.installation_key and not arguments.organization:
        return launch_gui()
    if arguments.installation_key and not arguments.organization:
        arguments.organization = arguments.installation_key
    if not arguments.installation_key or not arguments.organization:
        parser.error("informe a chave de instalação e a organização, ou execute sem argumentos para usar a interface gráfica.")

    try:
        _, output_file = generate_activation_file(
            arguments.organization,
            arguments.expires,
            arguments.private_key,
            arguments.output,
        )
        print(f"Chave gravada em: {output_file}")
    except LicenseError as error:
        parser.error(str(error))
    except OSError as error:
        parser.error(f"Não foi possível gravar o arquivo de saída: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
