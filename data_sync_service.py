"""Sincroniza configura\u00e7\u00f5es e cadastros da organiza\u00e7\u00e3o entre computadores."""

from __future__ import annotations

from typing import Any

from i18n import apply_shared_settings, get_shared_settings
from reports import BancoDadosPN
from supabase_service import sync_system_data


def synchronize_system_data(activation_code: str) -> dict[str, int]:
    """Consolida os dados locais com o estado remoto identificado pela licen\u00e7a."""
    banco = BancoDadosPN()
    local = banco.exportar_para_sincronizacao()
    shared_settings, settings_updated_at = get_shared_settings()
    remote = sync_system_data(
        activation_code=activation_code,
        settings=shared_settings,
        settings_updated_at=settings_updated_at,
        records=local["records"],
        reports=local["reports"],
    )
    settings = remote.get("settings")
    if isinstance(settings, dict):
        values = settings.get("values")
        updated_at = settings.get("updated_at")
        if isinstance(values, dict):
            apply_shared_settings(values, updated_at if isinstance(updated_at, str) else None)
    merged = banco.importar_da_sincronizacao(
        remote.get("records", []), remote.get("reports", [])
    )
    return merged
