"""Contrato HTTP da API SQLite compatível com a sincronização Supabase."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi import FastAPI
from fastapi import Request

from server.sync_api import install_sync_api


class SyncApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.database = Path(self.directory.name) / "sync.db"
        self.previous_database = os.environ.get("CURVSAT_SYNC_DB")
        self.previous_api_key = os.environ.get("CURVSAT_SYNC_API_KEY")
        os.environ["CURVSAT_SYNC_DB"] = str(self.database)
        os.environ.pop("CURVSAT_SYNC_API_KEY", None)
        app = FastAPI()
        install_sync_api(app)
        self.app = app
        self.license_hash = hashlib.sha256(b"CSAT-A1.exemplo.assinatura").hexdigest()

    def tearDown(self) -> None:
        if self.previous_database is None:
            os.environ.pop("CURVSAT_SYNC_DB", None)
        else:
            os.environ["CURVSAT_SYNC_DB"] = self.previous_database
        if self.previous_api_key is None:
            os.environ.pop("CURVSAT_SYNC_API_KEY", None)
        else:
            os.environ["CURVSAT_SYNC_API_KEY"] = self.previous_api_key
        self.directory.cleanup()

    def _activate(self) -> None:
        response = self._post("/rest/v1/rpc/sync_curvsat_license", {
            "p_license_hash": self.license_hash,
            "p_organization": "Empresa de Teste",
            "p_expires_on": None,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json_response(response)[0]["status"], "active")

    def _post(self, path: str, payload: dict, headers: dict[str, str] | None = None):
        route = next(item for item in self.app.routes if getattr(item, "path", None) == path)
        body = json.dumps(payload).encode("utf-8")
        request_headers = [(b"content-type", b"application/json")]
        request_headers.extend(
            (key.lower().encode("ascii"), value.encode("utf-8"))
            for key, value in (headers or {}).items()
        )
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request({
            "type": "http", "method": "POST", "path": path, "headers": request_headers,
            "query_string": b"", "scheme": "http", "server": ("testserver", 80),
            "client": ("testclient", 50000), "root_path": "",
        }, receive)
        return asyncio.run(route.endpoint(request))

    @staticmethod
    def _json_response(response):
        return json.loads(response.body)

    def _sync(self, **overrides):
        payload = {
            "p_license_hash": self.license_hash,
            "p_settings": {},
            "p_settings_updated_at": None,
            "p_records": [],
            "p_reports": [],
        }
        payload.update(overrides)
        return self._post("/rest/v1/rpc/sync_curvsat_system_data", payload)

    def test_license_route_matches_postgrest_list_contract(self):
        self._activate()
        response = self._post("/rest/v1/rpc/sync_curvsat_license", {
            "p_license_hash": self.license_hash,
            "p_organization": "Outra organização",
            "p_expires_on": None,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json_response(response)[0]["status"], "active")
        self.assertTrue(self._json_response(response)[0]["matched"])

    def test_system_sync_merges_newest_data_and_compacts_tombstone(self):
        self._activate()
        first = self._sync(
            p_settings={"language": "PT"},
            p_settings_updated_at="2026-11-05T10:00:00+00:00",
            p_records=[{
                "pn": "PN-001", "serial_number": "", "data": {"Peça / PN": "PN-001"},
                "curve": {"codigo_curva": "A2542"}, "updated_at": "2026-11-05T10:00:00+00:00",
                "deleted": False,
            }],
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self._json_response(first)["records"][0]["curve"]["codigo_curva"], "A2542")

        stale = self._sync(p_records=[{
            "pn": "PN-001", "serial_number": "", "data": {"Peça / PN": "antigo"},
            "curve": None, "updated_at": "2026-11-05T09:00:00+00:00", "deleted": False,
        }])
        self.assertEqual(stale.status_code, 200)
        self.assertEqual(self._json_response(stale)["records"][0]["curve"]["codigo_curva"], "A2542")

        deleted = self._sync(p_records=[{
            "pn": "PN-001", "serial_number": "", "data": {"não": "exportado"},
            "curve": {"não": "exportada"}, "updated_at": "2026-11-05T11:00:00+00:00", "deleted": True,
        }])
        item = self._json_response(deleted)["records"][0]
        self.assertTrue(item["deleted"])
        self.assertIsNone(item["data"])
        self.assertIsNone(item["curve"])

    def test_requires_prior_active_license_and_enforces_optional_api_key(self):
        denied = self._sync()
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self._json_response(denied)["message"], "Licença ativa obrigatória.")

        os.environ["CURVSAT_SYNC_API_KEY"] = "chave-local"
        rejected = self._post("/rest/v1/rpc/sync_curvsat_license", {
            "p_license_hash": self.license_hash, "p_organization": "Empresa", "p_expires_on": None,
        })
        self.assertEqual(rejected.status_code, 401)
        accepted = self._post(
            "/rest/v1/rpc/sync_curvsat_license",
            {"p_license_hash": self.license_hash, "p_organization": "Empresa", "p_expires_on": None},
            headers={"apikey": "chave-local"},
        )
        self.assertEqual(accepted.status_code, 200)


if __name__ == "__main__":
    unittest.main()
