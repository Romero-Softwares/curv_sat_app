"""Textos da interface e preferência persistente de idioma.

As chaves permanecem estáveis e independentes do idioma para que os dados
salvos no banco local continuem compatíveis quando a interface for alterada.
"""

from __future__ import annotations

import json

from app_paths import user_data_file


LANGUAGES = {
    "PT": "🇧🇷 PT",
    "EN": "🇺🇸 EN",
    "ES": "🇪🇸 SP",
}
DEFAULT_LANGUAGE = "PT"
_SETTINGS_FILE = user_data_file("configuracoes.json")

_TEXTS = {
    "PT": {
        "app_title": "Calculador de Curva de Saturação Almen",
        "measurements": "Medições da Lâmina Almen", "add_row": "+ Linha", "remove_row": "- Linha",
        "example": "Exemplo", "settings": "Configurações", "calculate": "Calcular e Gerar Gráfico",
        "generate_report": "Gerar relatório", "print_chart": "Imprimir gráfico", "technical_tables": "Tabelas técnicas",
        "system_references": "REFERÊNCIAS NORMATIVAS DO SISTEMA", "exposure": "Exposição",
        "arc_height": "Altura da flecha", "blade_deviation": "Lâmina / desvio", "no_deviation": "Sem desvio",
        "saturation_time": "Tempo de saturação (T)", "intensity": "Intensidade H(T)", "point_2t": "Ponto (2T)",
        "height_2t": "Altura H(2T)", "fit": "Ajuste R²", "deviations": "Desvios", "none_applied": "nenhum aplicado",
        "chart_title": "Curva de Saturação Almen", "measured_points": "Pontos medidos compensados",
        "fitted_curve": "Curva ajustada ($R^2={r2:.3f}$)", "saturation_point": "Saturação T ({value:.2f} {unit})",
        "row_incomplete": "Preencha exposição e flecha na linha {index}.", "invalid_numbers": "Use números válidos na linha {index}.",
        "error": "Erro: {message}", "print_windows_only": "A impressão direta está disponível somente no Windows.",
        "chart_sent_to_printer": "Gráfico enviado para a impressora padrão.", "print_error": "Não foi possível iniciar a impressão: {message}",
        "settings_title": "Configurações da curva", "general_parameters": "Parâmetros gerais", "language": "Idioma do sistema",
        "arc_unit": "Unidade da altura da flecha", "almen_type": "Tipo da lâmina Almen", "exposure_unit": "Unidade de exposição",
        "registered_references": "Referências normativas registradas", "individual_deviations": "Desvios individuais por lâmina ({unit})",
        "deviation_help": "Cadastre uma linha para cada lâmina que possua desvio próprio. Informe o desvio como medição indicada − valor real; ele será subtraído somente da flecha associada àquela lâmina.",
        "blade_id": "Identificação da lâmina", "deviation": "Desvio", "remove": "Remover", "add_blade": "+ Adicionar lâmina / desvio",
        "apply_settings": "Aplicar configurações", "blade": "Lâmina", "invalid_deviation": "Erro: informe um desvio numérico válido na lâmina {index}.",
        "blade_required": "Erro: informe a identificação da lâmina {index}.", "unique_blades": "Erro: use identificações únicas e diferentes de 'Sem desvio'.",
        "finite_deviations": "Erro: os desvios das lâminas devem ser finitos.", "report_title": "Gerar relatório técnico",
        "report_heading": "Relatório técnico da curva de saturação", "pn_registry": "Cadastro por PN", "search_pn": "Buscar PN",
        "search_pn_placeholder": "Digite todo ou parte do PN", "results": "Resultados", "search": "Buscar", "none_found": "Nenhum PN encontrado",
        "piece_identification": "Identificação e especificação", "process_data": "Dados do equipamento e processo", "value": "Valor",
        "standard": "Norma a ser atendida", "notes": "Observações", "save_update_pn": "Salvar / atualizar PN", "delete_pn": "Excluir PN",
        "generate_html": "Gerar relatório HTML", "piece_pn": "Peça / PN", "reference": "Referência", "repair": "Reparo", "equipment": "Equipamento",
        "no_information": "Não informado.", "report_subtitle": "Registro técnico de ensaio e parâmetros do processo", "issued": "Emitido em {date}",
        "piece_information": "Informações da peça", "standard_to_meet": "Norma a ser atendida", "process_parameters": "Parâmetros do processo",
        "curve_results": "Resultados da curva", "saturation_chart": "Gráfico de saturação", "save_report": "Salvar relatório técnico",
        "html_report": "Relatório HTML", "all_files": "Todos os arquivos", "report_file": "relatorio_curva_saturacao_almen.html",
        "pn_loaded": "Cadastro do PN {pn} carregado.", "save_pn_error": "Não foi possível salvar o PN: {message}", "pn_saved": "Cadastro do PN {pn} salvo/atualizado.",
        "pn_required_delete": "Informe a Peça / PN que deve ser removida.", "delete_registry": "Remover cadastro", "delete_confirmation": "Remover definitivamente o cadastro do PN {pn}?",
        "delete_pn_error": "Não foi possível remover o PN: {message}", "pn_removed": "Cadastro do PN {pn} removido.", "pn_not_found": "PN {pn} não foi encontrado no cadastro.",
        "report_generated": "Relatório técnico gerado com sucesso.", "save_report_error": "Não foi possível salvar o relatório: {message}",
        "technical_title": "Tabelas técnicas — mídia de shot peening", "technical_heading": "Tabelas técnicas de mídia e normas",
        "technical_subtitle": "Referência rápida para análise de esferas, granulometria, tipos de mídia e normas aplicáveis.",
        "tab_analysis": "Análise de esferas", "tab_grain_size": "Granulometria", "tab_media_types": "Tipos de mídia", "tab_standards": "Normas",
    },
    "EN": {
        "app_title": "Almen Saturation Curve Calculator", "measurements": "Almen Strip Measurements", "add_row": "+ Row", "remove_row": "- Row", "example": "Example", "settings": "Settings", "calculate": "Calculate and Plot", "generate_report": "Generate report", "print_chart": "Print chart", "technical_tables": "Technical tables", "system_references": "SYSTEM STANDARD REFERENCES", "exposure": "Exposure", "arc_height": "Arc height", "blade_deviation": "Strip / deviation", "no_deviation": "No deviation", "saturation_time": "Sat. time (T)", "intensity": "Intensity H(T)", "point_2t": "Point (2T)", "height_2t": "Height H(2T)", "fit": "Fit R²", "deviations": "Deviations", "none_applied": "none applied", "chart_title": "Almen Saturation Curve", "measured_points": "Compensated measured points", "fitted_curve": "Fitted curve ($R^2={r2:.3f}$)", "saturation_point": "Saturation T ({value:.2f} {unit})", "row_incomplete": "Fill in exposure and arc height on row {index}.", "invalid_numbers": "Use valid numbers on row {index}.", "error": "Error: {message}", "print_windows_only": "Direct printing is only available on Windows.", "chart_sent_to_printer": "Chart sent to the default printer.", "print_error": "Could not start printing: {message}", "settings_title": "Curve settings", "general_parameters": "General parameters", "language": "System language", "arc_unit": "Arc height unit", "almen_type": "Almen strip type", "exposure_unit": "Exposure unit", "registered_references": "Registered standards references", "individual_deviations": "Individual strip deviations ({unit})", "deviation_help": "Register one row for each strip with its own deviation. Enter the deviation as indicated measurement − actual value; it is subtracted only from the associated arc height.", "blade_id": "Strip identification", "deviation": "Deviation", "remove": "Remove", "add_blade": "+ Add strip / deviation", "apply_settings": "Apply settings", "blade": "Strip", "invalid_deviation": "Error: enter a valid numeric deviation for strip {index}.", "blade_required": "Error: identify strip {index}.", "unique_blades": "Error: use unique names other than 'No deviation'.", "finite_deviations": "Error: strip deviations must be finite.", "report_title": "Generate technical report", "report_heading": "Saturation curve technical report", "pn_registry": "PN registry", "search_pn": "Search PN", "search_pn_placeholder": "Type all or part of the PN", "results": "Results", "search": "Search", "none_found": "No PN found", "piece_identification": "Identification and specification", "process_data": "Equipment and process data", "value": "Value", "standard": "Required standard", "notes": "Notes", "save_update_pn": "Save / update PN", "delete_pn": "Delete PN", "generate_html": "Generate HTML report", "piece_pn": "Part / PN", "reference": "Reference", "repair": "Repair", "equipment": "Equipment", "no_information": "Not informed.", "report_subtitle": "Technical record of the test and process parameters", "issued": "Issued on {date}", "piece_information": "Part information", "standard_to_meet": "Required standard", "process_parameters": "Process parameters", "curve_results": "Curve results", "saturation_chart": "Saturation chart", "save_report": "Save technical report", "html_report": "HTML report", "all_files": "All files", "report_file": "almen_saturation_curve_report.html", "pn_loaded": "PN {pn} record loaded.", "save_pn_error": "Could not save PN: {message}", "pn_saved": "PN {pn} record saved/updated.", "pn_required_delete": "Enter the Part / PN to delete.", "delete_registry": "Delete record", "delete_confirmation": "Permanently delete PN {pn} record?", "delete_pn_error": "Could not delete PN: {message}", "pn_removed": "PN {pn} record deleted.", "pn_not_found": "PN {pn} was not found.", "report_generated": "Technical report generated successfully.", "save_report_error": "Could not save report: {message}", "technical_title": "Technical tables — shot peening media", "technical_heading": "Technical media and standards tables", "technical_subtitle": "Quick reference for shot analysis, grain size, media types and applicable standards.", "tab_analysis": "Shot analysis", "tab_grain_size": "Grain size", "tab_media_types": "Media types", "tab_standards": "Standards",
    },
    "ES": {
        "app_title": "Calculadora de Curva de Saturación Almen", "measurements": "Mediciones de la Lámina Almen", "add_row": "+ Fila", "remove_row": "- Fila", "example": "Ejemplo", "settings": "Configuración", "calculate": "Calcular y Generar Gráfico", "generate_report": "Generar informe", "print_chart": "Imprimir gráfico", "technical_tables": "Tablas técnicas", "system_references": "REFERENCIAS NORMATIVAS DEL SISTEMA", "exposure": "Exposición", "arc_height": "Altura de arco", "blade_deviation": "Lámina / desviación", "no_deviation": "Sin desviación", "saturation_time": "Tiempo sat. (T)", "intensity": "Intensidad H(T)", "point_2t": "Punto (2T)", "height_2t": "Altura H(2T)", "fit": "Ajuste R²", "deviations": "Desviaciones", "none_applied": "ninguna aplicada", "chart_title": "Curva de Saturación Almen", "measured_points": "Puntos medidos compensados", "fitted_curve": "Curva ajustada ($R^2={r2:.3f}$)", "saturation_point": "Saturación T ({value:.2f} {unit})", "row_incomplete": "Complete exposición y altura de arco en la fila {index}.", "invalid_numbers": "Use números válidos en la fila {index}.", "error": "Error: {message}", "print_windows_only": "La impresión directa solo está disponible en Windows.", "chart_sent_to_printer": "Gráfico enviado a la impresora predeterminada.", "print_error": "No se pudo iniciar la impresión: {message}", "settings_title": "Configuración de la curva", "general_parameters": "Parámetros generales", "language": "Idioma del sistema", "arc_unit": "Unidad de altura de arco", "almen_type": "Tipo de lámina Almen", "exposure_unit": "Unidad de exposición", "registered_references": "Referencias normativas registradas", "individual_deviations": "Desviaciones individuales por lámina ({unit})", "deviation_help": "Registre una fila para cada lámina que posea su propia desviación. Introduzca la desviación como medición indicada − valor real; solo se restará de la altura de arco asociada.", "blade_id": "Identificación de la lámina", "deviation": "Desviación", "remove": "Eliminar", "add_blade": "+ Añadir lámina / desviación", "apply_settings": "Aplicar configuración", "blade": "Lámina", "invalid_deviation": "Error: introduzca una desviación numérica válida en la lámina {index}.", "blade_required": "Error: identifique la lámina {index}.", "unique_blades": "Error: use identificaciones únicas y distintas de 'Sin desviación'.", "finite_deviations": "Error: las desviaciones deben ser finitas.", "report_title": "Generar informe técnico", "report_heading": "Informe técnico de la curva de saturación", "pn_registry": "Registro por PN", "search_pn": "Buscar PN", "search_pn_placeholder": "Escriba todo o parte del PN", "results": "Resultados", "search": "Buscar", "none_found": "Ningún PN encontrado", "piece_identification": "Identificación y especificación", "process_data": "Datos del equipo y proceso", "value": "Valor", "standard": "Norma requerida", "notes": "Observaciones", "save_update_pn": "Guardar / actualizar PN", "delete_pn": "Eliminar PN", "generate_html": "Generar informe HTML", "piece_pn": "Pieza / PN", "reference": "Referencia", "repair": "Reparación", "equipment": "Equipo", "no_information": "No informado.", "report_subtitle": "Registro técnico de ensayo y parámetros del proceso", "issued": "Emitido el {date}", "piece_information": "Información de la pieza", "standard_to_meet": "Norma requerida", "process_parameters": "Parámetros del proceso", "curve_results": "Resultados de la curva", "saturation_chart": "Gráfico de saturación", "save_report": "Guardar informe técnico", "html_report": "Informe HTML", "all_files": "Todos los archivos", "report_file": "informe_curva_saturacion_almen.html", "pn_loaded": "Registro del PN {pn} cargado.", "save_pn_error": "No se pudo guardar el PN: {message}", "pn_saved": "Registro del PN {pn} guardado/actualizado.", "pn_required_delete": "Introduzca la Pieza / PN que desea eliminar.", "delete_registry": "Eliminar registro", "delete_confirmation": "¿Eliminar definitivamente el registro del PN {pn}?", "delete_pn_error": "No se pudo eliminar el PN: {message}", "pn_removed": "Registro del PN {pn} eliminado.", "pn_not_found": "No se encontró el PN {pn}.", "report_generated": "Informe técnico generado correctamente.", "save_report_error": "No se pudo guardar el informe: {message}", "technical_title": "Tablas técnicas — medios de shot peening", "technical_heading": "Tablas técnicas de medios y normas", "technical_subtitle": "Referencia rápida para análisis de esferas, granulometría, tipos de medios y normas aplicables.", "tab_analysis": "Análisis de esferas", "tab_grain_size": "Granulometría", "tab_media_types": "Tipos de medios", "tab_standards": "Normas",
    },
}

