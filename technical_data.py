"""Dados de consulta técnica para mídia de shot peening.

Os valores abaixo facilitam a identificação inicial da mídia. A aprovação de
um lote deve considerar a norma aplicável, o certificado do fornecedor e o
plano de controle do processo.
"""

from __future__ import annotations


ANALISE_ESFERAS = (
    ("Identificação", "Tipo, lote, fabricante e certificado", "Mantém a rastreabilidade da mídia usada."),
    ("Granulometria", "Ensaio por peneiras ASTM E11", "Confirma a distribuição e a designação SAE J444."),
    ("Forma", "Esfericidade, partículas quebradas e satélites", "Evita impacto irregular e acabamento inconsistente."),
    ("Dureza", "Faixa especificada para a mídia", "Influencia a energia transferida e a vida útil da esfera."),
    ("Composição", "Análise química conforme especificação", "Confirma o material, como aço fundido de alto carbono."),
    ("Integridade", "Trincas, porosidade, contaminação e oxidação", "Reduz risco de quebra e contaminação da peça."),
    ("Desempenho", "Teste mecânico / vida Ervin quando requerido", "Compara durabilidade e energia transmitida pela mídia."),
)


# Em SAE J444, a designação S corresponde à abertura nominal de peneira em
# dez-milésimos de polegada. Os milímetros são a conversão dessa abertura.
GRANULOMETRIA_ESFERAS = (
    ("S70", "0.0070", "0,178", "Fina"),
    ("S110", "0.0110", "0,279", "Fina"),
    ("S170", "0.0170", "0,432", "Média"),
    ("S230", "0.0230", "0,584", "Média"),
    ("S280", "0.0280", "0,711", "Média"),
    ("S330", "0.0330", "0,838", "Média"),
    ("S390", "0.0390", "0,991", "Grossa"),
    ("S460", "0.0460", "1,168", "Grossa"),
    ("S550", "0.0550", "1,397", "Grossa"),
    ("S660", "0.0660", "1,676", "Muito grossa"),
    ("S780", "0.0780", "1,981", "Muito grossa"),
)


TIPOS_MIDIA = (
    ("Esfera de aço fundido alto carbono", "S + designação", "SAE J827 e SAE J444", "Shot peening e limpeza."),
    ("Esfera de aço fundido baixo carbono", "S + designação", "SAE J2175 e SAE J444", "Quando a especificação exigir baixa dureza/carbono."),
    ("Arame cortado condicionado", "Diâmetro nominal", "SAE J441", "Mídia metálica de alta durabilidade."),
    ("Granalha angular de aço (grit)", "G + designação", "SAE J1993 e SAE J444", "Limpeza, decapagem e ancoragem; não substitui esfera sem aprovação."),
    ("Esfera de vidro ou cerâmica", "Conforme fornecedor", "Especificação do processo", "Mídias não metálicas para aplicações definidas."),
)


NORMAS_REFERENCIA = (
    ("SAE J444", "Classificação de tamanhos de esfera e granalha fundidas", "Define designações S/G e controle por peneiras."),
    ("SAE J827", "Esfera de aço fundido de alto carbono", "Composição e características físicas da esfera."),
    ("SAE J2175", "Esfera de aço fundido de baixo carbono", "Requisitos de composição, dureza, microestrutura e características físicas."),
    ("SAE J441", "Arame cortado", "Guia para seleção e uso de shot de arame cortado."),
    ("SAE J1993", "Granalha de aço fundido alto carbono", "Requisitos para grit usado em limpeza e ataque superficial."),
    ("SAE J445", "Teste mecânico de esfera e granalha metálicas", "Métodos laboratoriais para avaliar a mídia."),
    ("SAE J442", "Lâmina, suporte e medidor Almen", "Equipamentos e suprimentos para medição de flecha."),
    ("SAE J443", "Determinação e verificação da intensidade", "Curva de saturação e uso das lâminas Almen."),
    ("SAE J2277", "Cobertura de shot peening", "Método para determinar a cobertura do processo."),
    ("SAE J2597", "Curvas de saturação geradas por computador", "Orientação para curvas de saturação assistidas por software."),
    ("AMS2430 / AMS2431", "Processo e aquisição de mídia aeroespacial", "Aplicar somente quando exigido pelo desenho, contrato ou cliente."),
)


AVISO_TECNICO = (
    "Consulta técnica: confirme sempre a revisão vigente da norma e os limites de aceitação "
    "no certificado do lote, desenho da peça e procedimento aprovado."
)
