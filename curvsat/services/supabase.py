"""Sincroniza o estado de licenças com o projeto Supabase do produto.

Somente a chave publishable é distribuída. Ela é enviada exclusivamente no
cabeçalho ``apikey`` porque chaves ``sb_publishable`` não são JWTs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SUPABASE_URL = "https://eizufvquvqdcwrojslfm.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_Bm1QBy7tqNaffK2ozkmxJw_K15Oe8t3"
SYNC_RPC_PATH = "/rest/v1/rpc/sync_curvsat_license"
SYSTEM_DATA_SYNC_RPC_PATH = "/rest/v1/rpc/sync_curvsat_system_data"
_VALID_REMOTE_STATUSES = frozenset({"active", "suspended", "revoked"})


class LicenseSyncError(RuntimeError):
    """Falha temporária ou resposta inválida do serviço de sincronização."""


@dataclass(frozen=True)
class LicenseSyncResult:
    status: str
    matched: bool
    last_seen_at: str | None


def activation_hash(activation_code: str) -> str:
    """Retorna uma impressão irreversível do código de ativação."""
    return hashlib.sha256(activation_code.encode("utf-8")).hexdigest()


def _request_json(url: str, payload: dict[str, Any], timeout: float) -> Any:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        # O PostgREST devolve o detalhe do PostgreSQL no corpo. Preservá-lo
        # torna problemas de esquema corrigíveis sem acesso a logs remotos.
        try:
            error_payload = json.loads(error.read().decode("utf-8"))
            server_message = error_payload.get("message") if isinstance(error_payload, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            server_message = None
        if isinstance(server_message, str) and server_message.strip():
            raise LicenseSyncError(
                f"O servidor recusou a sincronização (HTTP {error.code}): {server_message.strip()}."
            ) from error
        raise LicenseSyncError(f"O servidor recusou a sincronização (HTTP {error.code}).") from error
    except (URLError, TimeoutError, OSError) as error:
        raise LicenseSyncError("Não foi possível conectar ao servidor de licenças.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LicenseSyncError("O servidor retornou uma resposta inválida.") from error


def sync_license(
    *,
    activation_code: str,
    organization: str,
    expires: str | None,
    timeout: float = 6.0,
) -> LicenseSyncResult:
    """Registra o heartbeat da ativação e retorna o status remoto.

    A licença assinada continua sendo validada localmente pelo aplicativo.
    Falhas de rede são retornadas ao chamador e nunca invalidam a ativação local.
    """
    try:
        expires_on = date.fromisoformat(expires).isoformat() if expires else None
    except ValueError as error:
        raise LicenseSyncError("A data de validade local é inválida.") from error

    payload = {
        "p_license_hash": activation_hash(activation_code),
        "p_organization": organization,
        "p_expires_on": expires_on,
    }
    response = _request_json(f"{SUPABASE_URL}{SYNC_RPC_PATH}", payload, timeout)
    if not isinstance(response, list) or len(response) != 1 or not isinstance(response[0], dict):
        raise LicenseSyncError("O servidor retornou um estado de licença inválido.")

    item = response[0]
    status = item.get("status")
    matched = item.get("matched")
    last_seen_at = item.get("last_seen_at")
    if status not in _VALID_REMOTE_STATUSES or not isinstance(matched, bool):
        raise LicenseSyncError("O servidor retornou um estado de licença inválido.")
    if last_seen_at is not None and not isinstance(last_seen_at, str):
        raise LicenseSyncError("O servidor retornou uma data de sincronização inválida.")
    return LicenseSyncResult(status=status, matched=matched, last_seen_at=last_seen_at)


def sync_system_data(
    *,
    activation_code: str,
    settings: dict[str, Any],
    settings_updated_at: str | None,
    records: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Envia as altera\u00e7\u00f5es locais e devolve o estado consolidado da organiza\u00e7\u00e3o.

    O banco remoto faz o merge por registro e data de altera\u00e7\u00e3o. Assim, dois
    computadores podem sincronizar PNs diferentes sem um sobrescrever o outro.
    """
    if not isinstance(settings, dict) or not isinstance(records, list) or not isinstance(reports, list):
        raise LicenseSyncError("Os dados locais de sincroniza\u00e7\u00e3o s\u00e3o inv\u00e1lidos.")
    payload = {
        "p_license_hash": activation_hash(activation_code),
        "p_settings": settings,
        "p_settings_updated_at": settings_updated_at,
        "p_records": records,
        "p_reports": reports,
    }
    response = _request_json(f"{SUPABASE_URL}{SYSTEM_DATA_SYNC_RPC_PATH}", payload, timeout)
    # A RPC retorna ``jsonb``. O PostgREST devolve esse valor diretamente como
    # objeto JSON; algumas vers\u00f5es/instala\u00e7\u00f5es anteriores o encapsulam em uma
    # linha com o nome da fun\u00e7\u00e3o. Aceitamos ambos para manter os clientes
    # atualizados compat\u00edveis com os bancos j\u00e1 publicados.
    if isinstance(response, dict):
        remote_payload = response
    elif (
        isinstance(response, list)
        and len(response) == 1
        and isinstance(response[0], dict)
    ):
        remote_payload = response[0].get("sync_curvsat_system_data")
    else:
        raise LicenseSyncError("O servidor retornou dados do sistema inv\u00e1lidos.")
    if not isinstance(remote_payload, dict):
        raise LicenseSyncError("O servidor retornou dados do sistema inv\u00e1lidos.")
    if not isinstance(remote_payload.get("records", []), list) or not isinstance(remote_payload.get("reports", []), list):
        raise LicenseSyncError("O servidor retornou dados do sistema inv\u00e1lidos.")
    return remote_payload
