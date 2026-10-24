"""Publica uma nova versao do CurvSat em um unico fluxo local."""

from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Mapping, NoReturn
from urllib.parse import urlsplit

from curvsat.core.release_public_key import RELEASE_MANIFEST_PUBLIC_KEY
from curvsat.security.release_signing import load_private_key, sign_manifest, verify_artifact, verify_manifest

ROOT = Path(__file__).resolve().parents[2]
APP_VERSION_FILE = ROOT / "curvsat" / "core" / "version.py"
MANIFEST_FILE = ROOT / "update_manifest.json"
SPEC_FILE = ROOT / "packaging" / "ASCC System.spec"
COMPILE_PARAMS_FILE = ROOT / "packaging" / "pyinstaller-params.txt"
VERSION_INFO_FILE = ROOT / "packaging" / "version_info.txt"
ENV_FILE = ROOT / ".release.env"
SIGNING_KEY_FILE = ROOT / "licensing" / "release_signing_private_key.json"
ARTIFACT_PREFIX = "ASCC-System"
DEFAULT_DOWNLOAD_BASE_URL = "https://merotec.online/download"
DEFAULT_UPLOAD_URL = "https://merotec.online/api/releases/upload"
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def fail(message: str) -> NoReturn:
    raise SystemExit(f"ERRO: {message}")


def read_release_environment() -> None:
    """Carrega pares KEY=VALUE locais, sem sobrescrever variaveis ja definidas."""
    if not ENV_FILE.exists():
        return
    for line_number, raw_line in enumerate(ENV_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail(f"{ENV_FILE.name}:{line_number} deve usar o formato CHAVE=VALOR.")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            fail(f"{ENV_FILE.name}:{line_number} possui uma chave invalida.")
        os.environ.setdefault(key, value.strip())


def validate_version(version: str) -> str:
    version = version.strip().removeprefix("v")
    if not VERSION_PATTERN.fullmatch(version):
        fail("A versao deve seguir o formato X.Y.Z, por exemplo 1.0.2.")
    return version


def version_key(version: str) -> tuple[int, int, int, int, str]:
    """Cria uma chave comparável para versões semânticas já validadas."""
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        fail(f"Versao invalida: {version}.")
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), 1 if prerelease is None else 0, prerelease or ""


def run(command: list[str], *, description: str) -> None:
    print(f"\n{description}...")
    print(" ".join(shlex.quote(part) for part in command))
    subprocess.run(command, cwd=ROOT, check=True)


def require_clean_tracked_worktree() -> None:
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        result = subprocess.run(["git", *args], cwd=ROOT, check=False)
        if result.returncode == 1:
            fail("Ha alteracoes rastreadas pendentes. Commit, guarde ou reverta-as antes de publicar.")
        if result.returncode != 0:
            fail("Nao foi possivel consultar o estado do Git.")


def replace_version(source: str, version: str, file_name: str) -> str:
    updated, count = re.subn(
        r"(?m)^(APP_VERSION\s*=\s*)[\"'][^\"']+[\"']$",
        rf'\g<1>"{version}"',
        source,
    )
    if count != 1:
        fail(f"Nao foi possivel localizar APP_VERSION em {file_name}.")
    return updated


def _source(path: Path, rendered: Mapping[Path, str] | None = None) -> str:
    if rendered is not None and path in rendered:
        return rendered[path]
    return path.read_text(encoding="utf-8")


def _app_version_from_source(source: str) -> str:
    match = re.search(r'(?m)^APP_VERSION\s*=\s*["\']([^"\']+)["\']$', source)
    if not match:
        fail(f"Nao foi possivel localizar APP_VERSION em {APP_VERSION_FILE.name}.")
    return validate_version(match.group(1))


