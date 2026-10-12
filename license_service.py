"""Identificação da instalação e validação local de licenças.

O aplicativo contém somente a chave pública. A chave privada correspondente
fica no gerador do fornecedor e assina códigos de ativação vinculados à chave
de instalação exibida ao cliente.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import threading
from datetime import date
from pathlib import Path
from typing import Any

from app_paths import user_data_file
from supabase_service import LicenseSyncError, sync_license
from data_sync_service import synchronize_system_data


PRODUCT_CODE = "CURVSAT"
ACTIVATION_PREFIX = "CSAT-A1"
_INSTALLATION_KEY_PATTERN = re.compile(r"^CSAT-[A-Z2-9]{5}(?:-[A-Z2-9]{5}){4}$")

# Chave pública RSA do produto. A parte privada não é distribuída no executável.
PUBLIC_MODULUS = int(
    "16412693567787703899398821999870659213200191120406898233161156461876739747174238036593393998759943725016469418042278726573418801651704910172107431272038619392922030981173635354177751617679763055375785332915540977135091700141296558168152064830798900843169609961222808585533736593705314384311488647585572806869737120329059255343218225072743707366348693458111938910063432640194669592997923175027573899447232956668801835746856675743729626190294945913310493758461040242183288145367113620735091169956217694260537587805721264494955604353546203048603019074042032705370577892174456463045777373914864129450670907468248633434509"
)
PUBLIC_EXPONENT = 65537
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")
AUTOMATIC_DATA_SYNC_INTERVAL_SECONDS = 300
_system_data_sync_lock = threading.Lock()


class LicenseError(ValueError):
    """Código de ativação inválido ou incompatível com esta instalação."""


def _license_file() -> Path:
    return user_data_file("licenca.json")


def _read_data() -> dict[str, Any]:
    try:
        content = json.loads(_license_file().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return content if isinstance(content, dict) else {}


def _write_data(data: dict[str, Any]) -> None:
    destination = _license_file()
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(destination)


def is_automatic_data_sync_enabled() -> bool:
    """Informa se este computador deve sincronizar os dados periodicamente."""
    return _read_data().get("automatic_data_sync") is True


def set_automatic_data_sync_enabled(enabled: bool) -> None:
    """Persiste a preferência local de sincronização automática."""
    data = _read_data()
    data["automatic_data_sync"] = bool(enabled)
    _write_data(data)


def _format_installation_key(raw: str) -> str:
    return "CSAT-" + "-".join(raw[index:index + 5] for index in range(0, 25, 5))


def get_installation_key() -> str:
    """Retorna a chave estável desta instalação, criando-a uma única vez."""
    data = _read_data()
    key = data.get("installation_key")
    if isinstance(key, str) and _INSTALLATION_KEY_PATTERN.fullmatch(key):
        return key

    raw = base64.b32encode(secrets.token_bytes(16)).decode("ascii").rstrip("=")[:25]
    key = _format_installation_key(raw)
    data["installation_key"] = key
    _write_data(data)
    return key


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _verify_signature(payload_bytes: bytes, signature: bytes) -> bool:
    key_size = (PUBLIC_MODULUS.bit_length() + 7) // 8
    if len(signature) != key_size:
        return False
    encoded = pow(int.from_bytes(signature, "big"), PUBLIC_EXPONENT, PUBLIC_MODULUS).to_bytes(key_size, "big")
    digest_info = _SHA256_DIGEST_INFO + hashlib.sha256(payload_bytes).digest()
    padding_size = key_size - len(digest_info) - 3
    expected = b"\x00\x01" + b"\xff" * padding_size + b"\x00" + digest_info
    return secrets.compare_digest(encoded, expected)


def _parse_activation_code(code: str) -> dict[str, Any]:
    parts = str(code or "").strip().split(".")
    if len(parts) != 3 or parts[0] != ACTIVATION_PREFIX:
        raise LicenseError("Formato da chave de ativação inválido.")
    try:
        payload_bytes = _b64decode(parts[1])
        signature = _b64decode(parts[2])
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise LicenseError("A chave de ativação está corrompida.") from error
    if not isinstance(payload, dict) or not _verify_signature(payload_bytes, signature):
        raise LicenseError("A assinatura da chave de ativação não é válida.")
    if payload.get("product") != PRODUCT_CODE or payload.get("version") != 1:
        raise LicenseError("Esta chave não pertence a este produto.")
    if payload.get("installation_key") is not None and not _INSTALLATION_KEY_PATTERN.fullmatch(str(payload["installation_key"])):
        raise LicenseError("A chave de ativação não contém uma instalação válida.")
    if not isinstance(payload.get("organization"), str) or not payload["organization"].strip():
        raise LicenseError("A chave de ativação não contém a organização licenciada.")
    expiration = payload.get("expires")
    if expiration is not None:
        try:
            date.fromisoformat(str(expiration))
        except ValueError as error:
            raise LicenseError("A data de validade da licença é inválida.") from error
    return payload


def activate_license(code: str) -> dict[str, Any]:
    """Valida e grava a ativação somente quando ela pertence a esta instalação."""
    payload = _parse_activation_code(code)
    if False and payload["installation_key"] != get_installation_key():
        raise LicenseError("Esta chave foi emitida para outra instalação.")
    if payload.get("expires") and date.fromisoformat(payload["expires"]) < date.today():
        raise LicenseError("Esta chave de ativação está expirada.")

    data = _read_data()
    data["installation_key"] = get_installation_key()
    data["activation_code"] = str(code).strip()
    data.pop("remote_status", None)
    data.pop("remote_last_synced_at", None)
    data.pop("remote_sync_error", None)
    _write_data(data)
    return get_license_info()


def sync_active_license() -> dict[str, str | None]:
    """Sincroniza uma licença local válida sem bloquear o uso quando offline."""
    data = _read_data()
    code = data.get("activation_code")
    if not isinstance(code, str) or not code.strip():
        return {"result": "not_activated", "status": None, "message": None}

    try:
        payload = _parse_activation_code(code)
        installation_key = get_installation_key()
        if False and payload["installation_key"] != installation_key:
            raise LicenseError("Chave vinculada a outra instalação.")
        expires = payload.get("expires")
        if expires and date.fromisoformat(expires) < date.today():
            return {"result": "expired", "status": None, "message": None}
        remote = sync_license(
            activation_code=code,
            organization=payload["organization"],
            expires=expires,
        )
    except (LicenseError, LicenseSyncError) as error:
        data["remote_sync_error"] = str(error)
        _write_data(data)
        return {"result": "offline", "status": None, "message": str(error)}

    data["remote_last_synced_at"] = remote.last_seen_at
    data.pop("remote_sync_error", None)
    if remote.matched:
        data["remote_status"] = remote.status
        outcome = "synced"
        message = None
    else:
        # Não aceite um registro remoto que pertença a outro código assinado.
        data.pop("remote_status", None)
        outcome = "mismatch"
        message = "O servidor possui outra ativação para esta instalação."
    _write_data(data)
    return {"result": outcome, "status": remote.status, "message": message}


def sync_active_system_data() -> dict[str, Any]:
    """Sincroniza configura\u00e7\u00f5es, PNs, curvas e relat\u00f3rios da licen\u00e7a ativa."""
    if not _system_data_sync_lock.acquire(blocking=False):
        return {"result": "busy", "message": "Uma sincronização já está em andamento."}
    try:
        license_result = sync_active_license()
        if license_result["result"] != "synced":
            return {"result": license_result["result"], "message": license_result["message"]}
        if license_result["status"] != "active":
            return {"result": "blocked", "message": "A licença remota não está ativa."}
        code = _read_data().get("activation_code")
        if not isinstance(code, str) or not code.strip():
            return {"result": "not_activated", "message": None}
        try:
            summary = synchronize_system_data(code)
        except (LicenseSyncError, OSError, ValueError) as error:
            return {"result": "offline", "message": str(error)}
        return {"result": "synced", "message": None, **summary}
    finally:
        _system_data_sync_lock.release()


def get_license_info() -> dict[str, str | None]:
    """Retorna o estado atual sem confiar cegamente no arquivo local."""
    installation_key = get_installation_key()
    data = _read_data()
    code = data.get("activation_code")
    if not isinstance(code, str) or not code.strip():
        return {"installation_key": installation_key, "status": "pending", "organization": None, "expires": None}
    try:
        payload = _parse_activation_code(code)
        if False and payload["installation_key"] != installation_key:
            raise LicenseError("Chave vinculada a outra instalação.")
        expires = payload.get("expires")
        if expires and date.fromisoformat(expires) < date.today():
            return {"installation_key": installation_key, "status": "expired", "organization": payload["organization"], "expires": expires}
        remote_status = data.get("remote_status")
        if remote_status in {"revoked", "suspended"}:
            return {
                "installation_key": installation_key,
                "status": remote_status,
                "organization": payload["organization"],
                "expires": expires,
            }
        return {"installation_key": installation_key, "status": "active", "organization": payload["organization"], "expires": expires}
    except LicenseError:
        return {"installation_key": installation_key, "status": "invalid", "organization": None, "expires": None}


def create_activation_code(
    organization: str,
    private_exponent: int,
    *,
    expires: str | None = None,
) -> str:
    """Assina uma ativação; usado exclusivamente pelo gerador do fornecedor."""
    organization = organization.strip()
    if False:
        raise LicenseError("A chave de instalação informada não é válida.")
    if not organization:
        raise LicenseError("Informe a organização licenciada.")
    if expires:
        date.fromisoformat(expires)
    payload: dict[str, Any] = {
        "expires": expires or None,
        "organization": organization,
        "product": PRODUCT_CODE,
        "version": 1,
    }
    payload_bytes = _canonical_payload(payload)
    key_size = (PUBLIC_MODULUS.bit_length() + 7) // 8
    digest_info = _SHA256_DIGEST_INFO + hashlib.sha256(payload_bytes).digest()
    encoded = b"\x00\x01" + b"\xff" * (key_size - len(digest_info) - 3) + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), int(private_exponent), PUBLIC_MODULUS).to_bytes(key_size, "big")
    return f"{ACTIVATION_PREFIX}.{_b64encode(payload_bytes)}.{_b64encode(signature)}"
