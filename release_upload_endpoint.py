"""Endpoint FastAPI para receber instaladores publicados pelo ``release_update.py``.

No servidor que ja possui ``routes.py``, importe ``install_release_upload_endpoint``
e chame a funcao logo depois de criar a aplicacao FastAPI. O endpoint recebe o
binario por streaming e faz a troca do arquivo de forma atomica.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Optional, Union
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status


ARTIFACT_NAME = re.compile(r"^ASCC-System-\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\.exe$")
DEFAULT_MAX_BYTES = 500 * 1024 * 1024


def _max_upload_bytes() -> int:
    value = os.environ.get("CURVSAT_UPLOAD_MAX_BYTES", str(DEFAULT_MAX_BYTES))
    try:
        maximum = int(value)
    except ValueError as error:
        raise RuntimeError("CURVSAT_UPLOAD_MAX_BYTES deve ser um numero inteiro.") from error
    if maximum <= 0:
        raise RuntimeError("CURVSAT_UPLOAD_MAX_BYTES deve ser maior que zero.")
    return maximum


def install_release_upload_endpoint(
    app: FastAPI,
    download_directory: Optional[Union[Path, str]] = None,
) -> None:
    """Registra ``PUT /api/releases/upload`` e grava o instalador em ``assets/``."""
    target_directory = Path(
        download_directory
        or os.environ.get("CURVSAT_DOWNLOAD_DIR", Path(__file__).resolve().parent / "assets")
    ).resolve()

    @app.put("/api/releases/upload", status_code=status.HTTP_201_CREATED)
    async def upload_release(request: Request) -> dict[str, Union[str, int]]:
        filename = request.headers.get("x-release-filename", "")
        if not ARTIFACT_NAME.fullmatch(filename):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome de instalador invalido.")
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/octet-stream":
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Envie o instalador como binario.")

        declared_size = request.headers.get("content-length")
        maximum = _max_upload_bytes()
        if declared_size:
            try:
                if int(declared_size) > maximum:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Instalador excede o limite.")
            except ValueError as error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content-Length invalido.") from error

        target_directory.mkdir(parents=True, exist_ok=True)
        destination = target_directory / filename
        temporary = target_directory / f".{filename}.{uuid4().hex}.upload"
        size = 0
        try:
            with temporary.open("xb") as output:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > maximum:
                        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Instalador excede o limite.")
                    output.write(chunk)
            temporary.replace(destination)
        except HTTPException:
            temporary.unlink(missing_ok=True)
            raise
        except OSError as error:
            temporary.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao gravar instalador.") from error

        return {"filename": filename, "bytes": size, "status": "uploaded"}