def validate_release_state(version: str, rendered: Mapping[Path, str] | None = None) -> None:
    """Garante que código, manifesto e instruções de build apontam à mesma versão."""
    expected_name = f"{ARTIFACT_PREFIX}-{version}"

    app_version = _app_version_from_source(_source(APP_VERSION_FILE, rendered))
    if app_version != version:
        fail(f"{APP_VERSION_FILE.name} informa {app_version}, esperado {version}.")

    try:
        manifest = json.loads(_source(MANIFEST_FILE, rendered))
    except json.JSONDecodeError as error:
        fail(f"{MANIFEST_FILE.name} nao contem JSON valido: {error}.")
    if not isinstance(manifest, dict) or manifest.get("app") != "CurvSat":
        fail(f"{MANIFEST_FILE.name} nao contem um manifesto valido do CurvSat.")
    if str(manifest.get("version", "")).strip() != version:
        fail(f"{MANIFEST_FILE.name} informa uma versao diferente de {version}.")
    download_name = Path(urlsplit(str(manifest.get("download_url", ""))).path).name
    if download_name != f"{expected_name}.exe":
        fail(f"{MANIFEST_FILE.name} nao aponta para {expected_name}.exe.")
    if rendered is None and not verify_manifest(manifest, RELEASE_MANIFEST_PUBLIC_KEY):
        fail(f"{MANIFEST_FILE.name} nao possui uma assinatura local valida.")

    spec_source = _source(SPEC_FILE, rendered)
    if not re.search(rf"(?m)^\s*name='{re.escape(expected_name)}'", spec_source):
        fail(f"{SPEC_FILE.name} nao gera {expected_name}.exe.")
    if not re.search(r"(?m)^\s*version=str\(VERSION_INFO_FILE\),", spec_source):
        fail(f"{SPEC_FILE.name} nao incorpora {VERSION_INFO_FILE.name}.")

    version_info_source = _source(VERSION_INFO_FILE, rendered)
    version_tuple = ", ".join((*version.split("."), "0"))
    for field in ("filevers", "prodvers"):
        if f"{field}=({version_tuple})" not in version_info_source:
            fail(f"{VERSION_INFO_FILE.name} nao informa {field}={version_tuple}.")
    for field, value in {
        "FileVersion": version,
        "ProductVersion": version,
        "OriginalFilename": f"{expected_name}.exe",
    }.items():
        if f"StringStruct('{field}', '{value}')" not in version_info_source:
            fail(f"{VERSION_INFO_FILE.name} nao informa {field} corretamente.")
    for field in ("CompanyName", "FileDescription", "LegalCopyright", "ProductName"):
        if not re.search(rf"StringStruct\('{field}', '\S", version_info_source):
            fail(f"{VERSION_INFO_FILE.name} nao informa {field}.")

    compile_source = _source(COMPILE_PARAMS_FILE, rendered)
    if f'--name "{expected_name}"' not in compile_source:
        fail(f"{COMPILE_PARAMS_FILE.name} nao gera {expected_name}.exe.")
    if '--version-file "packaging/version_info.txt"' not in compile_source:
        fail(f"{COMPILE_PARAMS_FILE.name} nao incorpora {VERSION_INFO_FILE.name}.")


