"""Cálculo de distribuição granulométrica de esfera por peneiras.

Os critérios abaixo reproduzem a sequência de peneiras e os limites de
aceitação da SAE J444 (J444_202306) para esfera de aço fundido. A revisão
contratual da norma e o certificado do lote continuam prevalecendo sobre este
apoio de cálculo.

A SAE J444 requer um fundo (pan) sob a última peneira para coletar e registrar
o material passante. O fundo não possui um limite autônomo: sua massa é,
necessariamente, o percentual passante pela última peneira e já é avaliada
pelo limite cumulativo dessa peneira.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from curvsat.content.translations import tr


MASSA_AMOSTRA_G = 100.0
TOLERANCIA_MASSA_G = 0.1
TIPOS_AMOSTRA = ("nova", "usada")
LIMITE_MIDIA_EM_USO_RETIDA_MAX = 0.5
LIMITE_MIDIA_EM_USO_PASSANTE_MAX = 20.0


@dataclass(frozen=True)
class CriterioPeneira:
    numero: int
    abertura_mm: float
    tipo: str
    limite: float


@dataclass(frozen=True)
class LimitesMidiaEmUso:
    """Limites de manutenção da granulometria da mídia em operação.

    A AMS 2430 define, para cada tamanho de mídia, uma peneira superior com
    máximo de 0,5% retido e uma peneira inferior com máximo de 20% passante.
    A aplicação desses limites depende da revisão exigida pelo contrato ou
    procedimento aplicável ao processo.
    """

    peneira_retida_max: int
    peneira_passante_max: int


# Ordem: peneira mais grossa para a mais fina. ``retida_max`` controla a
# fração retida naquela peneira e ``retida_acumulada_min`` controla a fração
# acumulada retida até ela. A SAE J444 publica os requisitos mínimos como
# percentuais cumulativos retidos ("min on screen"). Na #30, por exemplo,
# soma-se o material retido na #30 e em todas as peneiras mais grossas. Assim,
# S230 exige 85% retidos até a #30 (no máximo 15% passam por ela) e 97% retidos
# até a #35 (no máximo 3% passam pela #35 e são coletados no fundo). Esse
# último valor não é um segundo critério; é a expressão do próprio limite da
# última peneira.
CRITERIOS_SAE_J444: dict[str, tuple[CriterioPeneira, ...]] = {
    "S70": (
        CriterioPeneira(40, 0.425, "retida_max", 0),
        CriterioPeneira(45, 0.355, "retida_max", 10),
        CriterioPeneira(80, 0.180, "retida_acumulada_min", 80),
        CriterioPeneira(120, 0.125, "retida_acumulada_min", 90),
    ),
    "S110": (
        CriterioPeneira(30, 0.600, "retida_max", 0),
        CriterioPeneira(35, 0.500, "retida_max", 10),
        CriterioPeneira(50, 0.300, "retida_acumulada_min", 80),
        CriterioPeneira(80, 0.180, "retida_acumulada_min", 90),
    ),
    "S170": (
        CriterioPeneira(20, 0.850, "retida_max", 0),
        CriterioPeneira(25, 0.710, "retida_max", 10),
        CriterioPeneira(40, 0.425, "retida_acumulada_min", 85),
        CriterioPeneira(45, 0.355, "retida_acumulada_min", 97),
    ),
    "S230": (
        CriterioPeneira(18, 1.000, "retida_max", 0),
        CriterioPeneira(20, 0.850, "retida_max", 10),
        CriterioPeneira(30, 0.600, "retida_acumulada_min", 85),
        CriterioPeneira(35, 0.500, "retida_acumulada_min", 97),
    ),
    "S280": (
        CriterioPeneira(16, 1.180, "retida_max", 0),
        CriterioPeneira(18, 1.000, "retida_max", 5),
        CriterioPeneira(25, 0.710, "retida_acumulada_min", 85),
        CriterioPeneira(30, 0.600, "retida_acumulada_min", 96),
    ),
    "S330": (
        CriterioPeneira(14, 1.400, "retida_max", 0),
        CriterioPeneira(16, 1.180, "retida_max", 5),
        CriterioPeneira(20, 0.850, "retida_acumulada_min", 85),
        CriterioPeneira(25, 0.710, "retida_acumulada_min", 96),
    ),
    "S390": (
        CriterioPeneira(12, 1.700, "retida_max", 0),
        CriterioPeneira(14, 1.400, "retida_max", 5),
        CriterioPeneira(18, 1.000, "retida_acumulada_min", 85),
        CriterioPeneira(20, 0.850, "retida_acumulada_min", 96),
    ),
    "S460": (
        CriterioPeneira(10, 2.000, "retida_max", 0),
        CriterioPeneira(12, 1.700, "retida_max", 5),
        CriterioPeneira(16, 1.180, "retida_acumulada_min", 85),
        CriterioPeneira(18, 1.000, "retida_acumulada_min", 96),
    ),
    "S550": (
        CriterioPeneira(10, 2.000, "retida_max", 0),
        CriterioPeneira(14, 1.400, "retida_acumulada_min", 85),
        CriterioPeneira(16, 1.180, "retida_acumulada_min", 97),
    ),
    "S660": (
        CriterioPeneira(8, 2.360, "retida_max", 0),
        CriterioPeneira(12, 1.700, "retida_acumulada_min", 85),
        CriterioPeneira(14, 1.400, "retida_acumulada_min", 97),
    ),
    "S780": (
        CriterioPeneira(7, 2.800, "retida_max", 0),
        CriterioPeneira(10, 2.000, "retida_acumulada_min", 85),
        CriterioPeneira(12, 1.700, "retida_acumulada_min", 97),
    ),
}


# Peneiras ASTM E11 da tabela de análise de mídia em processo da AMS 2430.
# A primeira limita material grosseiro retido; a segunda limita finos passantes.
LIMITES_AMS2430_MIDIA_EM_USO: dict[str, LimitesMidiaEmUso] = {
    "S70": LimitesMidiaEmUso(40, 80),
    "S110": LimitesMidiaEmUso(35, 50),
    "S170": LimitesMidiaEmUso(25, 40),
    "S230": LimitesMidiaEmUso(18, 30),
    "S280": LimitesMidiaEmUso(16, 25),
    "S330": LimitesMidiaEmUso(14, 20),
    "S390": LimitesMidiaEmUso(12, 18),
    "S460": LimitesMidiaEmUso(10, 16),
    "S550": LimitesMidiaEmUso(8, 14),
    "S660": LimitesMidiaEmUso(7, 12),
    "S780": LimitesMidiaEmUso(6, 10),
}


# Peneiras de controle AMS 2430 que não fazem parte da pilha J444 de mídia
# nova para algumas designações. As aberturas seguem ASTM E11.
ABERTURAS_ADICIONAIS_ASTME11: dict[int, float] = {
    6: 3.350,
    7: 2.800,
    8: 2.360,
}


def peneiras_para_designacao(designacao: str, language: str = "PT") -> tuple[CriterioPeneira, ...]:
    """Retorna as peneiras ASTM E11 aplicáveis à designação SAE informada."""
    try:
        return CRITERIOS_SAE_J444[str(designacao).strip().upper()]
    except KeyError as error:
        raise ValueError(tr("sieve_unsupported_j444", language, designation=designacao)) from error


def peneira_nominal_para_designacao(designacao: str) -> CriterioPeneira:
    """Retorna a peneira nominal usada como referência da mistura operacional.

    Na sequência da J444, ela é a primeira peneira cuja exigência para a
    mídia nova é expressa como percentual acumulado retido. Por exemplo,
    para S230 é a peneira #30 (0,600 mm).
    """
    return next(
        criterio
        for criterio in peneiras_para_designacao(designacao)
        if criterio.tipo == "retida_acumulada_min"
    )


def limites_midia_em_uso_para_designacao(designacao: str, language: str = "PT") -> LimitesMidiaEmUso:
    """Retorna as peneiras de controle AMS 2430 da mídia em uso."""
    codigo = str(designacao).strip().upper()
    try:
        return LIMITES_AMS2430_MIDIA_EM_USO[codigo]
    except KeyError as error:
        raise ValueError(tr("sieve_unsupported_ams2430", language, designation=designacao)) from error


def peneiras_para_analise(
    designacao: str, *, tipo_amostra: object = "nova", language: str = "PT"
) -> tuple[CriterioPeneira, ...]:
    """Retorna a pilha de peneiras necessária à condição analisada.

    Para mídia usada, inclui as peneiras extras exigidas pela AMS 2430 quando
    elas não estão presentes na sequência SAE J444 de mídia nova.
    """
    tipo = normalizar_tipo_amostra(tipo_amostra, language)
    criterios = peneiras_para_designacao(designacao, language)
    if tipo == "nova":
        return criterios

    limites = limites_midia_em_uso_para_designacao(designacao, language)
    existentes = {criterio.numero for criterio in criterios}
    extras = []
    for numero in (limites.peneira_retida_max, limites.peneira_passante_max):
        if numero not in existentes:
            extras.append(CriterioPeneira(numero, ABERTURAS_ADICIONAIS_ASTME11[numero], "registro", 0))
    return tuple(sorted((*criterios, *extras), key=lambda criterio: criterio.abertura_mm, reverse=True))


def normalizar_tipo_amostra(tipo_amostra: object, language: str = "PT") -> str:
    """Normaliza a condição da mídia para definir o critério aplicável.

    A SAE J444 classifica a granulometria de mídia nova adquirida. Para mídia
    usada, o cálculo aplica os parâmetros de manutenção AMS 2430, separados
    da aprovação de compra pela J444.
    """
    valor = str(tipo_amostra).strip().lower()
    aliases = {
        "nova": "nova",
        "novo": "nova",
        "new": "nova",
        "usada": "usada",
        "usado": "usada",
        "used": "usada",
        "operacional": "usada",
        "operating": "usada",
    }
    try:
        return aliases[valor]
    except KeyError as error:
        raise ValueError(tr("sieve_invalid_sample_type", language)) from error


def _massa_entrada(
    massas_retidas: Mapping[object, object], chave: object, language: str = "PT"
) -> float:
    valor = massas_retidas.get(chave, massas_retidas.get(str(chave), 0.0))
    try:
        massa = float(valor)
    except (TypeError, ValueError) as error:
        raise ValueError(tr("sieve_invalid_mass", language, sieve=chave, value=valor)) from error
    if not isfinite(massa) or massa < 0:
        raise ValueError(tr("sieve_nonnegative_mass", language, sieve=chave))
    return massa


def analisar_amostra_peneiras(
    designacao: str,
    massas_retidas: Mapping[object, object],
    *,
    massa_fundo: object | None = None,
    tipo_amostra: object = "nova",
    language: str = "PT",
) -> dict:
    """Calcula percentuais e conformidade de uma amostra nominal de 100 g.

    ``massas_retidas`` recebe a massa em gramas retida em cada número de
    peneira. ``massa_fundo`` é a massa coletada no fundo da pilha. Os
    percentuais são normalizados pela massa informada, mas o resultado somente
    é aprovado quando o total confere 100,0 g (±0,1 g), evitando mascarar perda
    ou contaminação da amostra.
    """
    tipo = normalizar_tipo_amostra(tipo_amostra, language)
    criterios_normativos_aplicaveis = tipo == "nova"
    criterios = peneiras_para_analise(designacao, tipo_amostra=tipo, language=language)
    limites_midia_em_uso = limites_midia_em_uso_para_designacao(designacao, language)
    retidas = {
        criterio.numero: _massa_entrada(massas_retidas, criterio.numero, language)
        for criterio in criterios
    }
    fundo = _massa_entrada(
        {"fundo": massa_fundo if massa_fundo is not None else massas_retidas.get("fundo", 0)},
        "fundo",
        language,
    )
    total = sum(retidas.values()) + fundo
    if total <= 0:
        raise ValueError(tr("sieve_empty_mass", language))

    linhas = []
    acumulada_retida = 0.0
    for criterio in criterios:
        massa = retidas[criterio.numero]
        acumulada_retida += massa
        percentual_retido = massa * 100.0 / total
        percentual_retido_acumulado = acumulada_retida * 100.0 / total
        percentual_passante = 100.0 - percentual_retido_acumulado
        if criterio.tipo == "retida_max":
            valor_avaliado = percentual_retido
            limite_texto = tr("sieve_limite_retida", language, limite=criterio.limite)
            conforme = valor_avaliado <= criterio.limite + 1e-9
        elif criterio.tipo == "retida_acumulada_min":
            valor_avaliado = percentual_retido_acumulado
            limite_passante = 100.0 - criterio.limite
            limite_texto = tr(
                "sieve_limite_acumulada",
                language,
                limite=criterio.limite,
                passante=limite_passante,
            )
            conforme = valor_avaliado + 1e-9 >= criterio.limite
        else:
            valor_avaliado = percentual_retido
            limite_texto = tr("sieve_registro_distribuicao", language)
            conforme = True
        linhas.append({
            "peneira": criterio.numero,
            "abertura_mm": criterio.abertura_mm,
            "massa_retida_g": massa,
            "percentual_retido": percentual_retido,
            "percentual_retido_acumulado": percentual_retido_acumulado,
            "percentual_passante": percentual_passante,
            "tipo_criterio": criterio.tipo,
            "criterio_j444": criterio.tipo != "registro",
            "valor_avaliado": valor_avaliado,
            "limite": criterio.limite,
            "limite_passante_max": 100.0 - criterio.limite if criterio.tipo == "retida_acumulada_min" else None,
            "limite_texto": limite_texto,
            "conforme_j444": conforme,
            "conforme": conforme if criterios_normativos_aplicaveis else None,
            "criterio_midia_em_uso_aplicavel": criterio.numero in (
                limites_midia_em_uso.peneira_retida_max,
                limites_midia_em_uso.peneira_passante_max,
            ),
            "limite_midia_em_uso_texto": (
                tr("sieve_limite_usada_retida", language)
                if criterio.numero == limites_midia_em_uso.peneira_retida_max
                else (
                    tr("sieve_limite_usada_passante", language)
                    if criterio.numero == limites_midia_em_uso.peneira_passante_max
                    else tr("sieve_registro_distribuicao", language)
                )
            ),
            "conforme_midia_em_uso": None,
        })

    massa_conforme = abs(total - MASSA_AMOSTRA_G) <= TOLERANCIA_MASSA_G
    criterios_j444_conformes = all(
        linha["conforme_j444"] for linha in linhas if linha["criterio_j444"]
    )
    criterios_conformes = criterios_j444_conformes if criterios_normativos_aplicaveis else None
    linha_retida_max = None
    linha_passante_max = None
    midia_em_uso_conforme = None
    if tipo == "usada":
        linha_retida_max = next(
            linha for linha in linhas if linha["peneira"] == limites_midia_em_uso.peneira_retida_max
        )
        linha_passante_max = next(
            linha for linha in linhas if linha["peneira"] == limites_midia_em_uso.peneira_passante_max
        )
        retida_max_conforme = (
            linha_retida_max["percentual_retido"] <= LIMITE_MIDIA_EM_USO_RETIDA_MAX + 1e-9
        )
        passante_max_conforme = (
            linha_passante_max["percentual_passante"] <= LIMITE_MIDIA_EM_USO_PASSANTE_MAX + 1e-9
        )
        linha_retida_max["conforme_midia_em_uso"] = retida_max_conforme
        linha_passante_max["conforme_midia_em_uso"] = passante_max_conforme
        midia_em_uso_conforme = retida_max_conforme and passante_max_conforme
    ultima_linha = linhas[-1]
    ultimo_criterio = criterios[-1]
    # Mantido para compatibilidade de consumidores existentes: o valor é
    # derivado do limite da última peneira, e não um critério próprio do fundo.
    fundo_limite_max = 100.0 - ultimo_criterio.limite
    return {
        "designacao": str(designacao).strip().upper(),
        "tipo_amostra": tipo,
        "criterios_normativos_aplicaveis": criterios_normativos_aplicaveis,
        "massa_total_g": total,
        "massa_fundo_g": fundo,
        "percentual_fundo": fundo * 100.0 / total,
        "fundo_limite_max": fundo_limite_max,
        "fundo_conforme": ultima_linha["conforme"] if criterios_normativos_aplicaveis else None,
        "fundo_criterio_independente": False,
        "fundo_referencia_peneira": ultimo_criterio.numero,
        "massa_conforme": massa_conforme,
        "criterios_j444_conformes": criterios_j444_conformes,
        "criterios_conformes": criterios_conformes,
        "conforme": massa_conforme and criterios_conformes if criterios_normativos_aplicaveis else None,
        "peneira_retida_max_midia_em_uso": limites_midia_em_uso.peneira_retida_max,
        "peneira_passante_max_midia_em_uso": limites_midia_em_uso.peneira_passante_max,
        "percentual_retido_peneira_retida_max": linha_retida_max["percentual_retido"] if linha_retida_max else None,
        "percentual_passante_peneira_passante_max": linha_passante_max["percentual_passante"] if linha_passante_max else None,
        "limite_midia_em_uso_retida_max": LIMITE_MIDIA_EM_USO_RETIDA_MAX,
        "limite_midia_em_uso_passante_max": LIMITE_MIDIA_EM_USO_PASSANTE_MAX,
        "midia_em_uso_conforme": midia_em_uso_conforme,
        "linhas": linhas,
    }
