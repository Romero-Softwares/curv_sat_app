"""API SQLite compatível com as RPCs de sincronização CurvSat no Supabase.

O módulo reproduz os dois contratos que o aplicativo desktop já conhece:
``sync_curvsat_license`` e ``sync_curvsat_system_data``. Ele não expõe tabelas
diretamente; cada operação é sempre isolada pelo hash da licença.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


LICENSE_HASH = re.compile(r"^[a-f0-9]{64}$")
REPORT_HASH = re.compile(r"^[a-f0-9]{64}$")
ACTIVE_STATUS = "active"
TOMBSTONE_RETENTION = timedelta(days=7)
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "data" / "curvsat_sync.db"


def _database_path() -> Path:
    configured = os.environ.get("CURVSAT_SYNC_DB")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_DATABASE_PATH


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    database = _database_path()
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Cria o esquema local de sincronização se ele ainda não existir."""
    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS curvsat_license_activations (
                license_hash TEXT PRIMARY KEY CHECK(length(license_hash) = 64),
                organization TEXT NOT NULL CHECK(length(trim(organization)) > 0),
                expires_on TEXT,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'suspended', 'revoked')),
                first_activated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS curvsat_system_settings (
                license_hash TEXT PRIMARY KEY REFERENCES curvsat_license_activations(license_hash)
                    ON DELETE CASCADE,
                values_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS curvsat_system_records (
                license_hash TEXT NOT NULL REFERENCES curvsat_license_activations(license_hash)
                    ON DELETE CASCADE,
                pn TEXT NOT NULL,
                serial_number TEXT NOT NULL DEFAULT '',
                data_json TEXT,
                curve_json TEXT,
                updated_at TEXT NOT NULL,
                deleted INTEGER NOT NULL DEFAULT 0 CHECK(deleted IN (0, 1)),
                PRIMARY KEY (license_hash, pn, serial_number)
            );
            CREATE INDEX IF NOT EXISTS idx_curvsat_system_records_sync
                ON curvsat_system_records (license_hash, updated_at DESC);

            CREATE TABLE IF NOT EXISTS curvsat_system_reports (
                license_hash TEXT NOT NULL REFERENCES curvsat_license_activations(license_hash)
                    ON DELETE CASCADE,
                sha256 TEXT NOT NULL,
                numero TEXT NOT NULL,
                prefixo TEXT NOT NULL,
                ano INTEGER NOT NULL,
                sequencia INTEGER NOT NULL,
                emitido_em TEXT NOT NULL,
                pn TEXT NOT NULL DEFAULT '',
                serial_number TEXT NOT NULL DEFAULT '',
                conteudo_html TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                deleted INTEGER NOT NULL DEFAULT 0 CHECK(deleted IN (0, 1)),
                updated_at TEXT NOT NULL,
                PRIMARY KEY (license_hash, sha256)
            );
            CREATE INDEX IF NOT EXISTS idx_curvsat_system_reports_sync
                ON curvsat_system_reports (license_hash, updated_at DESC);
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _parse_timestamp(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _error(message: str, status_code: int = 400) -> JSONResponse:
    # O cliente atual lê o campo ``message`` nas respostas de erro HTTP.
    return JSONResponse(status_code=status_code, content={"message": message})


async def _payload(request: Request) -> tuple[dict[str, Any] | None, JSONResponse | None]:
    try:
        value = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, _error("Corpo JSON inválido.")
    if not isinstance(value, dict):
        return None, _error("O corpo da solicitação deve ser um objeto JSON.")
    return value, None


def _is_authorized(request: Request) -> bool:
    required_key = os.environ.get("CURVSAT_SYNC_API_KEY", "")
    return not required_key or hmac.compare_digest(request.headers.get("apikey", ""), required_key)


def _require_hash(payload: dict[str, Any]) -> str | None:
    license_hash = payload.get("p_license_hash")
    if not isinstance(license_hash, str) or not LICENSE_HASH.fullmatch(license_hash):
        return None
    return license_hash


def _incoming_is_newer(connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...], updated_at: str) -> bool:
    row = connection.execute(query, parameters).fetchone()
    return row is None or updated_at >= row["updated_at"]


def _sync_settings(connection: sqlite3.Connection, license_hash: str, values: Any, updated_at: Any) -> None:
    normalized_updated_at = _parse_timestamp(updated_at)
    if not isinstance(values, dict) or normalized_updated_at is None:
        return
    if _incoming_is_newer(
        connection,
        "SELECT updated_at FROM curvsat_system_settings WHERE license_hash = ?",
        (license_hash,),
        normalized_updated_at,
    ):
        connection.execute(
            """INSERT INTO curvsat_system_settings (license_hash, values_json, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(license_hash) DO UPDATE SET
                   values_json = excluded.values_json, updated_at = excluded.updated_at""",
            (license_hash, _json(values), normalized_updated_at),
        )


def _sync_records(connection: sqlite3.Connection, license_hash: str, records: Any) -> None:
    if not isinstance(records, list):
        return
    for item in records:
        if not isinstance(item, dict):
            continue
        pn = item.get("pn")
        serial_number = item.get("serial_number", "")
        updated_at = _parse_timestamp(item.get("updated_at"))
        if not isinstance(pn, str) or not pn.strip() or not isinstance(serial_number, str) or updated_at is None:
            continue
        pn = pn.strip()
        deleted = bool(item.get("deleted", False))
        if not _incoming_is_newer(
            connection,
            """SELECT updated_at FROM curvsat_system_records
               WHERE license_hash = ? AND pn = ? AND serial_number = ?""",
            (license_hash, pn, serial_number),
            updated_at,
        ):
            continue
        try:
            data_json = None if deleted else _json(item.get("data"))
            curve_json = None if deleted else _json(item.get("curve"))
        except (TypeError, ValueError):
            continue
        connection.execute(
            """INSERT INTO curvsat_system_records
               (license_hash, pn, serial_number, data_json, curve_json, updated_at, deleted)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(license_hash, pn, serial_number) DO UPDATE SET
                   data_json = excluded.data_json, curve_json = excluded.curve_json,
                   updated_at = excluded.updated_at, deleted = excluded.deleted""",
            (license_hash, pn, serial_number, data_json, curve_json, updated_at, int(deleted)),
        )


def _sync_reports(connection: sqlite3.Connection, license_hash: str, reports: Any) -> None:
    if not isinstance(reports, list):
        return
    for item in reports:
        if not isinstance(item, dict):
            continue
        sha256 = item.get("sha256")
        updated_at = _parse_timestamp(item.get("updated_at"))
        deleted = bool(item.get("deleted", False))
        if not isinstance(sha256, str) or not REPORT_HASH.fullmatch(sha256) or updated_at is None:
            continue
        if not deleted and not all(isinstance(item.get(key), str) and item[key] for key in ("numero", "prefixo", "conteudo_html")):
            continue
        if not _incoming_is_newer(
            connection,
            "SELECT updated_at FROM curvsat_system_reports WHERE license_hash = ? AND sha256 = ?",
            (license_hash, sha256),
            updated_at,
        ):
            continue
        try:
            report = (
                "" if deleted else str(item.get("numero", "")),
                "" if deleted else str(item.get("prefixo", "")),
                0 if deleted else int(item.get("ano", 0)),
                0 if deleted else int(item.get("sequencia", 0)),
                "" if deleted else str(item.get("emitido_em", "")),
                "" if deleted else str(item.get("pn", "")),
                "" if deleted else str(item.get("serial_number", "")),
                "" if deleted else str(item.get("conteudo_html", "")),
                "" if deleted else str(item.get("criado_em", "")),
            )
        except (TypeError, ValueError):
            continue
        connection.execute(
            """INSERT INTO curvsat_system_reports
               (license_hash, sha256, numero, prefixo, ano, sequencia, emitido_em, pn,
                serial_number, conteudo_html, criado_em, deleted, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(license_hash, sha256) DO UPDATE SET
                   numero = excluded.numero, prefixo = excluded.prefixo, ano = excluded.ano,
                   sequencia = excluded.sequencia, emitido_em = excluded.emitido_em,
                   pn = excluded.pn, serial_number = excluded.serial_number,
                   conteudo_html = excluded.conteudo_html, criado_em = excluded.criado_em,
                   deleted = excluded.deleted, updated_at = excluded.updated_at""",
            (license_hash, sha256, *report, int(deleted), updated_at),
        )


def _purge_expired_tombstones(connection: sqlite3.Connection, license_hash: str) -> None:
    cutoff = (datetime.now(timezone.utc) - TOMBSTONE_RETENTION).isoformat()
    connection.execute(
        "DELETE FROM curvsat_system_records WHERE license_hash = ? AND deleted = 1 AND updated_at <= ?",
        (license_hash, cutoff),
    )
    connection.execute(
        "DELETE FROM curvsat_system_reports WHERE license_hash = ? AND deleted = 1 AND updated_at <= ?",
        (license_hash, cutoff),
    )


def _system_state(connection: sqlite3.Connection, license_hash: str) -> dict[str, Any]:
    settings_row = connection.execute(
        "SELECT values_json, updated_at FROM curvsat_system_settings WHERE license_hash = ?",
        (license_hash,),
    ).fetchone()
    records = []
    for row in connection.execute(
        """SELECT pn, serial_number, data_json, curve_json, updated_at, deleted
           FROM curvsat_system_records WHERE license_hash = ? ORDER BY pn, serial_number""",
        (license_hash,),
    ):
        records.append({
            "pn": row["pn"], "serial_number": row["serial_number"],
            "data": json.loads(row["data_json"]) if row["data_json"] is not None else None,
            "curve": json.loads(row["curve_json"]) if row["curve_json"] is not None else None,
            "updated_at": row["updated_at"], "deleted": bool(row["deleted"]),
        })
    reports = []
    for row in connection.execute(
        "SELECT * FROM curvsat_system_reports WHERE license_hash = ? ORDER BY sha256",
        (license_hash,),
    ):
        reports.append({key: row[key] for key in (
            "numero", "prefixo", "ano", "sequencia", "emitido_em", "pn", "serial_number",
            "conteudo_html", "sha256", "criado_em", "updated_at",
        )} | {"deleted": bool(row["deleted"])})
    return {
        "settings": None if settings_row is None else {
            "values": json.loads(settings_row["values_json"]), "updated_at": settings_row["updated_at"],
        },
        "records": records,
        "reports": reports,
    }


def install_sync_api(app: FastAPI) -> None:
    """Registra as RPCs de sincronização no aplicativo FastAPI fornecido."""
    initialize_database()

    @app.get("/api/sync/health")
    def sync_health() -> dict[str, str]:
        return {"status": "ok", "service": "curvsat-sync"}

    @app.post("/rest/v1/rpc/sync_curvsat_license")
    async def sync_curvsat_license(request: Request) -> JSONResponse:
        if not _is_authorized(request):
            return _error("Chave de API inválida.", 401)
        payload, error = await _payload(request)
        if error is not None:
            return error
        assert payload is not None
        license_hash = _require_hash(payload)
        organization = payload.get("p_organization")
        expires_on = payload.get("p_expires_on")
        if license_hash is None:
            return _error("Hash de licença inválido.")
        if not isinstance(organization, str) or not organization.strip():
            return _error("Organização inválida.")
        if expires_on is not None:
            try:
                datetime.strptime(expires_on, "%Y-%m-%d")
            except (TypeError, ValueError):
                return _error("Data de validade inválida.")
        now = _now()
        with _connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """INSERT INTO curvsat_license_activations
                       (license_hash, organization, expires_on, first_activated_at, last_seen_at)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(license_hash) DO UPDATE SET last_seen_at = excluded.last_seen_at""",
                    (license_hash, organization.strip(), expires_on, now, now),
                )
                row = connection.execute(
                    "SELECT status, last_seen_at FROM curvsat_license_activations WHERE license_hash = ?",
                    (license_hash,),
                ).fetchone()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return JSONResponse([{"status": row["status"], "matched": True, "last_seen_at": row["last_seen_at"]}])

    @app.post("/rest/v1/rpc/sync_curvsat_system_data")
    async def sync_curvsat_system_data(request: Request) -> JSONResponse:
        if not _is_authorized(request):
            return _error("Chave de API inválida.", 401)
        payload, error = await _payload(request)
        if error is not None:
            return error
        assert payload is not None
        license_hash = _require_hash(payload)
        if license_hash is None:
            return _error("Hash de licença inválido.")
        with _connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                license_row = connection.execute(
                    "SELECT status FROM curvsat_license_activations WHERE license_hash = ?", (license_hash,)
                ).fetchone()
                if license_row is None or license_row["status"] != ACTIVE_STATUS:
                    connection.rollback()
                    return _error("Licença ativa obrigatória.", 403)
                _sync_settings(connection, license_hash, payload.get("p_settings"), payload.get("p_settings_updated_at"))
                _sync_records(connection, license_hash, payload.get("p_records"))
                _sync_reports(connection, license_hash, payload.get("p_reports"))
                _purge_expired_tombstones(connection, license_hash)
                state = _system_state(connection, license_hash)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return JSONResponse(state)