def render_release_files(version: str, notes: str, download_url: str) -> dict[Path, str]:
    app_version = replace_version(APP_VERSION_FILE.read_text(encoding="utf-8"), version, APP_VERSION_FILE.name)

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("app") != "CurvSat":
        fail("update_manifest.json nao contem um manifesto valido do CurvSat.")
    manifest.pop("artifact", None)
    manifest.pop("local_signature", None)
    manifest.update({"version": version, "release_notes": notes, "download_url": download_url})
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"

    executable_name = f"{ARTIFACT_PREFIX}-{version}"
    spec_source = SPEC_FILE.read_text(encoding="utf-8")
    spec_text, spec_count = re.subn(
        r"(?m)^(\s*name=')[^']+('.*)$", rf"\g<1>{executable_name}\g<2>", spec_source
    )
    if spec_count != 1:
        fail(f"Nao foi possivel atualizar o nome em {SPEC_FILE.name}.")

    compile_source = COMPILE_PARAMS_FILE.read_text(encoding="utf-8")
    compile_text, compile_count = re.subn(
        r'--name\s+"[^"]+"', f'--name "{executable_name}"', compile_source
    )
    if compile_count != 1:
        fail(f"Nao foi possivel atualizar --name em {COMPILE_PARAMS_FILE.name}.")

    version_info_source = VERSION_INFO_FILE.read_text(encoding="utf-8")
    version_parts = version.split(".")
    version_tuple = ", ".join((*version_parts, "0"))
    version_info_text = version_info_source
    for field in ("filevers", "prodvers"):
        version_info_text, count = re.subn(
            rf"(?m)^(\s*{field}=)\([^)]*\)(,)$",
            rf"\g<1>({version_tuple})\g<2>",
            version_info_text,
        )
        if count != 1:
            fail(f"Nao foi possivel atualizar {field} em {VERSION_INFO_FILE.name}.")
    for field, value in {
        "FileVersion": version,
        "ProductVersion": version,
        "OriginalFilename": f"{executable_name}.exe",
    }.items():
        version_info_text, count = re.subn(
            rf"(StringStruct\('{field}', ')[^']*('\))",
            rf"\g<1>{value}\g<2>",
            version_info_text,
        )
        if count != 1:
            fail(f"Nao foi possivel atualizar {field} em {VERSION_INFO_FILE.name}.")

    rendered = {
        APP_VERSION_FILE: app_version,
        MANIFEST_FILE: manifest_text,
        SPEC_FILE: spec_text,
        COMPILE_PARAMS_FILE: compile_text,
        VERSION_INFO_FILE: version_info_text,
    }
    validate_release_state(version, rendered)
    return rendered


def write_release_files(rendered: dict[Path, str]) -> None:
    for path, content in rendered.items():
        path.write_text(content, encoding="utf-8", newline="\n")


def upload_to_endpoint(upload_url: str, artifact: Path, version: str) -> None:
    """Envia o instalador sem depender de SCP, cliente HTTP externo ou shell."""
    parsed = urlsplit(upload_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        fail("CURVSAT_UPLOAD_URL deve ser uma URL HTTP/HTTPS valida.")

    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_class(parsed.hostname, parsed.port, timeout=300)
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(artifact.stat().st_size),
        "X-Release-Filename": artifact.name,
        "X-Release-Version": version,
    }
    print("\nEnviando instalador ao servidor...")
    print(f"PUT {upload_url}")
    try:
        connection.putrequest("PUT", target)
        for name, value in headers.items():
            connection.putheader(name, value)
        connection.endheaders()
        with artifact.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                connection.send(chunk)
        response = connection.getresponse()
        response_body = response.read(1024 * 1024).decode("utf-8", errors="replace").strip()
    except (OSError, http.client.HTTPException) as error:
        fail(f"Nao foi possivel enviar ao endpoint de upload: {error}")
    finally:
        connection.close()

    if not 200 <= response.status < 300:
        details = f": {response_body}" if response_body else ""
        fail(f"O endpoint recusou o instalador (HTTP {response.status}){details}")
    print(f"Endpoint confirmou o recebimento (HTTP {response.status}).")


def require_available_release_tag(version: str) -> str:
    """Evita sobrescrever ou republicar uma versão já identificada no Git."""
    tag = f"v{version}"
    local = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"], cwd=ROOT)
    if local.returncode == 0:
        fail(f"A tag local {tag} ja existe. Escolha uma nova versao.")
    if local.returncode != 1:
        fail("Nao foi possivel consultar as tags locais do Git.")

    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if remote.returncode == 0:
        fail(f"A tag remota {tag} ja existe. Escolha uma nova versao.")
    if remote.returncode != 2 and remote.returncode != 1:
        fail("Nao foi possivel consultar as tags remotas do Git.")
    return tag


def validate_artifact(artifact: Path) -> None:
    if not artifact.is_file() or artifact.stat().st_size == 0:
        fail(f"Executavel nao encontrado ou vazio: {artifact.relative_to(ROOT)}")


