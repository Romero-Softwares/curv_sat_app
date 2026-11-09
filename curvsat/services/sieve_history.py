"""Persistência local e consulta de análises granulométricas."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from curvsat.content.translations import tr
from curvsat.core.paths import user_data_file


def formatar_data_historico(data_analise: str) -> str:
    """Converte a data técnica do banco para a convenção exibida na interface."""
    try:
        return datetime.fromisoformat(str(data_analise)).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return str(data_analise)


class HistoricoAnalisesPeneiras:
    """Arquiva análises de peneiras em SQLite no perfil local do usuário."""

    _CODIGO_VALIDO = re.compile(r"[A-Z0-9_-]{3,32}")

    def __init__(self, arquivo: Path | str | None = None, language: str = "PT"):
        self.arquivo = Path(arquivo) if arquivo is not None else user_data_file("analises_peneiras.db")
        self.language = language
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self._criar_estrutura()

    @contextmanager
    def _conectar(self) -> Iterator[sqlite3.Connection]:
        conexao = sqlite3.connect(self.arquivo)
        conexao.row_factory = sqlite3.Row
        try:
            yield conexao
            conexao.commit()
        finally:
            conexao.close()

    def _criar_estrutura(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS analises_peneiras (
                    codigo TEXT PRIMARY KEY,
                    data_analise TEXT NOT NULL,
                    designacao TEXT NOT NULL,
                    tipo_amostra TEXT NOT NULL,
                    situacao TEXT NOT NULL,
                    massa_total_g REAL NOT NULL,
                    massas_json TEXT NOT NULL,
                    resultado_json TEXT NOT NULL
                )
                """
            )
            conexao.execute(
                "CREATE INDEX IF NOT EXISTS idx_analises_peneiras_data ON analises_peneiras(data_analise DESC)"
            )
            conexao.execute(
                "CREATE INDEX IF NOT EXISTS idx_analises_peneiras_situacao ON analises_peneiras(situacao)"
            )

    @staticmethod
    def situacao_do_resultado(resultado: dict) -> str:
        if not resultado.get("massa_conforme"):
            return "invalida"
        if resultado.get("criterios_normativos_aplicaveis"):
            return "conforme" if resultado.get("conforme") else "nao_conforme"
        return "conforme" if resultado.get("midia_em_uso_conforme") else "nao_conforme"

    def _proximo_codigo(self, conexao: sqlite3.Connection) -> str:
        maior = conexao.execute(
            "SELECT MAX(CAST(SUBSTR(codigo, 2) AS INTEGER)) FROM analises_peneiras "
            "WHERE codigo GLOB 'P[0-9]*'"
        ).fetchone()[0]
        return f"P{int(maior or 0) + 1:06d}"

    def salvar(self, resultado: dict, massas: dict, codigo: str = "", data_analise: datetime | None = None) -> dict:
        """Salva o resultado completo e retorna o registro criado.

        Um código vazio recebe o próximo identificador sequencial ``P000001``.
        Códigos informados pelo usuário são preservados, desde que únicos.
        """
        codigo = str(codigo or "").strip().upper()
        momento = data_analise or datetime.now()
        data_texto = momento.strftime("%Y-%m-%d %H:%M:%S")
        situacao = self.situacao_do_resultado(resultado)
        registro = {
            "codigo": codigo,
            "data_analise": data_texto,
            "designacao": str(resultado["designacao"]),
            "tipo_amostra": str(resultado["tipo_amostra"]),
            "situacao": situacao,
            "massa_total_g": float(resultado["massa_total_g"]),
            "massas": massas,
            "resultado": resultado,
        }
        with self._conectar() as conexao:
            if not codigo:
                registro["codigo"] = self._proximo_codigo(conexao)
            elif not self._CODIGO_VALIDO.fullmatch(codigo):
                raise ValueError(tr("sieve_invalid_code", self.language))
            try:
                conexao.execute(
                    """
                    INSERT INTO analises_peneiras (
                        codigo, data_analise, designacao, tipo_amostra, situacao,
                        massa_total_g, massas_json, resultado_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        registro["codigo"], registro["data_analise"], registro["designacao"],
                        registro["tipo_amostra"], registro["situacao"], registro["massa_total_g"],
                        json.dumps(massas, ensure_ascii=False), json.dumps(resultado, ensure_ascii=False),
                    ),
                )
            except sqlite3.IntegrityError as erro:
                raise ValueError(tr("sieve_duplicate_code", self.language, code=registro["codigo"])) from erro
        return registro

    def _normalizar_data(self, data: str) -> str:
        data = str(data or "").strip()
        if not data:
            return ""
        for formato in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(data, formato).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(tr("sieve_invalid_date", self.language))

    def buscar(self, codigo: str = "", data: str = "", situacao: str = "", limite: int = 12) -> list[dict]:
        """Busca por código, data e situação, mais recentes primeiro."""
        filtros: list[str] = []
        valores: list[object] = []
        if codigo := str(codigo or "").strip().upper():
            filtros.append("codigo LIKE ?")
            valores.append(f"%{codigo}%")
        if data_normalizada := self._normalizar_data(data):
            filtros.append("data_analise LIKE ?")
            valores.append(f"{data_normalizada}%")
        if situacao := str(situacao or "").strip().lower():
            filtros.append("situacao = ?")
            valores.append(situacao)
        clausula = f" WHERE {' AND '.join(filtros)}" if filtros else ""
        with self._conectar() as conexao:
            linhas = conexao.execute(
                "SELECT * FROM analises_peneiras" + clausula + " ORDER BY data_analise DESC LIMIT ?",
                [*valores, max(1, int(limite))],
            ).fetchall()
        registros = []
        for linha in linhas:
            registro = dict(linha)
            registro["massas"] = json.loads(registro.pop("massas_json"))
            registro["resultado"] = json.loads(registro.pop("resultado_json"))
            registros.append(registro)
        return registros