_TEXTS["PT"]["part_serial_number"] = "SN da peça (opcional)"
_TEXTS["EN"]["part_serial_number"] = "Part serial number (optional)"
_TEXTS["ES"]["part_serial_number"] = "N.º de serie de la pieza (opcional)"

# Textos de interface que não se encaixam nas chaves curtas acima. Mantê-los
# aqui evita que módulos de dados e telas técnicas carreguem conteúdo em um
# idioma fixo.
_TEXTS["PT"].update({
    "required_peening_intensity": "Intensidade de peening",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "Referências SAE registradas; a conformidade exige validação do processo e dos dados do ensaio.",
    "unit_mm": "Milímetros (mm)", "unit_in": "Polegadas (in)",
    "exposure_seconds": "Segundos", "exposure_passes": "Passes", "exposure_rotations": "Rotações", "exposure_cycles": "Ciclos", "exposure_inverse_feed": "Inverso do avanço",
    "almen_type_n": "N - fina", "almen_type_a": "A - padrão", "almen_type_c": "C - espessa",
    "deviation_placeholder": "Ex.: 0,005", "point_2t_legend": "Ponto 2T ({value:.2f} {unit})",
    "shot": "Esfera", "hardness": "Dureza", "nozzle": "Bico", "injector": "Injetor", "distance": "Distância", "angle": "Ângulo", "pressure": "Pressão",
    "registered_deviations": "Desvios de lâmina cadastrados", "standard_default": "SAE J443 e SAE J2597", "standard_other": "Outra norma (informar em observações)",
    "pn_required_save": "Informe a Peça / PN para salvar o cadastro.", "pn_required_remove": "Informe a Peça / PN a remover.",
    "invalid_arc_unit": "Unidade de flecha inválida.", "deviation_not_finite": "O desvio da lâmina deve ser um número finito.",
    "deviation_per_height": "Informe um desvio para cada flecha medida.", "negative_compensated": "O desvio informado torna alguma flecha compensada negativa.",
    "data_vectors": "Tempo e altura devem ser vetores do mesmo tamanho.", "data_finite": "Tempo e altura devem conter apenas números finitos.",
    "exposure_negative": "Os tempos de exposição não podem ser negativos.", "arc_negative": "As alturas de arco não podem ser negativas.",
    "min_measurements": "A curva exige pelo menos 4 medições válidas.", "min_nonzero_arc": "A curva exige pelo menos 4 alturas de arco não nulas.",
    "distinct_exposure": "Informe pelo menos dois valores de exposição distintos.", "varying_arc": "As alturas precisam variar para calcular a saturação.",
    "saturation_rate": "Não foi possível determinar uma taxa de saturação positiva.",
})
_TEXTS["EN"].update({
    "required_peening_intensity": "Peening intensity",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "SAE references are registered; compliance requires validation of the process and test data.",
    "unit_mm": "Millimetres (mm)", "unit_in": "Inches (in)",
    "exposure_seconds": "Seconds", "exposure_passes": "Passes", "exposure_rotations": "Rotations", "exposure_cycles": "Cycles", "exposure_inverse_feed": "Inverse feed rate",
    "almen_type_n": "N - thin", "almen_type_a": "A - standard", "almen_type_c": "C - thick",
    "deviation_placeholder": "E.g.: 0.005", "point_2t_legend": "Point 2T ({value:.2f} {unit})",
    "shot": "Shot", "hardness": "Hardness", "nozzle": "Nozzle", "injector": "Injector", "distance": "Distance", "angle": "Angle", "pressure": "Pressure",
    "registered_deviations": "Registered strip deviations", "standard_default": "SAE J443 and SAE J2597", "standard_other": "Other standard (enter in notes)",
    "pn_required_save": "Enter the Part / PN to save the record.", "pn_required_remove": "Enter the Part / PN to remove.",
    "invalid_arc_unit": "Invalid arc-height unit.", "deviation_not_finite": "The strip deviation must be a finite number.",
    "deviation_per_height": "Enter one deviation for each measured arc height.", "negative_compensated": "The supplied deviation makes a compensated arc height negative.",
    "data_vectors": "Time and height must be vectors of the same size.", "data_finite": "Time and height must contain only finite numbers.",
    "exposure_negative": "Exposure times cannot be negative.", "arc_negative": "Arc heights cannot be negative.",
    "min_measurements": "The curve requires at least 4 valid measurements.", "min_nonzero_arc": "The curve requires at least 4 non-zero arc heights.",
    "distinct_exposure": "Enter at least two distinct exposure values.", "varying_arc": "Arc heights must vary to calculate saturation.",
    "saturation_rate": "Could not determine a positive saturation rate.",
})
_TEXTS["ES"].update({
    "required_peening_intensity": "Intensidad de peening",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "Las referencias SAE están registradas; la conformidad exige validar el proceso y los datos del ensayo.",
    "unit_mm": "Milímetros (mm)", "unit_in": "Pulgadas (in)",
    "exposure_seconds": "Segundos", "exposure_passes": "Pasadas", "exposure_rotations": "Rotaciones", "exposure_cycles": "Ciclos", "exposure_inverse_feed": "Inverso del avance",
    "almen_type_n": "N - fina", "almen_type_a": "A - estándar", "almen_type_c": "C - gruesa",
    "deviation_placeholder": "Ej.: 0,005", "point_2t_legend": "Punto 2T ({value:.2f} {unit})",
    "shot": "Esfera", "hardness": "Dureza", "nozzle": "Boquilla", "injector": "Inyector", "distance": "Distancia", "angle": "Ángulo", "pressure": "Presión",
    "registered_deviations": "Desviaciones de lámina registradas", "standard_default": "SAE J443 y SAE J2597", "standard_other": "Otra norma (indicar en observaciones)",
    "pn_required_save": "Introduzca la Pieza / PN para guardar el registro.", "pn_required_remove": "Introduzca la Pieza / PN que desea eliminar.",
    "invalid_arc_unit": "Unidad de altura de arco no válida.", "deviation_not_finite": "La desviación de la lámina debe ser un número finito.",
    "deviation_per_height": "Introduzca una desviación para cada altura de arco medida.", "negative_compensated": "La desviación indicada hace negativa alguna altura de arco compensada.",
    "data_vectors": "El tiempo y la altura deben ser vectores del mismo tamaño.", "data_finite": "El tiempo y la altura solo deben contener números finitos.",
    "exposure_negative": "Los tiempos de exposición no pueden ser negativos.", "arc_negative": "Las alturas de arco no pueden ser negativas.",
    "min_measurements": "La curva requiere al menos 4 mediciones válidas.", "min_nonzero_arc": "La curva requiere al menos 4 alturas de arco no nulas.",
    "distinct_exposure": "Introduzca al menos dos valores de exposición distintos.", "varying_arc": "Las alturas de arco deben variar para calcular la saturación.",
    "saturation_rate": "No fue posible determinar una tasa de saturación positiva.",
})

