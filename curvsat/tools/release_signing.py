"""Cria a chave local e assina manifestos de atualização do CurvSat."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from curvsat.security.release_signing import (
    generate_private_key_file,
    load_private_key,
    sign_manifest,
    verify_artifact,
    verify_manifest,
)
from curvsat.core.release_public_key import RELEASE_MANIFEST_PUBLIC_KEY


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEY_FILE = ROOT / "licensing" / "release_signing_private_key.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assinatura local de releases CurvSat.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-key", help="Cria a chave privada local uma única vez")
    create.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    sign = commands.add_parser("sign", help="Assina um manifesto com o hash do executável")
    sign.add_argument("--manifest", type=Path, default=ROOT / "update_manifest.json")
    sign.add_argument("--artifact", type=Path, required=True)
    sign.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    verify = commands.add_parser("verify", help="Valida a assinatura e o executável")
    verify.add_argument("--manifest", type=Path, default=ROOT / "update_manifest.json")
    verify.add_argument("--artifact", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "create-key":
        public_key, key_id = generate_private_key_file(args.key_file)
        print(f"Chave privada criada em: {args.key_file}")
        print(f"Chave pública (incorpore no aplicativo): {public_key}")
        print(f"Identificador da chave: {key_id}")
        return 0

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"ERRO: manifesto inválido: {error}") from error
    if not isinstance(manifest, dict):
        raise SystemExit("ERRO: o manifesto deve ser um objeto JSON.")
    if args.command == "verify":
        if not verify_manifest(manifest, RELEASE_MANIFEST_PUBLIC_KEY):
            raise SystemExit("ERRO: assinatura local do manifesto inválida.")
        if not verify_artifact(args.artifact, manifest):
            raise SystemExit("ERRO: executável diferente do artefato assinado.")
        print("Manifesto e executável verificados com sucesso.")
        return 0
    if not args.artifact.is_file() or args.artifact.stat().st_size == 0:
        raise SystemExit(f"ERRO: executável não encontrado ou vazio: {args.artifact}")
    signed = sign_manifest(manifest, args.artifact, load_private_key(args.key_file))
    args.manifest.write_text(json.dumps(signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifesto assinado: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
