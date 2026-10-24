"""Assinatura local dos manifestos e artefatos de atualização.

Esta assinatura é uma camada de integridade do CurvSat. Ela não é uma
assinatura Authenticode e, portanto, não altera a reputação do SmartScreen.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


SIGNATURE_FIELD = "local_signature"
SIGNATURE_ALGORITHM = "Ed25519"
SIGNATURE_FORMAT = "merotec.release-manifest.v1"
PRIVATE_KEY_FORMAT = "merotec.ed25519.private.v1"


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("Valor codificado em base64 ausente.")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def public_key_id(public_key: bytes) -> str:
    """Retorna o identificador curto e reproduzível de uma chave pública."""
    return "ed25519:" + hashlib.sha256(public_key).hexdigest()[:24]


def canonical_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Serializa os campos assinados sem depender da formatação do JSON."""
    unsigned = dict(manifest)
    unsigned.pop(SIGNATURE_FIELD, None)
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def artifact_metadata(path: Path) -> dict[str, int | str]:
    """Calcula os dados imutáveis do instalador que entram no manifesto."""
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for block in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(block)
    return {
        "name": path.name,
        "sha256": digest.hexdigest(),
        "size": path.stat().st_size,
    }


def generate_private_key_file(path: Path) -> tuple[str, str]:
    """Cria uma chave Ed25519 local e retorna chave pública e identificador."""
    if path.exists():
        raise FileExistsError(f"A chave privada já existe: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    payload = {
        "format": PRIVATE_KEY_FORMAT,
        "algorithm": SIGNATURE_ALGORITHM,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "private_key": _b64encode(private_bytes),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return _b64encode(public_bytes), public_key_id(public_bytes)


def load_private_key(path: Path) -> Ed25519PrivateKey:
    """Carrega a chave local e rejeita arquivos incompatíveis ou corrompidos."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não foi possível ler a chave privada local: {error}") from error
    if not isinstance(payload, dict) or payload.get("format") != PRIVATE_KEY_FORMAT:
        raise ValueError("Arquivo de chave privada local inválido.")
    try:
        return Ed25519PrivateKey.from_private_bytes(_b64decode(payload["private_key"]))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Chave privada Ed25519 inválida.") from error


def sign_manifest(
    manifest: Mapping[str, Any],
    artifact: Path,
    private_key: Ed25519PrivateKey,
) -> dict[str, Any]:
    """Inclui hash do artefato e assinatura no manifesto de atualização."""
    signed = dict(manifest)
    signed["artifact"] = artifact_metadata(artifact)
    public_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    signature = private_key.sign(canonical_manifest_bytes(signed))
    signed[SIGNATURE_FIELD] = {
        "format": SIGNATURE_FORMAT,
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": public_key_id(public_bytes),
        "value": _b64encode(signature),
    }
    return signed


def verify_manifest(manifest: Mapping[str, Any], public_key_b64: str) -> bool:
    """Verifica a autenticidade do manifesto com uma chave pública conhecida."""
    signature = manifest.get(SIGNATURE_FIELD)
    if not isinstance(signature, Mapping):
        return False
    if signature.get("format") != SIGNATURE_FORMAT or signature.get("algorithm") != SIGNATURE_ALGORITHM:
        return False
    try:
        public_bytes = _b64decode(public_key_b64)
        if signature.get("key_id") != public_key_id(public_bytes):
            return False
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        public_key.verify(_b64decode(str(signature["value"])), canonical_manifest_bytes(manifest))
    except (KeyError, TypeError, ValueError, InvalidSignature):
        return False
    return True


def verify_artifact(path: Path, manifest: Mapping[str, Any]) -> bool:
    """Confere se um executável ainda corresponde aos metadados assinados."""
    metadata = manifest.get("artifact")
    if not path.is_file() or not isinstance(metadata, Mapping):
        return False
    try:
        expected_name = str(metadata["name"])
        expected_hash = str(metadata["sha256"])
        expected_size = int(metadata["size"])
    except (KeyError, TypeError, ValueError):
        return False
    actual = artifact_metadata(path)
    return (
        actual["name"] == expected_name
        and actual["sha256"] == expected_hash
        and actual["size"] == expected_size
    )
