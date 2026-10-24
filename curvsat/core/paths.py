"""Caminhos graváveis da aplicação.

Os recursos empacotados pelo PyInstaller podem ficar em uma pasta temporária
ou protegida. Dados que mudam durante o uso devem ficar no perfil do usuário.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_DATA_FOLDER = "CurvSatApp"


def application_data_dir() -> Path:
    """Retorna e cria a pasta de dados graváveis da aplicação."""
    if sys.platform == "win32":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_dir = base_dir / APP_DATA_FOLDER
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _legacy_data_paths(filename: str) -> tuple[Path, ...]:
    """Locais usados por versões antigas, consultados apenas na migração."""
    locations: list[Path] = []

    if getattr(sys, "frozen", False):
        locations.append(Path(sys.executable).resolve().parent / filename)

    locations.append(Path(__file__).resolve().parent / filename)
    return tuple(locations)


def user_data_file(filename: str) -> Path:
    """Retorna um arquivo de dados gravável e migra o arquivo legado uma vez."""
    destination = application_data_dir() / filename
    if destination.exists():
        return destination

    for legacy_file in _legacy_data_paths(filename):
        try:
            if legacy_file.is_file() and legacy_file.resolve() != destination.resolve():
                shutil.copy2(legacy_file, destination)
                break
        except OSError:
            # Uma migração não deve impedir a abertura do aplicativo; o arquivo
            # será criado normalmente quando a aplicação salvar seus dados.
            continue

    return destination
