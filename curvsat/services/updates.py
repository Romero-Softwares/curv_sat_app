"""Consulta segura do manifesto público de atualizações."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any
from urllib.request import Request, urlopen

from curvsat.core.release_public_key import RELEASE_MANIFEST_PUBLIC_KEY
from curvsat.core.version import APP_NAME, APP_VERSION
from curvsat.security.release_signing import verify_manifest


UPDATE_MANIFEST_URL = (
    "https://raw.githubusercontent.com/Romero-Softwares/curv_sat_app/main/"
    "update_manifest.json"
)
_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


@dataclass(frozen=True)
class UpdateInfo:
    """Dados validados de uma atualização disponível."""

    version: str
    release_notes: str
    download_url: str | None


def _version_key(version: str) -> tuple[int, int, int, int, str]:
    """Converte a versão semântica em uma chave comparável."""
    match = _VERSION_PATTERN.fullmatch(str(version).strip())
    if not match:
        raise ValueError("Versão deve estar no formato X.Y.Z ou X.Y.Z-sufixo.")
    major, minor, patch, prerelease = match.groups()
    # Uma versão final sempre é posterior à sua prévia correspondente.
    return int(major), int(minor), int(patch), 1 if prerelease is None else 0, prerelease or ""


def is_newer_version(candidate: str, current: str = APP_VERSION) -> bool:
    """Retorna se ``candidate`` é posterior à versão distribuída."""
    return _version_key(candidate) > _version_key(current)


def _read_manifest(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("O manifesto de atualização deve ser um objeto JSON.")
    return payload


def check_for_update(
    current_version: str = APP_VERSION,
    manifest_url: str = UPDATE_MANIFEST_URL,
    timeout: float = 4.0,
) -> UpdateInfo | None:
    """Consulta o GitHub e retorna uma atualização válida, se existir.

    Problemas de conexão e manifestos inválidos retornam ``None``: a checagem
    é apenas informativa e nunca deve impedir o uso normal do aplicativo.
    """
    try:
        manifest = _read_manifest(manifest_url, timeout)
        if manifest.get("app") != APP_NAME:
            return None
        if not verify_manifest(manifest, RELEASE_MANIFEST_PUBLIC_KEY):
            return None
        version = str(manifest["version"]).strip()
        if not is_newer_version(version, current_version):
            return None
        release_notes = str(manifest.get("release_notes", "")).strip()
        download_url = manifest.get("download_url")
        if download_url is not None:
            download_url = str(download_url).strip()
            if not download_url.startswith(("https://", "http://")):
                return None
        return UpdateInfo(version, release_notes, download_url or None)
    except (KeyError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