_TECHNICAL_CONTENT = {
    "PT": {
        "analysis": ("Roteiro de análise de esferas / mídia metálica", "Use o roteiro junto com o plano de inspeção e o certificado do lote; ele não substitui ensaios nem critérios contratuais.", ("Item", "Verificação", "Finalidade"), (("Identificação", "Tipo, lote, fabricante e certificado", "Mantém a rastreabilidade da mídia usada."), ("Granulometria", "Ensaio por peneiras ASTM E11", "Confirma a distribuição e a designação SAE J444."), ("Forma", "Esfericidade, partículas quebradas e satélites", "Evita impacto irregular e acabamento inconsistente."), ("Dureza", "Faixa especificada para a mídia", "Influencia a energia transferida e a vida útil da esfera."), ("Composição", "Análise química conforme especificação", "Confirma o material, como aço fundido de alto carbono."), ("Integridade", "Trincas, porosidade, contaminação e oxidação", "Reduz risco de quebra e contaminação da peça."), ("Desempenho", "Teste mecânico / vida Ervin quando requerido", "Compara durabilidade e energia transmitida pela mídia."))),
        "grain": ("Granulometria de esfera conforme designação SAE J444", "A abertura nominal identifica a classe. A distribuição completa e seus limites devem ser conferidos na edição vigente da J444 e no certificado do lote.", ("Designação", "Abertura nominal (in)", "Abertura nominal (mm)", "Classe visual"), (("S70", "0.0070", "0,178", "Fina"), ("S110", "0.0110", "0,279", "Fina"), ("S170", "0.0170", "0,432", "Média"), ("S230", "0.0230", "0,584", "Média"), ("S280", "0.0280", "0,711", "Média"), ("S330", "0.0330", "0,838", "Média"), ("S390", "0.0390", "0,991", "Grossa"), ("S460", "0.0460", "1,168", "Grossa"), ("S550", "0.0550", "1,397", "Grossa"), ("S660", "0.0660", "1,676", "Muito grossa"), ("S780", "0.0780", "1,981", "Muito grossa"))),
        "media": ("Tipos de mídia", "Escolha conforme desenho, material da peça e processo aprovado.", ("Tipo", "Designação", "Referência", "Uso"), (("Esfera de aço fundido alto carbono", "S + designação", "SAE J827 e SAE J444", "Shot peening e limpeza."), ("Esfera de aço fundido baixo carbono", "S + designação", "SAE J2175 e SAE J444", "Quando a especificação exigir baixa dureza/carbono."), ("Arame cortado condicionado", "Diâmetro nominal", "SAE J441", "Mídia metálica de alta durabilidade."), ("Granalha angular de aço (grit)", "G + designação", "SAE J1993 e SAE J444", "Limpeza, decapagem e ancoragem; não substitui esfera sem aprovação."), ("Esfera de vidro ou cerâmica", "Conforme fornecedor", "Especificação do processo", "Mídias não metálicas para aplicações definidas."))),
        "standards": ("Normas de referência", "Verifique a revisão contratual antes de declarar conformidade.", ("Norma", "Assunto", "Aplicação no app"), (("SAE J444", "Classificação de tamanhos de esfera e granalha fundidas", "Define designações S/G e controle por peneiras."), ("SAE J827", "Esfera de aço fundido de alto carbono", "Composição e características físicas da esfera."), ("SAE J2175", "Esfera de aço fundido de baixo carbono", "Requisitos de composição, dureza, microestrutura e características físicas."), ("SAE J441", "Arame cortado", "Guia para seleção e uso de shot de arame cortado."), ("SAE J1993", "Granalha de aço fundido alto carbono", "Requisitos para grit usado em limpeza e ataque superficial."), ("SAE J445", "Teste mecânico de esfera e granalha metálicas", "Métodos laboratoriais para avaliar a mídia."), ("SAE J442", "Lâmina, suporte e medidor Almen", "Equipamentos e suprimentos para medição de flecha."), ("SAE J443", "Determinação e verificação da intensidade", "Curva de saturação e uso das lâminas Almen."), ("SAE J2277", "Cobertura de shot peening", "Método para determinar a cobertura do processo."), ("SAE J2597", "Curvas de saturação geradas por computador", "Orientação para curvas de saturação assistidas por software."), ("AMS2430 / AMS2431", "Processo e aquisição de mídia aeroespacial", "Aplicar somente quando exigido pelo desenho, contrato ou cliente."))),
        "notice": "Consulta técnica: confirme sempre a revisão vigente da norma e os limites de aceitação no certificado do lote, desenho da peça e procedimento aprovado.",
    },
    "EN": {
        "analysis": ("Shot / metallic media inspection guide", "Use this guide with the inspection plan and batch certificate; it does not replace tests or contractual criteria.", ("Item", "Check", "Purpose"), (("Identification", "Type, batch, manufacturer and certificate", "Maintains traceability of the media used."), ("Grain size", "ASTM E11 sieve test", "Confirms distribution and SAE J444 designation."), ("Shape", "Sphericity, broken particles and satellites", "Prevents irregular impact and inconsistent finish."), ("Hardness", "Specified range for the media", "Influences transferred energy and shot service life."), ("Composition", "Chemical analysis per specification", "Confirms the material, such as high-carbon cast steel."), ("Integrity", "Cracks, porosity, contamination and oxidation", "Reduces breakage and part contamination risk."), ("Performance", "Mechanical test / Ervin life when required", "Compares media durability and transmitted energy."))),
        "grain": ("Shot grain size according to SAE J444 designation", "The nominal opening identifies the class. Check the complete distribution and limits in the current J444 edition and batch certificate.", ("Designation", "Nominal opening (in)", "Nominal opening (mm)", "Visual class"), (("S70", "0.0070", "0.178", "Fine"), ("S110", "0.0110", "0.279", "Fine"), ("S170", "0.0170", "0.432", "Medium"), ("S230", "0.0230", "0.584", "Medium"), ("S280", "0.0280", "0.711", "Medium"), ("S330", "0.0330", "0.838", "Medium"), ("S390", "0.0390", "0.991", "Coarse"), ("S460", "0.0460", "1.168", "Coarse"), ("S550", "0.0550", "1.397", "Coarse"), ("S660", "0.0660", "1.676", "Very coarse"), ("S780", "0.0780", "1.981", "Very coarse"))),
        "media": ("Media types", "Select according to the drawing, part material and approved process.", ("Type", "Designation", "Reference", "Use"), (("High-carbon cast steel shot", "S + designation", "SAE J827 and SAE J444", "Shot peening and cleaning."), ("Low-carbon cast steel shot", "S + designation", "SAE J2175 and SAE J444", "When the specification requires low hardness/carbon."), ("Conditioned cut wire", "Nominal diameter", "SAE J441", "High-durability metallic media."), ("Angular steel grit", "G + designation", "SAE J1993 and SAE J444", "Cleaning, descaling and anchoring; does not replace shot without approval."), ("Glass or ceramic bead", "Per supplier", "Process specification", "Non-metallic media for defined applications."))),
        "standards": ("Reference standards", "Check the contractual revision before declaring compliance.", ("Standard", "Subject", "Application in app"), (("SAE J444", "Cast shot and grit size classification", "Defines S/G designations and sieve control."), ("SAE J827", "High-carbon cast steel shot", "Composition and physical characteristics of shot."), ("SAE J2175", "Low-carbon cast steel shot", "Composition, hardness, microstructure and physical requirements."), ("SAE J441", "Cut wire", "Guide for selecting and using cut-wire shot."), ("SAE J1993", "High-carbon cast steel grit", "Requirements for grit used in cleaning and surface preparation."), ("SAE J445", "Mechanical test for shot and metallic grit", "Laboratory methods for media evaluation."), ("SAE J442", "Almen strip, holder and gauge", "Equipment and supplies for arc-height measurement."), ("SAE J443", "Determining and verifying intensity", "Saturation curve and Almen strip use."), ("SAE J2277", "Shot peening coverage", "Method for determining process coverage."), ("SAE J2597", "Computer-generated saturation curves", "Guidance for software-assisted saturation curves."), ("AMS2430 / AMS2431", "Aerospace media process and procurement", "Apply only when required by drawing, contract or customer."))),
        "notice": "Technical reference: always confirm the current standard revision and acceptance limits in the batch certificate, part drawing and approved procedure.",
    },
    "ES": {
        "analysis": ("Guía de análisis de esferas / medio metálico", "Use la guía con el plan de inspección y el certificado del lote; no sustituye ensayos ni criterios contractuales.", ("Elemento", "Verificación", "Finalidad"), (("Identificación", "Tipo, lote, fabricante y certificado", "Mantiene la trazabilidad del medio utilizado."), ("Granulometría", "Ensayo de tamices ASTM E11", "Confirma la distribución y designación SAE J444."), ("Forma", "Esfericidad, partículas rotas y satélites", "Evita impacto irregular y acabado inconsistente."), ("Dureza", "Rango especificado para el medio", "Influye en la energía transferida y la vida útil de la esfera."), ("Composición", "Análisis químico conforme a especificación", "Confirma el material, como acero fundido de alto carbono."), ("Integridad", "Grietas, porosidad, contaminación y oxidación", "Reduce el riesgo de rotura y contaminación de la pieza."), ("Desempeño", "Ensayo mecánico / vida Ervin cuando sea requerido", "Compara durabilidad y energía transmitida por el medio."))),
        "grain": ("Granulometría de esfera según designación SAE J444", "La abertura nominal identifica la clase. Compruebe la distribución completa y límites en la edición vigente de J444 y el certificado del lote.", ("Designación", "Abertura nominal (in)", "Abertura nominal (mm)", "Clase visual"), (("S70", "0.0070", "0,178", "Fina"), ("S110", "0.0110", "0,279", "Fina"), ("S170", "0.0170", "0,432", "Media"), ("S230", "0.0230", "0,584", "Media"), ("S280", "0.0280", "0,711", "Media"), ("S330", "0.0330", "0,838", "Media"), ("S390", "0.0390", "0,991", "Gruesa"), ("S460", "0.0460", "1,168", "Gruesa"), ("S550", "0.0550", "1,397", "Gruesa"), ("S660", "0.0660", "1,676", "Muy gruesa"), ("S780", "0.0780", "1,981", "Muy gruesa"))),
        "media": ("Tipos de medio", "Elija según el plano, material de la pieza y proceso aprobado.", ("Tipo", "Designación", "Referencia", "Uso"), (("Esfera de acero fundido de alto carbono", "S + designación", "SAE J827 y SAE J444", "Shot peening y limpieza."), ("Esfera de acero fundido de bajo carbono", "S + designación", "SAE J2175 y SAE J444", "Cuando la especificación requiera baja dureza/carbono."), ("Alambre cortado acondicionado", "Diámetro nominal", "SAE J441", "Medio metálico de alta durabilidad."), ("Granalla angular de acero", "G + designación", "SAE J1993 y SAE J444", "Limpieza, decapado y anclaje; no sustituye la esfera sin aprobación."), ("Esfera de vidrio o cerámica", "Según proveedor", "Especificación del proceso", "Medios no metálicos para aplicaciones definidas."))),
        "standards": ("Normas de referencia", "Verifique la revisión contractual antes de declarar conformidad.", ("Norma", "Asunto", "Aplicación en la app"), (("SAE J444", "Clasificación de tamaños de esfera y granalla fundidas", "Define designaciones S/G y control por tamices."), ("SAE J827", "Esfera de acero fundido de alto carbono", "Composición y características físicas de la esfera."), ("SAE J2175", "Esfera de acero fundido de bajo carbono", "Requisitos de composición, dureza, microestructura y características físicas."), ("SAE J441", "Alambre cortado", "Guía para seleccionar y usar shot de alambre cortado."), ("SAE J1993", "Granalla de acero fundido alto carbono", "Requisitos para grit utilizado en limpieza y preparación superficial."), ("SAE J445", "Ensayo mecánico de esfera y granalla metálicas", "Métodos de laboratorio para evaluar el medio."), ("SAE J442", "Lámina, soporte y medidor Almen", "Equipo y suministros para medir altura de arco."), ("SAE J443", "Determinación y verificación de intensidad", "Curva de saturación y uso de láminas Almen."), ("SAE J2277", "Cobertura de shot peening", "Método para determinar la cobertura del proceso."), ("SAE J2597", "Curvas de saturación generadas por ordenador", "Guía para curvas asistidas por software."), ("AMS2430 / AMS2431", "Proceso y adquisición de medio aeroespacial", "Aplicar solo cuando lo exija el plano, contrato o cliente."))),
        "notice": "Consulta técnica: confirme siempre la revisión vigente de la norma y los límites de aceptación en el certificado del lote, plano de la pieza y procedimiento aprobado.",
    },
}


def load_language() -> str:
    try:
        language = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8")).get("language", DEFAULT_LANGUAGE)
    except (OSError, json.JSONDecodeError, AttributeError):
        try:
            save_language(DEFAULT_LANGUAGE)
        except OSError:
            pass
        return DEFAULT_LANGUAGE
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def save_language(language: str) -> None:
    if language not in LANGUAGES:
        raise ValueError(f"Idioma não suportado: {language}")
    _SETTINGS_FILE.write_text(json.dumps({"language": language}, ensure_ascii=False, indent=2), encoding="utf-8")


def tr(key: str, language: str | None = None, **values) -> str:
    language = language or load_language()
    text = _TEXTS.get(language, _TEXTS[DEFAULT_LANGUAGE]).get(key, _TEXTS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**values)


def technical_content(language: str | None = None) -> dict:
    """Retorna o conteúdo técnico integral no idioma selecionado."""
    return _TECHNICAL_CONTENT.get(language or load_language(), _TECHNICAL_CONTENT[DEFAULT_LANGUAGE])


def html_language(language: str | None = None) -> str:
    return {"PT": "pt-BR", "EN": "en", "ES": "es"}.get(language or load_language(), "pt-BR")
