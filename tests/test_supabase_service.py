"""Testes do cliente HTTP de sincronização de licença."""

from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from curvsat.services.supabase import activation_hash, sync_license, sync_system_data


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class SupabaseServiceTests(unittest.TestCase):
    @patch("curvsat.services.supabase.urlopen")
    def test_sync_uses_publishable_key_only_in_apikey_header(self, mocked_urlopen):
        mocked_urlopen.return_value = _Response([
            {"status": "active", "matched": True, "last_seen_at": "2026-10-11T20:00:00+00:00"}
        ])

        result = sync_license(
            activation_code="CSAT-A1.exemplo.assinatura",
            organization="Empresa de Teste",
            expires=None,
        )

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Apikey"), "sb_publishable_Bm1QBy7tqNaffK2ozkmxJw_K15Oe8t3")
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(
            json.loads(request.data.decode("utf-8"))["p_license_hash"],
            activation_hash("CSAT-A1.exemplo.assinatura"),
        )
        self.assertEqual(result.status, "active")
        self.assertTrue(result.matched)

    def test_activation_hash_is_deterministic_and_does_not_return_the_code(self):
        code = "CSAT-A1.exemplo.assinatura"
        digest = activation_hash(code)
        self.assertEqual(len(digest), 64)
        self.assertNotIn(code, digest)
        self.assertEqual(digest, activation_hash(code))

    @patch("curvsat.services.supabase.urlopen")
    def test_system_sync_sends_structured_data_to_dedicated_rpc(self, mocked_urlopen):
        # Uma RPC que retorna jsonb \u00e9 devolvida diretamente pelo PostgREST,
        # sem uma lista e sem o nome da fun\u00e7\u00e3o como chave envolvente.
        mocked_urlopen.return_value = _Response({"settings": None, "records": [], "reports": []})

        remote = sync_system_data(
            activation_code="CSAT-A1.exemplo.assinatura",
            settings={"language": "PT"},
            settings_updated_at="2026-10-11T20:00:00+00:00",
            records=[{"pn": "PN-1", "serial_number": "", "data": {}, "curve": None,
                      "updated_at": "2026-10-11T20:00:00", "deleted": False}],
            reports=[],
        )

        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/rpc/sync_curvsat_system_data"))
        self.assertEqual(request.get_header("Apikey"), "sb_publishable_Bm1QBy7tqNaffK2ozkmxJw_K15Oe8t3")
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(json.loads(request.data.decode("utf-8"))["p_records"][0]["pn"], "PN-1")
        self.assertEqual(remote["records"], [])

    @patch("curvsat.services.supabase.urlopen")
    def test_system_sync_accepts_legacy_wrapped_rpc_response(self, mocked_urlopen):
        mocked_urlopen.return_value = _Response([{
            "sync_curvsat_system_data": {"settings": None, "records": [], "reports": []}
        }])

        remote = sync_system_data(
            activation_code="CSAT-A1.exemplo.assinatura",
            settings={},
            settings_updated_at=None,
            records=[],
            reports=[],
        )

        self.assertEqual(remote["reports"], [])

    @patch("curvsat.services.supabase.urlopen")
    def test_sync_includes_postgrest_error_message(self, mocked_urlopen):
        mocked_urlopen.side_effect = HTTPError(
            "https://example.test/rpc/sync", 400, "Bad Request", {},
            __import__("io").BytesIO(b'{"message":"column \\"updated_at\\" does not exist"}'),
        )

        with self.assertRaisesRegex(RuntimeError, 'column "updated_at" does not exist'):
            sync_system_data(
                activation_code="CSAT-A1.exemplo.assinatura",
                settings={},
                settings_updated_at=None,
                records=[],
                reports=[],
            )


if __name__ == "__main__":
    unittest.main()