def sign_release_manifest(artifact: Path) -> None:
    """Assina o manifesto depois do build, vinculando-o ao hash do executável."""
    if not SIGNING_KEY_FILE.is_file():
        fail(
            "Chave de assinatura local ausente. Execute: "
            "python -m curvsat.tools.release_signing create-key"
        )
    try:
        manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        signed = sign_manifest(manifest, artifact, load_private_key(SIGNING_KEY_FILE))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        fail(f"Nao foi possivel assinar o manifesto: {error}")
    if not verify_manifest(signed, RELEASE_MANIFEST_PUBLIC_KEY):
        fail("A chave privada local nao corresponde a chave publica incorporada no aplicativo.")
    if not verify_artifact(artifact, signed):
        fail("A verificacao do executavel assinado falhou.")
    MANIFEST_FILE.write_text(json.dumps(signed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera e publica uma atualizacao do CurvSat.")
    parser.add_argument("version", help="Nova versao no formato X.Y.Z")
    parser.add_argument("--notes", required=True, help="Notas exibidas ao usuario")
    parser.add_argument("--no-build", action="store_true", help="Nao recompila o executavel")
    parser.add_argument("--no-push", action="store_true", help="Cria o commit, mas nao envia ao GitHub")
    parser.add_argument("--skip-tests", action="store_true", help="Nao executa os testes automatizados antes do build")
    parser.add_argument("--dry-run", action="store_true", help="Valida o fluxo sem modificar ou publicar arquivos")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    version = validate_version(args.version)
    notes = args.notes.strip()
    if not notes:
        fail("As notas da atualizacao nao podem ficar vazias.")

    read_release_environment()
    download_base_url = os.environ.get("CURVSAT_DOWNLOAD_BASE_URL", DEFAULT_DOWNLOAD_BASE_URL).rstrip("/")
    artifact_name = f"{ARTIFACT_PREFIX}-{version}.exe"
    download_url = f"{download_base_url}/{artifact_name}"
    upload_url = os.environ.get("CURVSAT_UPLOAD_URL", DEFAULT_UPLOAD_URL).strip() or DEFAULT_UPLOAD_URL

    if args.dry_run:
        current_version = _app_version_from_source(APP_VERSION_FILE.read_text(encoding="utf-8"))
        validate_release_state(current_version)
        if version_key(version) <= version_key(current_version):
            fail(f"A nova versao deve ser maior que a atual ({current_version}).")
        render_release_files(version, notes, download_url)
        print(f"Fluxo valido para {artifact_name} -> {download_url}")
        return 0
    require_clean_tracked_worktree()
    current_version = _app_version_from_source(APP_VERSION_FILE.read_text(encoding="utf-8"))
    validate_release_state(current_version)
    if version_key(version) <= version_key(current_version):
        fail(f"A nova versao deve ser maior que a atual ({current_version}).")
    tag = require_available_release_tag(version)
    if not args.skip_tests:
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], description="Executando testes")
    rendered = render_release_files(version, notes, download_url)
    originals = {path: path.read_text(encoding="utf-8") for path in rendered}
    try:
        write_release_files(rendered)
        artifact = ROOT / "dist" / artifact_name
        if not args.no_build:
            run([sys.executable, "-m", "PyInstaller", "--noconfirm", str(SPEC_FILE.relative_to(ROOT))], description="Gerando executavel")
        validate_artifact(artifact)
        sign_release_manifest(artifact)
        validate_release_state(version)
        upload_to_endpoint(upload_url, artifact, version)
    except BaseException:
        write_release_files(originals)
        raise

    release_files = [str(path.relative_to(ROOT)) for path in rendered]
    run(["git", "add", *release_files], description="Preparando arquivos da versao")
    run(["git", "commit", "-m", f"Publica atualizacao {version}"], description="Registrando publicacao")
    run(["git", "tag", "-a", tag, "-m", f"Publica atualizacao {version}"], description="Marcando versao no Git")
    if not args.no_push:
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
        if not branch:
            fail("Nao foi possivel identificar a branch atual para envio ao GitHub.")
        run(["git", "push", "origin", branch], description="Enviando manifesto ao GitHub")
        run(["git", "push", "origin", tag], description="Enviando tag da versao ao GitHub")

    print(f"\nPublicacao concluida: {artifact_name}")
    print(f"Download: {download_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
