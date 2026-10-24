"""Conteúdo técnico localizado para a consulta de shot peening."""

from __future__ import annotations

from curvsat.content.translations import technical_content


def dados_tecnicos(language: str | None = None) -> dict:
    """Retorna títulos, colunas, linhas e aviso no idioma solicitado."""
    return technical_content(language)


# Compatibilidade para importadores existentes. A interface sempre chama
# ``dados_tecnicos`` ao abrir a janela, portanto acompanha o idioma atual.
_PADRAO = dados_tecnicos("PT")
ANALISE_ESFERAS = _PADRAO["analysis"][3]
GRANULOMETRIA_ESFERAS = _PADRAO["grain"][3]
TIPOS_MIDIA = _PADRAO["media"][3]
NORMAS_REFERENCIA = _PADRAO["standards"][3]
AVISO_TECNICO = _PADRAO["notice"]
