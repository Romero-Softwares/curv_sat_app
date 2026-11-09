"""Textos da interface e preferência persistente de idioma.

As chaves permanecem estáveis e independentes do idioma para que os dados
salvos no banco local continuem compatíveis quando a interface for alterada.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from curvsat.core.paths import user_data_file


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
        "example": "⟳ Recarregar", "settings": "Configurações", "calculate": "Calcular e Gerar Gráfico",
        "generate_report": "Gerenciar Dados e Relatório", "print_chart": "Imprimir gráfico", "technical_tables": "Tabelas técnicas",
        "system_references": "REFERÊNCIAS NORMATIVAS DO SISTEMA", "exposure": "Exposição",
        "arc_height": "Altura do arco", "blade_deviation": "Lâmina / desvio", "no_deviation": "Sem desvio",
        "saturation_time": "Tempo de saturação (T)", "intensity": "Intensidade H(T)", "point_2t": "Ponto (2T)",
        "height_2t": "Altura H(2T)", "fit": "Ajuste R²", "deviations": "Desvios", "none_applied": "nenhum aplicado",
        "chart_title": "Curva de Saturação Almen", "measured_points": "Pontos medidos compensados",
        "fitted_curve": "Curva ajustada ($R^2={r2:.3f}$)", "saturation_point": "Saturação T ({value:.2f} {unit})",
        "row_incomplete": "Preencha exposição e altura do arco na linha {index}.", "invalid_numbers": "Use números válidos na linha {index}.",
        "error": "Erro: {message}", "print_windows_only": "A impressão direta está disponível somente no Windows.",
        "chart_sent_to_printer": "Gráfico enviado para a impressora padrão.", "print_error": "Não foi possível iniciar a impressão: {message}",
        "settings_title": "Configurações da curva", "general_parameters": "Parâmetros gerais", "language": "Idioma do sistema",
        "arc_unit": "Unidade da altura do arco", "almen_type": "Tipo da lâmina Almen", "exposure_unit": "Unidade de exposição",
        "registered_references": "Referências normativas registradas", "individual_deviations": "Desvios individuais por lâmina ({unit})",
        "deviation_help": "Cadastre uma linha para cada lâmina que possua desvio próprio. Informe o desvio como medição indicada − valor real; ele será subtraído somente da altura do arco associada àquela lâmina.",
        "blade_id": "Identificação da lâmina", "deviation": "Desvio", "remove": "Remover", "add_blade": "+ Adicionar lâmina / desvio",
        "apply_settings": "Aplicar configurações", "blade": "Lâmina", "invalid_deviation": "Erro: informe um desvio numérico válido na lâmina {index}.",
        "blade_required": "Erro: informe a identificação da lâmina {index}.", "unique_blades": "Erro: use identificações únicas e diferentes de 'Sem desvio'.",
        "finite_deviations": "Erro: os desvios das lâminas devem ser finitos.", "report_title": "Gerenciar Dados e Relatório",
        "report_heading": "Gerenciar Dados e Relatório", "pn_registry": "Cadastro por Router, PN, SN, intensidade ou código da curva", "search_pn": "Buscar cadastro",
        "search_pn_placeholder": "Router, PN, SN, intensidade (ex.: 0,014-0,018A) ou código", "results": "Resultados", "search": "Buscar", "none_found": "Nenhum cadastro encontrado",
        "piece_identification": "Identificação e especificação", "process_data": "Dados do equipamento e processo", "value": "Valor",
        "standard": "Norma a ser atendida", "notes": "Observações", "save_update_pn": "Salvar / atualizar PN", "delete_pn": "Excluir PN",
        "generate_html": "Gerar relatório", "piece_pn": "Peça / PN", "reference": "Referência", "reference_cmm": "Referência CMM", "repair": "Reparo", "equipment": "Equipamento",
        "no_information": "Não informado.", "report_subtitle": "Registro técnico de ensaio e parâmetros do processo", "issued": "Emitido em {date}",
        "piece_information": "Informações da peça", "standard_to_meet": "Norma a ser atendida", "process_parameters": "Parâmetros do processo",
        "curve_results": "Resultados da curva", "saturation_chart": "Gráfico de saturação", "save_report": "Salvar relatório técnico",
        "html_report": "Relatório HTML", "all_files": "Todos os arquivos", "report_file": "relatorio_curva_saturacao_almen.pdf",
        "pn_loaded": "Cadastro do PN {pn} carregado.", "save_pn_error": "Não foi possível salvar o PN: {message}", "pn_saved": "Cadastro do PN {pn} salvo/atualizado.",
        "pn_required_delete": "Informe a Peça / PN que deve ser removida.", "delete_registry": "Remover cadastro", "delete_confirmation": "Remover definitivamente o cadastro do PN {pn}?",
        "delete_pn_error": "Não foi possível remover o PN: {message}", "pn_removed": "Cadastro do PN {pn} removido.", "pn_not_found": "PN {pn} não foi encontrado no cadastro.",
        "report_generated": "Relatório técnico gerado com sucesso.", "save_report_error": "Não foi possível salvar o relatório: {message}",
        "technical_title": "Tabelas técnicas — mídia de shot peening", "technical_heading": "Tabelas técnicas de mídia e normas",
        "technical_subtitle": "Referência rápida para análise de esferas, granulometria, tipos de mídia e normas aplicáveis.",
        "tab_analysis": "Análise de esferas", "tab_grain_size": "Granulometria", "tab_media_types": "Tipos de mídia", "tab_standards": "Normas",
    },
    "EN": {
        "app_title": "Almen Saturation Curve Calculator", "measurements": "Almen Strip Measurements", "add_row": "+ Row", "remove_row": "- Row", "example": "Example", "settings": "Settings", "calculate": "Calculate and Plot", "generate_report": "Manage Data and Report", "print_chart": "Print chart", "technical_tables": "Technical tables", "system_references": "SYSTEM STANDARD REFERENCES", "exposure": "Exposure", "arc_height": "Arc height", "blade_deviation": "Strip / deviation", "no_deviation": "No deviation", "saturation_time": "Sat. time (T)", "intensity": "Intensity H(T)", "point_2t": "Point (2T)", "height_2t": "Height H(2T)", "fit": "Fit R²", "deviations": "Deviations", "none_applied": "none applied", "chart_title": "Almen Saturation Curve", "measured_points": "Compensated measured points", "fitted_curve": "Fitted curve ($R^2={r2:.3f}$)", "saturation_point": "Saturation T ({value:.2f} {unit})", "row_incomplete": "Fill in exposure and arc height on row {index}.", "invalid_numbers": "Use valid numbers on row {index}.", "error": "Error: {message}", "print_windows_only": "Direct printing is only available on Windows.", "chart_sent_to_printer": "Chart sent to the default printer.", "print_error": "Could not start printing: {message}", "settings_title": "Curve settings", "general_parameters": "General parameters", "language": "System language", "arc_unit": "Arc height unit", "almen_type": "Almen strip type", "exposure_unit": "Exposure unit", "registered_references": "Registered standards references", "individual_deviations": "Individual strip deviations ({unit})", "deviation_help": "Register one row for each strip with its own deviation. Enter the deviation as indicated measurement − actual value; it is subtracted only from the associated arc height.", "blade_id": "Strip identification", "deviation": "Deviation", "remove": "Remove", "add_blade": "+ Add strip / deviation", "apply_settings": "Apply settings", "blade": "Strip", "invalid_deviation": "Error: enter a valid numeric deviation for strip {index}.", "blade_required": "Error: identify strip {index}.", "unique_blades": "Error: use unique names other than 'No deviation'.", "finite_deviations": "Error: strip deviations must be finite.", "report_title": "Manage Data and Report", "report_heading": "Manage Data and Report", "pn_registry": "Registry by Router, PN, SN, intensity or curve code", "search_pn": "Search records", "search_pn_placeholder": "Router, PN, SN, intensity (e.g. 0.014-0.018A) or code", "results": "Results", "search": "Search", "none_found": "No records found", "piece_identification": "Identification and specification", "process_data": "Equipment and process data", "value": "Value", "standard": "Required standard", "notes": "Notes", "save_update_pn": "Save / update PN", "delete_pn": "Delete PN", "generate_html": "Generate report", "piece_pn": "Part / PN", "reference": "Reference", "repair": "Repair", "equipment": "Equipment", "no_information": "Not informed.", "report_subtitle": "Technical record of the test and process parameters", "issued": "Issued on {date}", "piece_information": "Part information", "standard_to_meet": "Required standard", "process_parameters": "Process parameters", "curve_results": "Curve results", "saturation_chart": "Saturation chart", "save_report": "Save technical report", "html_report": "HTML report", "all_files": "All files", "report_file": "almen_saturation_curve_report.pdf", "pn_loaded": "PN {pn} record loaded.", "save_pn_error": "Could not save PN: {message}", "pn_saved": "PN {pn} record saved/updated.", "pn_required_delete": "Enter the Part / PN to delete.", "delete_registry": "Delete record", "delete_confirmation": "Permanently delete PN {pn} record?", "delete_pn_error": "Could not delete PN: {message}", "pn_removed": "PN {pn} record deleted.", "pn_not_found": "PN {pn} was not found.", "report_generated": "Technical report generated successfully.", "save_report_error": "Could not save report: {message}", "technical_title": "Technical tables — shot peening media", "technical_heading": "Technical media and standards tables", "technical_subtitle": "Quick reference for shot analysis, grain size, media types and applicable standards.", "tab_analysis": "Shot analysis", "tab_grain_size": "Grain size", "tab_media_types": "Media types", "tab_standards": "Standards",
    },
    "ES": {
        "app_title": "Calculadora de Curva de Saturación Almen", "measurements": "Mediciones de la Lámina Almen", "add_row": "+ Fila", "remove_row": "- Fila", "example": "Ejemplo", "settings": "Configuración", "calculate": "Calcular y Generar Gráfico", "generate_report": "Gestionar Datos e Informe", "print_chart": "Imprimir gráfico", "technical_tables": "Tablas técnicas", "system_references": "REFERENCIAS NORMATIVAS DEL SISTEMA", "exposure": "Exposición", "arc_height": "Altura de arco", "blade_deviation": "Lámina / desviación", "no_deviation": "Sin desviación", "saturation_time": "Tiempo sat. (T)", "intensity": "Intensidad H(T)", "point_2t": "Punto (2T)", "height_2t": "Altura H(2T)", "fit": "Ajuste R²", "deviations": "Desviaciones", "none_applied": "ninguna aplicada", "chart_title": "Curva de Saturación Almen", "measured_points": "Puntos medidos compensados", "fitted_curve": "Curva ajustada ($R^2={r2:.3f}$)", "saturation_point": "Saturación T ({value:.2f} {unit})", "row_incomplete": "Complete exposición y altura de arco en la fila {index}.", "invalid_numbers": "Use números válidos en la fila {index}.", "error": "Error: {message}", "print_windows_only": "La impresión directa solo está disponible en Windows.", "chart_sent_to_printer": "Gráfico enviado a la impresora predeterminada.", "print_error": "No se pudo iniciar la impresión: {message}", "settings_title": "Configuración de la curva", "general_parameters": "Parámetros generales", "language": "Idioma del sistema", "arc_unit": "Unidad de altura de arco", "almen_type": "Tipo de lámina Almen", "exposure_unit": "Unidad de exposición", "registered_references": "Referencias normativas registradas", "individual_deviations": "Desviaciones individuales por lámina ({unit})", "deviation_help": "Registre una fila para cada lámina que posea su propia desviación. Introduzca la desviación como medición indicada − valor real; solo se restará de la altura de arco asociada.", "blade_id": "Identificación de la lámina", "deviation": "Desviación", "remove": "Eliminar", "add_blade": "+ Añadir lámina / desviación", "apply_settings": "Aplicar configuración", "blade": "Lámina", "invalid_deviation": "Error: introduzca una desviación numérica válida en la lámina {index}.", "blade_required": "Error: identifique la lámina {index}.", "unique_blades": "Error: use identificaciones únicas y distintas de 'Sin desviación'.", "finite_deviations": "Error: las desviaciones deben ser finitas.", "report_title": "Gestionar Datos e Informe", "report_heading": "Gestionar Datos e Informe", "pn_registry": "Registro por Router, PN, SN, intensidad o código de curva", "search_pn": "Buscar registro", "search_pn_placeholder": "Router, PN, SN, intensidad (ej.: 0,014-0,018A) o código", "results": "Resultados", "search": "Buscar", "none_found": "No se encontraron registros", "piece_identification": "Identificación y especificación", "process_data": "Datos del equipo y proceso", "value": "Valor", "standard": "Norma requerida", "notes": "Observaciones", "save_update_pn": "Guardar / actualizar PN", "delete_pn": "Eliminar PN", "generate_html": "Generar informe HTML", "piece_pn": "Pieza / PN", "reference": "Referencia", "repair": "Reparación", "equipment": "Equipo", "no_information": "No informado.", "report_subtitle": "Registro técnico de ensayo y parámetros del proceso", "issued": "Emitido el {date}", "piece_information": "Información de la pieza", "standard_to_meet": "Norma requerida", "process_parameters": "Parámetros del proceso", "curve_results": "Resultados de la curva", "saturation_chart": "Gráfico de saturación", "save_report": "Guardar informe técnico", "html_report": "Informe HTML", "all_files": "Todos los archivos", "report_file": "informe_curva_saturacion_almen.html", "pn_loaded": "Registro del PN {pn} cargado.", "save_pn_error": "No se pudo guardar el PN: {message}", "pn_saved": "Registro del PN {pn} guardado/actualizado.", "pn_required_delete": "Introduzca la Pieza / PN que desea eliminar.", "delete_registry": "Eliminar registro", "delete_confirmation": "¿Eliminar definitivamente el registro del PN {pn}?", "delete_pn_error": "No se pudo eliminar el PN: {message}", "pn_removed": "Registro del PN {pn} eliminado.", "pn_not_found": "No se encontró el PN {pn}.", "report_generated": "Informe técnico generado correctamente.", "save_report_error": "No se pudo guardar el informe: {message}", "technical_title": "Tablas técnicas — medios de shot peening", "technical_heading": "Tablas técnicas de medios y normas", "technical_subtitle": "Referencia rápida para análisis de esferas, granulometría, tipos de medios y normas aplicables.", "tab_analysis": "Análisis de esferas", "tab_grain_size": "Granulometría", "tab_media_types": "Tipos de medios", "tab_standards": "Normas",
    },
}

_TEXTS["PT"]["part_serial_number"] = "SN da peça"
_TEXTS["EN"]["part_serial_number"] = "Part serial number"
_TEXTS["ES"]["part_serial_number"] = "N.º de serie de la pieza"
_TEXTS["EN"]["example"] = "⟳ Reload"
_TEXTS["ES"]["example"] = "⟳ Recargar"
_TEXTS["EN"]["reference_cmm"] = "CMM Reference"
_TEXTS["ES"]["reference_cmm"] = "Referencia CMM"

# Textos de interface que não se encaixam nas chaves curtas acima. Mantê-los
# aqui evita que módulos de dados e telas técnicas carreguem conteúdo em um
# idioma fixo.
_TEXTS["PT"].update({
    "required_peening_intensity": "Intensidade de peening",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "Referências SAE registradas; a conformidade exige validação do processo e dos dados do ensaio.",
    "unit_mm": "Milímetros (mm)", "unit_in": "Polegadas (in)",
    "exposure_seconds": "Segundos", "exposure_passes": "Passes", "exposure_rotations": "Rotações", "exposure_cycles": "Ciclos", "exposure_inverse_feed": "Inverso do avanço",
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C", "curve_identifier": "Identificador: {code}",
    "deviation_placeholder": "Ex.: 0,005", "point_2t_legend": "Ponto 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Faixa de intensidade de peening: {value} {unit}",
    "shot": "Esfera", "hardness": "Dureza", "nozzle": "Bico", "injector": "Injetor", "distance": "Distância", "angle": "Ângulo", "pressure": "Pressão",
    "registered_deviations": "Desvios de lâmina cadastrados", "standard_default": "SAE J443 e SAE J2597", "standard_other": "Outra norma (informar em observações)",
    "pn_required_save": "Informe a Peça / PN para salvar o cadastro.", "pn_required_remove": "Informe a Peça / PN a remover.",
    "invalid_arc_unit": "Unidade da altura do arco inválida.", "deviation_not_finite": "O desvio da lâmina deve ser um número finito.",
    "deviation_per_height": "Informe um desvio para cada altura do arco medida.", "negative_compensated": "O desvio informado torna alguma altura do arco compensada negativa.",
    "data_vectors": "Tempo e altura devem ser vetores do mesmo tamanho.", "data_finite": "Tempo e altura devem conter apenas números finitos.",
    "exposure_negative": "Os tempos de exposição não podem ser negativos.", "arc_negative": "As alturas de arco não podem ser negativas.",
    "min_measurements": "A curva exige pelo menos 4 medições válidas.", "min_nonzero_arc": "A curva exige pelo menos 4 alturas de arco não nulas.",
    "distinct_exposure": "Informe pelo menos quatro valores de exposição distintos.", "varying_arc": "As alturas precisam variar para calcular a saturação.",
    "saturation_rate": "Não foi possível determinar uma taxa de saturação positiva.",
    "curve_valid": "CURVA VÁLIDA — critério SAE J443 atendido.",
    "curve_invalid": "CURVA NÃO VÁLIDA — {reasons}",
    "curve_invalid_before_t": "sem medição em/antes de T", "curve_invalid_2t": "a exposição máxima não alcança 2T",
    "curve_invalid_descending_arc": "a altura medida diminui com o aumento da exposição",
        "curve_invalid_type2_10_percent": "o aumento de T para 2T excede 10%", "curve_invalid_fit": "o ajuste aos dados é insuficiente (R² abaixo de 0,80)",
    "curve_validation": "Validação da curva", "curve_2t_increase": "Aumento de T para 2T",
    "intensity_out_of_required_range": "ATENÇÃO: H(T) = {value:.4f} {unit} está fora da faixa requerida ({lower:.4f} a {upper:.4f} {unit}).",
})
_TEXTS["EN"].update({
    "required_peening_intensity": "Peening intensity",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "SAE references are registered; compliance requires validation of the process and test data.",
    "unit_mm": "Millimetres (mm)", "unit_in": "Inches (in)",
    "exposure_seconds": "Seconds", "exposure_passes": "Passes", "exposure_rotations": "Rotations", "exposure_cycles": "Cycles", "exposure_inverse_feed": "Inverse feed rate",
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C", "curve_identifier": "Identifier: {code}",
    "deviation_placeholder": "E.g.: 0.005", "point_2t_legend": "Point 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Peening intensity range: {value} {unit}",
    "shot": "Shot", "hardness": "Hardness", "nozzle": "Nozzle", "injector": "Injector", "distance": "Distance", "angle": "Angle", "pressure": "Pressure",
    "registered_deviations": "Registered strip deviations", "standard_default": "SAE J443 and SAE J2597", "standard_other": "Other standard (enter in notes)",
    "pn_required_save": "Enter the Part / PN to save the record.", "pn_required_remove": "Enter the Part / PN to remove.",
    "invalid_arc_unit": "Invalid arc-height unit.", "deviation_not_finite": "The strip deviation must be a finite number.",
    "deviation_per_height": "Enter one deviation for each measured arc height.", "negative_compensated": "The supplied deviation makes a compensated arc height negative.",
    "data_vectors": "Time and height must be vectors of the same size.", "data_finite": "Time and height must contain only finite numbers.",
    "exposure_negative": "Exposure times cannot be negative.", "arc_negative": "Arc heights cannot be negative.",
    "min_measurements": "The curve requires at least 4 valid measurements.", "min_nonzero_arc": "The curve requires at least 4 non-zero arc heights.",
    "distinct_exposure": "Enter at least four distinct exposure values.", "varying_arc": "Arc heights must vary to calculate saturation.",
    "saturation_rate": "Could not determine a positive saturation rate.",
    "curve_valid": "VALID CURVE — SAE J443 criterion met.",
    "curve_invalid": "INVALID CURVE — {reasons}",
    "curve_invalid_before_t": "no measurement at/before T", "curve_invalid_2t": "maximum exposure does not reach 2T",
    "curve_invalid_descending_arc": "measured arc height decreases as exposure increases",
        "curve_invalid_type2_10_percent": "the increase from T to 2T exceeds 10%", "curve_invalid_fit": "the fit to the data is insufficient (R² below 0.80)",
    "curve_validation": "Curve validation", "curve_2t_increase": "Increase from T to 2T",
    "intensity_out_of_required_range": "WARNING: H(T) = {value:.4f} {unit} is outside the required range ({lower:.4f} to {upper:.4f} {unit}).",
})
_TEXTS["ES"].update({
    "required_peening_intensity": "Intensidad de peening",
    "references_sae": "SAE J443_202512 — Procedures for Determining and Verifying Peening Intensity\nSAE J2597_201709 — Computer Generated Shot Peening Saturation Curves",
    "normative_notice": "Las referencias SAE están registradas; la conformidad exige validar el proceso y los datos del ensayo.",
    "unit_mm": "Milímetros (mm)", "unit_in": "Pulgadas (in)",
    "exposure_seconds": "Segundos", "exposure_passes": "Pasadas", "exposure_rotations": "Rotaciones", "exposure_cycles": "Ciclos", "exposure_inverse_feed": "Inverso del avance",
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C", "curve_identifier": "Identificador: {code}",
    "deviation_placeholder": "Ej.: 0,005", "point_2t_legend": "Punto 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Rango de intensidad de peening: {value} {unit}",
    "shot": "Esfera", "hardness": "Dureza", "nozzle": "Boquilla", "injector": "Inyector", "distance": "Distancia", "angle": "Ángulo", "pressure": "Presión",
    "registered_deviations": "Desviaciones de lámina registradas", "standard_default": "SAE J443 y SAE J2597", "standard_other": "Otra norma (indicar en observaciones)",
    "pn_required_save": "Introduzca la Pieza / PN para guardar el registro.", "pn_required_remove": "Introduzca la Pieza / PN que desea eliminar.",
    "invalid_arc_unit": "Unidad de altura de arco no válida.", "deviation_not_finite": "La desviación de la lámina debe ser un número finito.",
    "deviation_per_height": "Introduzca una desviación para cada altura de arco medida.", "negative_compensated": "La desviación indicada hace negativa alguna altura de arco compensada.",
    "data_vectors": "El tiempo y la altura deben ser vectores del mismo tamaño.", "data_finite": "El tiempo y la altura solo deben contener números finitos.",
    "exposure_negative": "Los tiempos de exposición no pueden ser negativos.", "arc_negative": "Las alturas de arco no pueden ser negativas.",
    "min_measurements": "La curva requiere al menos 4 mediciones válidas.", "min_nonzero_arc": "La curva requiere al menos 4 alturas de arco no nulas.",
    "distinct_exposure": "Introduzca al menos cuatro valores de exposición distintos.", "varying_arc": "Las alturas de arco deben variar para calcular la saturación.",
    "saturation_rate": "No fue posible determinar una tasa de saturación positiva.",
    "curve_valid": "CURVA VÁLIDA — criterio SAE J443 cumplido.",
    "curve_invalid": "CURVA NO VÁLIDA — {reasons}",
    "curve_invalid_before_t": "sin medicion en/antes de T", "curve_invalid_2t": "la exposicion maxima no alcanza 2T",
    "curve_invalid_descending_arc": "la altura medida disminuye al aumentar la exposición",
        "curve_invalid_type2_10_percent": "el aumento de T a 2T supera el 10%", "curve_invalid_fit": "el ajuste a los datos es insuficiente (R² inferior a 0,80)",
    "curve_validation": "Validación de la curva", "curve_2t_increase": "Aumento de T a 2T",
    "intensity_out_of_required_range": "ATENCIÓN: H(T) = {value:.4f} {unit} está fuera del rango requerido ({lower:.4f} a {upper:.4f} {unit}).",
})

_TEXTS["PT"].update({
    "company_logo": "Logo da empresa",
    "select_company_logo": "Selecionar logo da empresa",
    "image_files": "Arquivos de imagem",
    "browse_image": "Procurar...",
    "clear_logo": "Limpar",
    "company_logo_help": "A imagem é copiada para os dados do aplicativo e aparece no cabeçalho dos novos relatórios.",
    "invalid_company_logo": "Erro: selecione um arquivo de imagem válido.",
})
_TEXTS["EN"].update({
    "company_logo": "Company logo",
    "select_company_logo": "Select company logo",
    "image_files": "Image files",
    "browse_image": "Browse...",
    "clear_logo": "Clear",
    "company_logo_help": "The image is copied to the application data and appears in the header of new reports.",
    "invalid_company_logo": "Error: select a valid image file.",
})
_TEXTS["ES"].update({
    "company_logo": "Logo de la empresa",
    "select_company_logo": "Seleccionar logo de la empresa",
    "image_files": "Archivos de imagen",
    "browse_image": "Buscar...",
    "clear_logo": "Limpiar",
    "company_logo_help": "La imagen se copia a los datos de la aplicación y aparece en el encabezado de los nuevos informes.",
    "invalid_company_logo": "Error: seleccione un archivo de imagen válido.",
})

_TEXTS["PT"].update({
    "report_prefix": "Prefixo do número do relatório",
    "report_prefix_help": "Exemplo: SP gera SP-001-26 e reinicia automaticamente a cada ano.",
    "report_number": "Relatório nº",
    "generated_reports": "Relatórios gerados",
    "report_search_placeholder": "Buscar por número, PN ou SN",
    "reprint_report": "Reimprimir",
    "no_generated_reports": "Nenhum relatório gerado foi encontrado.",
    "report_not_found": "Relatório não encontrado.",
    "report_reprint_ready": "Relatório {number} convertido em PDF e enviado para a impressora padrão.",
    "report_generated_numbered": "Relatório {number} gerado e arquivado com sucesso.",
})
_TEXTS["EN"].update({
    "report_prefix": "Report number prefix",
    "report_prefix_help": "Example: SP generates SP-001-26 and restarts automatically each year.",
    "report_number": "Report no.",
    "generated_reports": "Generated reports",
    "report_search_placeholder": "Search by number, PN or serial number",
    "reprint_report": "Reprint",
    "no_generated_reports": "No generated reports were found.",
    "report_not_found": "Report not found.",
    "report_reprint_ready": "Report {number} converted to PDF and sent to the default printer.",
    "report_generated_numbered": "Report {number} generated and archived successfully.",
})
_TEXTS["ES"].update({
    "report_prefix": "Prefijo del número de informe",
    "report_prefix_help": "Ejemplo: SP genera SP-001-26 y se reinicia automáticamente cada año.",
    "report_number": "Informe n.º",
    "generated_reports": "Informes generados",
    "report_search_placeholder": "Buscar por número, PN o serie",
    "reprint_report": "Reimprimir",
    "no_generated_reports": "No se encontraron informes generados.",
    "report_not_found": "Informe no encontrado.",
    "report_reprint_ready": "Informe {number} convertido a PDF y enviado a la impresora predeterminada.",
    "report_generated_numbered": "Informe {number} generado y archivado correctamente.",
})

_TEXTS["PT"].update({
    "current_month_reports_hint": "Exibindo os relatórios do mês atual. Pesquise para localizar qualquer relatório anterior.",
    "results_count": "Resultados ({count})",
    "displayed_count": "{count} relatório(s) exibido(s)",
    "measurements_count": "Medições ({count})",
    "individual_deviations_count": "Desvios individuais por lâmina ({unit}) — {count} item(ns)",
    "listed_count": "({count} item(ns))",
    "report_year": "Ano", "report_month": "Mês", "delete_report": "Excluir",
    "delete_report_confirmation": "Excluir definitivamente o relatório {number}? Esta ação será sincronizada com os outros computadores.",
    "report_deleted": "Relatório {number} excluído.",
    "tooltip_delete_report": "Exclui este relatório após confirmação.",
})
_TEXTS["EN"].update({
    "current_month_reports_hint": "Showing reports from the current month. Search to find any earlier report.",
    "results_count": "Results ({count})",
    "displayed_count": "{count} report(s) displayed",
    "measurements_count": "Measurements ({count})",
    "individual_deviations_count": "Individual strip deviations ({unit}) — {count} item(s)",
    "listed_count": "({count} item(s))",
    "report_year": "Year", "report_month": "Month", "delete_report": "Delete",
    "delete_report_confirmation": "Permanently delete report {number}? This action will be synchronized with the other computers.",
    "report_deleted": "Report {number} deleted.",
    "tooltip_delete_report": "Deletes this report after confirmation.",
})
_TEXTS["ES"].update({
    "current_month_reports_hint": "Mostrando los informes del mes actual. Busque para localizar informes anteriores.",
    "results_count": "Resultados ({count})",
    "displayed_count": "{count} informe(s) mostrado(s)",
    "measurements_count": "Mediciones ({count})",
    "individual_deviations_count": "Desviaciones individuales por lámina ({unit}) — {count} elemento(s)",
    "listed_count": "({count} elemento(s))",
    "report_year": "Año", "report_month": "Mes", "delete_report": "Eliminar",
    "delete_report_confirmation": "¿Eliminar definitivamente el informe {number}? Esta acción se sincronizará con los demás equipos.",
    "report_deleted": "Informe {number} eliminado.",
    "tooltip_delete_report": "Elimina este informe después de confirmarlo.",
})

_TECHNICAL_CONTENT = {
    "PT": {
        "analysis": ("Roteiro de análise de esferas / mídia metálica", "Use o roteiro junto com o plano de inspeção e o certificado do lote; ele não substitui ensaios nem critérios contratuais.", ("Item", "Verificação", "Finalidade"), (("Identificação", "Tipo, lote, fabricante e certificado", "Mantém a rastreabilidade da mídia usada."), ("Granulometria", "Ensaio por peneiras ASTM E11", "Confirma a distribuição e a designação SAE J444."), ("Forma", "Esfericidade, partículas quebradas e satélites", "Evita impacto irregular e acabamento inconsistente."), ("Dureza", "Faixa especificada para a mídia", "Influencia a energia transferida e a vida útil da esfera."), ("Composição", "Análise química conforme especificação", "Confirma o material, como aço fundido de alto carbono."), ("Integridade", "Trincas, porosidade, contaminação e oxidação", "Reduz risco de quebra e contaminação da peça."), ("Desempenho", "Teste mecânico / vida Ervin quando requerido", "Compara durabilidade e energia transmitida pela mídia."))),
        "grain": ("Granulometria de esfera conforme designação SAE J444", "A abertura nominal identifica a classe. A distribuição completa e seus limites devem ser conferidos na edição vigente da J444 e no certificado do lote.", ("Designação", "Abertura nominal (in)", "Abertura nominal (mm)", "Classe visual"), (("S70", "0.0070", "0,178", "Fina"), ("S110", "0.0110", "0,279", "Fina"), ("S170", "0.0170", "0,432", "Média"), ("S230", "0.0230", "0,584", "Média"), ("S280", "0.0280", "0,711", "Média"), ("S330", "0.0330", "0,838", "Média"), ("S390", "0.0390", "0,991", "Grossa"), ("S460", "0.0460", "1,168", "Grossa"), ("S550", "0.0550", "1,397", "Grossa"), ("S660", "0.0660", "1,676", "Muito grossa"), ("S780", "0.0780", "1,981", "Muito grossa"))),
        "media": ("Tipos de mídia", "Escolha conforme desenho, material da peça e processo aprovado.", ("Tipo", "Designação", "Referência", "Uso"), (("Esfera de aço fundido alto carbono", "S + designação", "SAE J827 e SAE J444", "Shot peening e limpeza."), ("Esfera de aço fundido baixo carbono", "S + designação", "SAE J2175 e SAE J444", "Quando a especificação exigir baixa dureza/carbono."), ("Arame cortado condicionado", "Diâmetro nominal", "SAE J441", "Mídia metálica de alta durabilidade."), ("Granalha angular de aço (grit)", "G + designação", "SAE J1993 e SAE J444", "Limpeza, decapagem e ancoragem; não substitui esfera sem aprovação."), ("Esfera de vidro ou cerâmica", "Conforme fornecedor", "Especificação do processo", "Mídias não metálicas para aplicações definidas."))),
        "standards": ("Normas de referência", "Verifique a revisão contratual antes de declarar conformidade.", ("Norma", "Assunto", "Aplicação no app"), (("SAE J444", "Classificação de tamanhos de esfera e granalha fundidas", "Define designações S/G e controle por peneiras."), ("SAE J827", "Esfera de aço fundido de alto carbono", "Composição e características físicas da esfera."), ("SAE J2175", "Esfera de aço fundido de baixo carbono", "Requisitos de composição, dureza, microestrutura e características físicas."), ("SAE J441", "Arame cortado", "Guia para seleção e uso de shot de arame cortado."), ("SAE J1993", "Granalha de aço fundido alto carbono", "Requisitos para grit usado em limpeza e ataque superficial."), ("SAE J445", "Teste mecânico de esfera e granalha metálicas", "Métodos laboratoriais para avaliar a mídia."), ("SAE J442", "Lâmina, suporte e medidor Almen", "Equipamentos e suprimentos para medição de altura do arco."), ("SAE J443", "Determinação e verificação da intensidade", "Curva de saturação e uso das lâminas Almen."), ("SAE J2277", "Cobertura de shot peening", "Método para determinar a cobertura do processo."), ("SAE J2597", "Curvas de saturação geradas por computador", "Orientação para curvas de saturação assistidas por software."), ("AMS2430 / AMS2431", "Processo e aquisição de mídia aeroespacial", "Aplicar somente quando exigido pelo desenho, contrato ou cliente."))),
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


_TEXTS["PT"].update({
    "strip_measurements_table": "Leituras e compensa\u00e7\u00f5es das l\u00e2minas",
    "reading_after_exposure": "Leitura ap\u00f3s exposi\u00e7\u00e3o",
    "compensated_value": "Valor compensado",
    "strip_compensation_formula": "Valor compensado = leitura ap\u00f3s exposi\u00e7\u00e3o \u2212 desvio da l\u00e2mina. Desvios negativos s\u00e3o aceitos e somados corretamente ao valor compensado.",
    "operator": "Operador",
    "quality_representative": "Inspetor Supervisor",
    "signatures": "Assinaturas",
    "integrity_sha256": "Integridade do relat\u00f3rio (SHA-256)",
    "integrity_sha256_note": "O SHA-256 \u00e9 calculado sobre o relat\u00f3rio com o pr\u00f3prio campo SHA normalizado, permitindo verificar altera\u00e7\u00f5es no documento.",
})
_TEXTS["EN"].update({
    "strip_measurements_table": "Strip readings and compensations",
    "reading_after_exposure": "Reading after exposure",
    "compensated_value": "Compensated value",
    "strip_compensation_formula": "Compensated value = reading after exposure \u2212 strip deviation. Negative deviations are accepted and correctly added to the compensated value.",
    "operator": "Operator",
    "quality_representative": "Supervisor Inspector",
    "signatures": "Signatures",
    "integrity_sha256": "Report integrity (SHA-256)",
    "integrity_sha256_note": "The SHA-256 is calculated over the report with its own SHA field normalized, allowing document changes to be verified.",
})
_TEXTS["ES"].update({
    "strip_measurements_table": "Lecturas y compensaciones de las l\u00e1minas",
    "reading_after_exposure": "Lectura despu\u00e9s de la exposici\u00f3n",
    "compensated_value": "Valor compensado",
    "strip_compensation_formula": "Valor compensado = lectura despu\u00e9s de la exposici\u00f3n \u2212 desviaci\u00f3n de la l\u00e1mina. Se aceptan desviaciones negativas y se suman correctamente al valor compensado.",
    "operator": "Operador",
    "quality_representative": "Inspector Supervisor",
    "signatures": "Firmas",
    "integrity_sha256": "Integridad del informe (SHA-256)",
    "integrity_sha256_note": "El SHA-256 se calcula sobre el informe con su propio campo SHA normalizado, lo que permite verificar cambios en el documento.",
})


_TEXTS["PT"].update({
    "curve_source_latest": "Dados da curva exibida: última curva salva",
    "curve_source_selected": "Dados da curva exibida: cadastro selecionado — Router: {router} | PN: {pn} | SN: {sn}",
    "curve_source_example": "Dados da curva exibida: exemplo padrão",
    "tooltip_add_row": "Adiciona uma nova linha de medição.",
    "tooltip_remove_row": "Remove a última linha de medição.",
    "tooltip_reload": "Restaura a última curva de saturação para análise.",
    "tooltip_settings": "Abre as configurações de unidades, lâminas e idioma.",
    "tooltip_calculate": "Calcula a curva de saturação e atualiza o gráfico.",
    "tooltip_generate_report": "Abre a tela para gerenciar os dados e gerar o relatório técnico.",
    "tooltip_print_chart": "Envia o gráfico de saturação para a impressora padrão.",
    "tooltip_generated_reports": "Consulta e reimprime relatórios técnicos já emitidos.",
    "tooltip_technical_tables": "Abre tabelas de referência sobre mídia e normas técnicas.",
    "tooltip_browse_logo": "Seleciona a imagem do logo que aparecerá nos novos relatórios.",
    "tooltip_clear_logo": "Remove o logo selecionado dos novos relatórios.",
    "tooltip_remove_blade": "Remove esta lâmina e seu desvio cadastrado.",
    "tooltip_add_blade": "Adiciona uma lâmina para cadastrar seu desvio individual.",
    "tooltip_apply_settings": "Salva e aplica as configurações informadas.",
    "tooltip_search_pn": "Busca cadastros por Router, PN, SN, faixa de intensidade ou código da curva.",
    "tooltip_save_update_pn": "Salva um novo cadastro de PN ou atualiza o cadastro atual.",
    "tooltip_delete_pn": "Exclui permanentemente o cadastro de PN informado.",
    "tooltip_generate_html": "Gera, numera e arquiva o relatório técnico em HTML.",
    "tooltip_reprint_report": "Converte a versão arquivada em PDF antes de enviá-la à impressora padrão.",
    "tooltip_search_reports": "Filtra a lista de relatórios emitidos.",
})
_TEXTS["EN"].update({
    "curve_source_latest": "Displayed curve data: latest saved curve",
    "curve_source_selected": "Displayed curve data: selected record — Router: {router} | PN: {pn} | SN: {sn}",
    "curve_source_example": "Displayed curve data: default example",
    "tooltip_add_row": "Adds a new measurement row.",
    "tooltip_remove_row": "Removes the last measurement row.",
    "tooltip_reload": "Restores the last saturation curve for analysis.",
    "tooltip_settings": "Opens unit, strip and language settings.",
    "tooltip_calculate": "Calculates the saturation curve and updates the chart.",
    "tooltip_generate_report": "Opens the screen to manage data and generate the technical report.",
    "tooltip_print_chart": "Sends the saturation chart to the default printer.",
    "tooltip_generated_reports": "Views and reprints issued technical reports.",
    "tooltip_technical_tables": "Opens reference tables for media and technical standards.",
    "tooltip_browse_logo": "Selects the logo image shown in new reports.",
    "tooltip_clear_logo": "Removes the selected logo from new reports.",
    "tooltip_remove_blade": "Removes this strip and its registered deviation.",
    "tooltip_add_blade": "Adds a strip to register its individual deviation.",
    "tooltip_apply_settings": "Saves and applies the entered settings.",
    "tooltip_search_pn": "Searches records by Router, PN, SN, intensity range or curve code.",
    "tooltip_save_update_pn": "Saves a new PN record or updates the current record.",
    "tooltip_delete_pn": "Permanently deletes the entered PN record.",
    "tooltip_generate_html": "Generates, numbers and archives the HTML technical report.",
    "tooltip_reprint_report": "Converts the archived report to PDF before sending it to the default printer.",
    "tooltip_search_reports": "Filters the list of issued reports.",
})
_TEXTS["ES"].update({
    "curve_source_latest": "Datos de curva mostrados: última curva guardada",
    "curve_source_selected": "Datos de curva mostrados: registro seleccionado — Router: {router} | PN: {pn} | SN: {sn}",
    "curve_source_example": "Datos de curva mostrados: ejemplo predeterminado",
    "tooltip_add_row": "Añade una nueva fila de medición.",
    "tooltip_remove_row": "Elimina la última fila de medición.",
    "tooltip_reload": "Restaura la última curva de saturación para el análisis.",
    "tooltip_settings": "Abre la configuración de unidades, láminas e idioma.",
    "tooltip_calculate": "Calcula la curva de saturación y actualiza el gráfico.",
    "tooltip_generate_report": "Abre la pantalla para gestionar los datos y generar el informe técnico.",
    "tooltip_print_chart": "Envía el gráfico de saturación a la impresora predeterminada.",
    "tooltip_generated_reports": "Consulta y reimprime informes técnicos emitidos.",
    "tooltip_technical_tables": "Abre tablas de referencia de medios y normas técnicas.",
    "tooltip_browse_logo": "Selecciona la imagen del logo que aparecerá en los nuevos informes.",
    "tooltip_clear_logo": "Elimina el logo seleccionado de los nuevos informes.",
    "tooltip_remove_blade": "Elimina esta lámina y su desviación registrada.",
    "tooltip_add_blade": "Añade una lámina para registrar su desviación individual.",
    "tooltip_apply_settings": "Guarda y aplica la configuración ingresada.",
    "tooltip_search_pn": "Busca registros por Router, PN, SN, rango de intensidad o código de curva.",
    "tooltip_save_update_pn": "Guarda un nuevo registro de PN o actualiza el registro actual.",
    "tooltip_delete_pn": "Elimina permanentemente el registro de PN ingresado.",
    "tooltip_generate_html": "Genera, numera y archiva el informe técnico en HTML.",
    "tooltip_reprint_report": "Convierte la versión archivada a PDF antes de enviarla a la impresora predeterminada.",
    "tooltip_search_reports": "Filtra la lista de informes emitidos.",
})

_TEXTS["PT"].update({
    "company_name": "ROUTER",
    "piece_pn": "PN",
})
_TEXTS["EN"].update({
    "company_name": "ROUTER",
    "piece_pn": "PN",
})
_TEXTS["ES"].update({
    "company_name": "ROUTER",
    "piece_pn": "PN",
})

_TEXTS["PT"].update({
    "tooltip_developer_info": "Mostra as informações do desenvolvedor do sistema.",
    "tooltip_license_sync": "Mostra a licença do sistema e a chave de sincronização em nuvem.",
    "tooltip_about_system": "Mostra a versão e as informações gerais do sistema.",
})
_TEXTS["EN"].update({
    "tooltip_developer_info": "Shows the system developer information.",
    "tooltip_license_sync": "Shows the system license and cloud synchronization key.",
    "tooltip_about_system": "Shows the system version and general information.",
})
_TEXTS["ES"].update({
    "tooltip_developer_info": "Muestra la informacion del desarrollador del sistema.",
    "tooltip_license_sync": "Muestra la licencia del sistema y la clave de sincronizacion en la nube.",
    "tooltip_about_system": "Muestra la version y la informacion general del sistema.",
})

_TEXTS["PT"].update({
    "developer_info_title": "Informações do desenvolvedor",
    "developer_info_subtitle": "Créditos e canais oficiais de atendimento.",
    "developer_team": "Equipe de desenvolvimento",
    "developer_agents": "Agentes",
    "developer_label": "Desenvolvedor",
    "email": "E-mail",
    "website": "Site",
    "information_copied": "Informação copiada para a área de transferência.",
    "tooltip_copy_info": "Copiar {label}",
    "tooltip_open_info": "Abrir {label}",
    "close": "Fechar",
    "tooltip_close_window": "Fechar esta janela",
    "info_screen_coming_soon": "Esta área está preparada para receber as próximas informações do sistema.",
    "license_sync_title": "Licença e sincronização",
    "about_system_title": "Sobre o sistema",
})
_TEXTS["EN"].update({
    "developer_info_title": "Developer information",
    "developer_info_subtitle": "Credits and official support channels.",
    "developer_team": "Development team",
    "developer_agents": "Agents",
    "developer_label": "Developer",
    "email": "Email",
    "website": "Website",
    "information_copied": "Information copied to the clipboard.",
    "tooltip_copy_info": "Copy {label}",
    "tooltip_open_info": "Open {label}",
    "close": "Close",
    "tooltip_close_window": "Close this window",
    "info_screen_coming_soon": "This area is ready to receive the system's upcoming information.",
    "license_sync_title": "License and synchronization",
    "about_system_title": "About the system",
})
_TEXTS["ES"].update({
    "developer_info_title": "Información del desarrollador",
    "developer_info_subtitle": "Créditos y canales oficiales de atención.",
    "developer_team": "Equipo de desarrollo",
    "developer_agents": "Agentes",
    "developer_label": "Desarrollador",
    "email": "Correo electrónico",
    "website": "Sitio web",
    "information_copied": "Información copiada al portapapeles.",
    "tooltip_copy_info": "Copiar {label}",
    "tooltip_open_info": "Abrir {label}",
    "close": "Cerrar",
    "tooltip_close_window": "Cerrar esta ventana",
    "info_screen_coming_soon": "Esta área está preparada para recibir la próxima información del sistema.",
    "license_sync_title": "Licencia y sincronización",
    "about_system_title": "Acerca del sistema",
})

_TEXTS["PT"].update({
    "about_system_subtitle": "Informações operacionais, rastreabilidade e uso do aplicativo.",
    "system_product": "Produto", "system_product_value": "Curv Saturation — Curva de Saturação Almen",
    "system_version": "Versão",
    "system_scope": "Função principal", "system_scope_value": "Cálculo, análise e emissão de relatórios técnicos de curva de saturação.",
    "system_sync": "Sincronização", "system_sync_value": "PNs, curvas e relatórios podem ser sincronizados entre computadores com a mesma licença ativa.",
    "system_offline": "Operação sem internet", "system_offline_value": "O banco local continua disponível; as alterações são sincronizadas quando a conexão retornar.",
    "system_references_info": "Referências", "system_references_info_value": "SAE J443 e SAE J2597 apoiam a análise; valide sempre o processo e a revisão contratual aplicável.",
    "open_user_manual": "Abrir manual de uso", "tooltip_open_user_manual": "Abre o guia de operação do software.",
    "user_manual_title": "Manual de uso", "user_manual_subtitle": "Roteiro rápido para operar o Curv Saturation.",
    "manual_step_1_title": "Registrar as medições", "manual_step_1_text": "Informe pelo menos quatro pares de exposição e altura do arco. Se necessário, selecione a lâmina cadastrada para aplicar sua compensação.",
    "manual_step_2_title": "Calcular e avaliar a curva", "manual_step_2_text": "Clique em Calcular e gerar gráfico. Confira T, 2T, intensidade H(T), R² e as faixas de intensidade antes de emitir um documento.",
    "manual_step_3_title": "Cadastrar o PN e gerar o relatório", "manual_step_3_text": "Abra Gerar relatório, preencha os dados da peça e processo, salve ou atualize o PN e gere o HTML. O relatório recebe número e SHA-256 para rastreabilidade.",
    "manual_step_4_title": "Consultar, reimprimir ou excluir", "manual_step_4_text": "Relatórios gerados exibem inicialmente apenas o mês atual. Use a busca por número, PN ou SN para localizar históricos, reimprimir a versão arquivada ou excluí-la após confirmação.",
    "manual_step_5_title": "Sincronizar e trabalhar offline", "manual_step_5_text": "Na tela Licença e sincronização, ative a sincronização automática ou use Sincronizar dados. Sem internet, o sistema opera com o banco local e envia as alterações quando a conexão voltar.",
})
_TEXTS["EN"].update({
    "about_system_subtitle": "Operational information, traceability and application use.",
    "system_product": "Product", "system_product_value": "Curv Saturation — Almen Saturation Curve",
    "system_version": "Version",
    "system_scope": "Main function", "system_scope_value": "Calculation, analysis and issuance of saturation curve technical reports.",
    "system_sync": "Synchronization", "system_sync_value": "PNs, curves and reports can be synchronized between computers with the same active license.",
    "system_offline": "Offline operation", "system_offline_value": "The local database remains available; changes are synchronized when the connection returns.",
    "system_references_info": "References", "system_references_info_value": "SAE J443 and SAE J2597 support the analysis; always validate the process and applicable contractual revision.",
    "open_user_manual": "Open user manual", "tooltip_open_user_manual": "Opens the software operation guide.",
    "user_manual_title": "User manual", "user_manual_subtitle": "Quick guide to operate Curv Saturation.",
    "manual_step_1_title": "Enter measurements", "manual_step_1_text": "Enter at least four exposure and arc-height pairs. If required, select the registered strip to apply its compensation.",
    "manual_step_2_title": "Calculate and review the curve", "manual_step_2_text": "Click Calculate and generate chart. Review T, 2T, H(T) intensity, R² and intensity ranges before issuing a document.",
    "manual_step_3_title": "Register the PN and generate the report", "manual_step_3_text": "Open Generate report, enter part and process data, save or update the PN, and generate the HTML. The report receives a number and SHA-256 for traceability.",
    "manual_step_4_title": "Find, reprint or delete", "manual_step_4_text": "Generated reports initially show only the current month. Search by number, PN or serial number to find history, reprint the archived version or delete it after confirmation.",
    "manual_step_5_title": "Synchronize and work offline", "manual_step_5_text": "In License and synchronization, enable automatic synchronization or use Sync data. Without internet the system uses the local database and sends changes once connected.",
})
_TEXTS["ES"].update({
    "about_system_subtitle": "Información operativa, trazabilidad y uso de la aplicación.",
    "system_product": "Producto", "system_product_value": "Curv Saturation — Curva de Saturación Almen",
    "system_version": "Versión",
    "system_scope": "Función principal", "system_scope_value": "Cálculo, análisis y emisión de informes técnicos de curvas de saturación.",
    "system_sync": "Sincronización", "system_sync_value": "Los PN, curvas e informes pueden sincronizarse entre equipos con la misma licencia activa.",
    "system_offline": "Operación sin internet", "system_offline_value": "La base local sigue disponible; los cambios se sincronizan al volver la conexión.",
    "system_references_info": "Referencias", "system_references_info_value": "SAE J443 y SAE J2597 apoyan el análisis; valide siempre el proceso y la revisión contractual aplicable.",
    "open_user_manual": "Abrir manual de uso", "tooltip_open_user_manual": "Abre la guía de operación del software.",
    "user_manual_title": "Manual de uso", "user_manual_subtitle": "Guía rápida para utilizar Curv Saturation.",
    "manual_step_1_title": "Registrar mediciones", "manual_step_1_text": "Introduzca al menos cuatro pares de exposición y altura de arco. Si es necesario, seleccione la lámina registrada para aplicar su compensación.",
    "manual_step_2_title": "Calcular y evaluar la curva", "manual_step_2_text": "Haga clic en Calcular y generar gráfico. Revise T, 2T, intensidad H(T), R² y los rangos de intensidad antes de emitir un documento.",
    "manual_step_3_title": "Registrar el PN y generar el informe", "manual_step_3_text": "Abra Generar informe, complete los datos de la pieza y proceso, guarde o actualice el PN y genere el HTML. El informe recibe un número y SHA-256 para trazabilidad.",
    "manual_step_4_title": "Consultar, reimprimir o eliminar", "manual_step_4_text": "Los informes generados muestran inicialmente solo el mes actual. Busque por número, PN o serie para localizar históricos, reimprimir la versión archivada o eliminarla tras confirmación.",
    "manual_step_5_title": "Sincronizar y trabajar sin conexión", "manual_step_5_text": "En Licencia y sincronización, active la sincronización automática o use Sincronizar datos. Sin internet el sistema utiliza la base local y envía cambios al reconectarse.",
})


_TEXTS["PT"].update({
    "license_activation_title": "Ativação do sistema",
    "installation_key": "Chave desta instalação",
    "copy_key": "Copiar",
    "installation_key_copied": "Chave da instalação copiada. Envie-a ao fornecedor para gerar a ativação.",
    "activation_key": "Chave de ativação",
    "activation_key_placeholder": "Cole aqui a chave recebida",
    "activate_license": "Ativar",
    "license_pending": "Aguardando ativação. Copie a chave desta instalação para solicitar a licença.",
    "license_active": "Licença ativa para {organization}. Validade: {expires}.",
    "license_no_expiration": "sem expiração",
    "license_expired": "A licença registrada está expirada. Solicite uma nova chave de ativação.",
    "license_invalid": "A licença registrada não é válida para esta instalação.",
    "license_activation_error": "Não foi possível ativar: {message}",
    "tooltip_copy_installation_key": "Copiar a chave desta instalação",
    "tooltip_activate_license": "Validar e salvar a chave de ativação",
})
_TEXTS["EN"].update({
    "license_activation_title": "System activation",
    "installation_key": "This installation key",
    "copy_key": "Copy",
    "installation_key_copied": "Installation key copied. Send it to the supplier to generate the activation.",
    "activation_key": "Activation key",
    "activation_key_placeholder": "Paste the received key here",
    "activate_license": "Activate",
    "license_pending": "Activation pending. Copy this installation key to request the license.",
    "license_active": "License active for {organization}. Validity: {expires}.",
    "license_no_expiration": "no expiration",
    "license_expired": "The registered license has expired. Request a new activation key.",
    "license_invalid": "The registered license is not valid for this installation.",
    "license_activation_error": "Could not activate: {message}",
    "tooltip_copy_installation_key": "Copy this installation key",
    "tooltip_activate_license": "Validate and save the activation key",
})
_TEXTS["ES"].update({
    "license_activation_title": "Activación del sistema",
    "installation_key": "Clave de esta instalación",
    "copy_key": "Copiar",
    "installation_key_copied": "Clave de instalación copiada. Envíela al proveedor para generar la activación.",
    "activation_key": "Clave de activación",
    "activation_key_placeholder": "Pegue aquí la clave recibida",
    "activate_license": "Activar",
    "license_pending": "Activación pendiente. Copie la clave de esta instalación para solicitar la licencia.",
    "license_active": "Licencia activa para {organization}. Validez: {expires}.",
    "license_no_expiration": "sin vencimiento",
    "license_expired": "La licencia registrada ha expirado. Solicite una nueva clave de activación.",
    "license_invalid": "La licencia registrada no es válida para esta instalación.",
    "license_activation_error": "No se pudo activar: {message}",
    "tooltip_copy_installation_key": "Copiar la clave de esta instalación",
    "tooltip_activate_license": "Validar y guardar la clave de activación",
})


_TEXTS["PT"].update({
    "license_revoked": "A licença foi revogada pelo fornecedor. Solicite uma nova ativação.",
    "license_suspended": "A licença está suspensa. Entre em contato com o fornecedor.",
    "sync_license": "Sincronizar",
    "license_syncing": "Sincronizando licença com o servidor...",
    "license_sync_success": "Licença sincronizada com o servidor.",
    "license_sync_mismatch": "O servidor possui uma ativação diferente para esta instalação.",
    "license_sync_offline": "Servidor indisponível; a licença local continua válida.",
})
_TEXTS["EN"].update({
    "license_revoked": "The license was revoked by the supplier. Request a new activation.",
    "license_suspended": "The license is suspended. Contact the supplier.",
    "sync_license": "Sync",
    "license_syncing": "Synchronizing license with the server...",
    "license_sync_success": "License synchronized with the server.",
    "license_sync_mismatch": "The server has a different activation for this installation.",
    "license_sync_offline": "Server unavailable; the local license remains valid.",
})
_TEXTS["ES"].update({
    "license_revoked": "La licencia fue revocada por el proveedor. Solicite una nueva activación.",
    "license_suspended": "La licencia está suspendida. Contacte con el proveedor.",
    "sync_license": "Sincronizar",
    "license_syncing": "Sincronizando la licencia con el servidor...",
    "license_sync_success": "Licencia sincronizada con el servidor.",
    "license_sync_mismatch": "El servidor tiene una activación diferente para esta instalación.",
    "license_sync_offline": "Servidor no disponible; la licencia local sigue siendo válida.",
})


_TEXTS["PT"].update({
    "system_data_sync_title": "Dados compartilhados da empresa",
    "system_data_sync_description": "Sincroniza preferências, cadastros e curvas por PN, exclusões e relatórios emitidos entre os computadores com esta mesma licença.",
    "sync_system_data": "Sincronizar dados",
    "system_data_syncing": "Enviando e recebendo dados da empresa...",
    "system_data_sync_success": "Dados sincronizados. {records} cadastro(s) e {reports} relatório(s) atualizados neste computador.",
    "system_data_sync_error": "Não foi possível sincronizar os dados: {message}",
    "system_data_sync_requires_license": "Ative e sincronize uma licença válida antes de sincronizar os dados.",
    "automatic_sync_option": "Sincronizar automaticamente a cada {minutes} minutos",
    "automatic_sync_enabled": "Sincronização automática ativada. A próxima tentativa ocorrerá em até {minutes} minutos.",
    "automatic_sync_disabled": "Sincronização automática desativada neste computador.",
})
_TEXTS["EN"].update({
    "system_data_sync_title": "Shared company data",
    "system_data_sync_description": "Synchronizes preferences, PN records and curves, deletions, and issued reports between computers using this license.",
    "sync_system_data": "Sync data",
    "system_data_syncing": "Sending and receiving company data...",
    "system_data_sync_success": "Data synchronized. {records} record(s) and {reports} report(s) updated on this computer.",
    "system_data_sync_error": "Could not synchronize data: {message}",
    "system_data_sync_requires_license": "Activate and synchronize a valid license before synchronizing data.",
    "automatic_sync_option": "Synchronize automatically every {minutes} minutes",
    "automatic_sync_enabled": "Automatic synchronization enabled. The next attempt will occur within {minutes} minutes.",
    "automatic_sync_disabled": "Automatic synchronization disabled on this computer.",
})
_TEXTS["ES"].update({
    "system_data_sync_title": "Datos compartidos de la empresa",
    "system_data_sync_description": "Sincroniza preferencias, registros y curvas por PN, eliminaciones e informes emitidos entre los ordenadores con esta licencia.",
    "sync_system_data": "Sincronizar datos",
    "system_data_syncing": "Enviando y recibiendo datos de la empresa...",
    "system_data_sync_success": "Datos sincronizados. {records} registro(s) y {reports} informe(s) actualizados en este ordenador.",
    "system_data_sync_error": "No se pudieron sincronizar los datos: {message}",
    "system_data_sync_requires_license": "Active y sincronice una licencia válida antes de sincronizar los datos.",
    "automatic_sync_option": "Sincronizar automáticamente cada {minutes} minutos",
    "automatic_sync_enabled": "Sincronización automática activada. El próximo intento ocurrirá en hasta {minutes} minutos.",
    "automatic_sync_disabled": "Sincronización automática desactivada en este ordenador.",
})

_TEXTS["PT"].update({
    "html_report_heading": "Relatório técnico da curva de saturação",
    "report_page": "Página",
})
_TEXTS["EN"].update({
    "generate_report": "Manage Data and Report",
    "report_title": "Manage Data and Report",
    "report_heading": "Manage Data and Report",
    "html_report_heading": "Saturation curve technical report",
    "report_page": "Page",
})
_TEXTS["ES"].update({
    "generate_report": "Gestionar Datos e Informe",
    "report_title": "Gestionar Datos e Informe",
    "report_heading": "Gestionar Datos e Informe",
    "html_report_heading": "Informe técnico de la curva de saturación",
    "report_page": "Página",
})


def load_language() -> str:
    try:
        language = _load_settings().get("language", DEFAULT_LANGUAGE)
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
    configuracoes = _load_settings()
    configuracoes["language"] = language
    _save_settings(configuracoes)


def load_company_logo_path() -> str:
    """Retorna o caminho da logo corporativa configurada."""
    caminho = _load_settings().get("company_logo_path", "")
    return caminho if isinstance(caminho, str) else ""


def save_company_logo_path(caminho: str) -> None:
    """Persiste o caminho da cópia local da logo corporativa."""
    configuracoes = _load_settings()
    configuracoes["company_logo_path"] = caminho
    _save_settings(configuracoes)


def load_report_prefix() -> str:
    """Retorna o prefixo configurado para a numeração anual de relatórios."""
    prefixo = _load_settings().get("report_prefix", "REL")
    return prefixo.strip() if isinstance(prefixo, str) and prefixo.strip() else "REL"


def save_report_prefix(prefixo: str) -> None:
    configuracoes = _load_settings()
    configuracoes["report_prefix"] = str(prefixo or "").strip().upper() or "REL"
    _save_settings(configuracoes)


def _load_settings() -> dict:
    try:
        configuracoes = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return configuracoes if isinstance(configuracoes, dict) else {}


def _save_settings(configuracoes: dict) -> None:
    configuracoes = dict(configuracoes)
    configuracoes["cloud_updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _write_settings(configuracoes)


def _write_settings(configuracoes: dict) -> None:
    """Grava as configurações sem disputar o arquivo com outra instância."""
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{_SETTINGS_FILE.stem}.", suffix=".tmp", dir=_SETTINGS_FILE.parent, text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(configuracoes, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, _SETTINGS_FILE)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def get_shared_settings() -> tuple[dict, str | None]:
    """Retorna somente prefer\u00eancias que podem ser reutilizadas em outro PC.

    Caminhos de arquivos pertencem ao computador atual e, por isso, n\u00e3o s\u00e3o
    enviados. A licen\u00e7a fica em outro arquivo e nunca passa por esta fun\u00e7\u00e3o.
    """
    configuracoes = _load_settings()
    ignored = {"company_logo_path", "cloud_updated_at"}
    values = {key: value for key, value in configuracoes.items() if key not in ignored}
    updated_at = configuracoes.get("cloud_updated_at")
    return values, updated_at if isinstance(updated_at, str) else None


def apply_shared_settings(values: dict, updated_at: str | None) -> None:
    """Aplica prefer\u00eancias remotas sem sobrescrever caminhos locais."""
    if not isinstance(values, dict):
        return
    configuracoes = _load_settings()
    for key, value in values.items():
        if key not in {"company_logo_path", "cloud_updated_at"}:
            configuracoes[key] = value
    if updated_at:
        configuracoes["cloud_updated_at"] = updated_at
    _write_settings(configuracoes)


def tr(key: str, language: str | None = None, **values) -> str:
    language = language or load_language()
    text = _TEXTS.get(language, _TEXTS[DEFAULT_LANGUAGE]).get(key, _TEXTS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**values)


def technical_content(language: str | None = None) -> dict:
    """Retorna o conteúdo técnico integral no idioma selecionado."""
    return _TECHNICAL_CONTENT.get(language or load_language(), _TECHNICAL_CONTENT[DEFAULT_LANGUAGE])


def html_language(language: str | None = None) -> str:
    return {"PT": "pt-BR", "EN": "en", "ES": "es"}.get(language or load_language(), "pt-BR")


_TEXTS["PT"].update({
    "print_pdf": "Imprimir / salvar em PDF",
    "print_pdf_ready": "Relatório {number} aberto no navegador. Use Imprimir e Salvar como PDF.",
    "print_pdf_error": "Não foi possível abrir o relatório para impressão: {message}",
    "tooltip_print_pdf": "Abre o HTML arquivado no navegador para salvar o PDF com a impressão nativa.",
    "export_pdf": "Exportar PDF",
    "pdf_file": "Arquivo PDF",
    "pdf_export_ready": "Relatório {number} exportado em PDF.",
    "pdf_export_unavailable": "Navegador compatível não encontrado para exportar PDF.",
    "pdf_export_error": "Não foi possível exportar o PDF: {message}",
    "tooltip_export_pdf": "Exporta diretamente a versão arquivada em PDF.",
})
_TEXTS["EN"].update({
    "print_pdf": "Print / save as PDF",
    "print_pdf_ready": "Report {number} opened in the browser. Use Print and Save as PDF.",
    "print_pdf_error": "Could not open the report for printing: {message}",
    "tooltip_print_pdf": "Opens the archived HTML in the browser to save the PDF using native printing.",
    "export_pdf": "Export PDF",
    "pdf_file": "PDF file",
    "pdf_export_ready": "Report {number} exported to PDF.",
    "pdf_export_unavailable": "No compatible browser was found to export PDF.",
    "pdf_export_error": "Could not export PDF: {message}",
    "tooltip_export_pdf": "Directly exports the archived report as PDF.",
})
_TEXTS["ES"].update({
    "print_pdf": "Imprimir / guardar como PDF",
    "print_pdf_ready": "El informe {number} se abrió en el navegador. Use Imprimir y Guardar como PDF.",
    "print_pdf_error": "No se pudo abrir el informe para imprimir: {message}",
    "tooltip_print_pdf": "Abre el HTML archivado en el navegador para guardar el PDF con la impresión nativa.",
    "export_pdf": "Exportar PDF",
    "pdf_file": "Archivo PDF",
    "pdf_export_ready": "Informe {number} exportado a PDF.",
    "pdf_export_unavailable": "No se encontro un navegador compatible para exportar PDF.",
    "pdf_export_error": "No se pudo exportar el PDF: {message}",
    "tooltip_export_pdf": "Exporta directamente la version archivada a PDF.",
})

_TEXTS["PT"].update({
    "generate_html": "Gerar relatório",
    "report_file": "relatorio_curva_saturacao_almen.pdf",
    "numbered_report_file": "relatorio_{number}.pdf",
    "report_generated_numbered": "Relatório {number} exportado em PDF e arquivado com sucesso.",
    "tooltip_generate_html": "Gera, numera, arquiva e exporta o relatório técnico em PDF.",
})
_TEXTS["EN"].update({
    "generate_html": "Generate report",
    "report_file": "almen_saturation_curve_report.pdf",
    "numbered_report_file": "report_{number}.pdf",
    "report_generated_numbered": "Report {number} exported as PDF and archived successfully.",
    "tooltip_generate_html": "Generates, numbers, archives and exports the technical report as PDF.",
})
_TEXTS["ES"].update({
    "generate_html": "Generar informe",
    "report_file": "informe_curva_saturacion_almen.pdf",
    "numbered_report_file": "informe_{number}.pdf",
    "report_generated_numbered": "Informe {number} exportado a PDF y archivado correctamente.",
    "tooltip_generate_html": "Genera, numera, archiva y exporta el informe técnico a PDF.",
})

# Integração de análise granulométrica. O prefixo mantém as chaves agrupadas
# no mesmo catálogo usado por toda a aplicação.
_TEXTS["PT"].update({
    "sieve_aba": "Granulometria por peneiramento", "sieve_titulo": "Análise granulométrica por peneiras — SAE J444 / AMS 2430",
    "sieve_ajuda": "Informe a massa retida em cada peneira e no fundo. A SAE J444 exige o fundo para coletar o passante da última peneira, mas não define descarte ou limite independente nele: esse valor já é avaliado pelo limite cumulativo da última peneira. A amostra deve totalizar 100,0 g.",
    "sieve_designacao": "Designação da esfera", "sieve_tipo_amostra": "Condição da esfera", "sieve_esfera_nova": "Nova - especificação SAE J444", "sieve_esfera_usada": "Usada - controle de mídia AMS 2430",
    "sieve_peneira": "Peneira ASTM E11", "sieve_massa": "Massa retida na peneira (g)", "sieve_fundo": "Fundo da pilha (material passante pela última peneira)", "sieve_fundo_curto": "Fundo",
    "sieve_calcular": "Exibir resultados", "sieve_resultado": "Resultado", "sieve_fechar": "Fechar", "sieve_imprimir": "Imprimir / salvar em PDF",
    "sieve_impressao_pronta": "A análise foi aberta no navegador. Use Imprimir e Salvar como PDF.", "sieve_impressao_erro": "Não foi possível preparar a impressão: {erro}",
    "sieve_instrucoes_entrada": "Preencha as massas retidas e selecione Exibir resultados para consultar a análise em uma janela separada.",
    "sieve_total": "Massa total", "sieve_criterio": "Critério", "sieve_medido": "Resultado calculado", "sieve_situacao": "Situação",
    "sieve_conforme": "CONFORME", "sieve_nao_conforme": "NÃO CONFORME", "sieve_amostra_invalida": "AMOSTRA INVÁLIDA",
    "sieve_massa_aviso": "A massa deve ser 100,0 g (aceita-se diferença de até 0,1 g para conferência do lançamento).",
    "sieve_referencia": "Critério aplicado: SAE J444, com peneiras ASTM E11. O fundo é obrigatório como coletor, porém não é descarte nem tem limite próprio; a conformidade dele é a da última peneira. Revisões contratuais mais restritivas devem ser aplicadas separadamente.",
    "sieve_erro": "Corrija os valores informados: ", "sieve_retida": "retida", "sieve_passante": "passante cumulativo", "sieve_retida_acumulada": "retida acumulada",
    "sieve_fundo_limite": "Passante da última peneira", "sieve_fundo_sem_criterio": "Sem critério independente — já avaliado na peneira #{peneira}",
    "sieve_referencia_midia_em_uso": "Limites de mídia em uso — AMS 2430", "sieve_sem_limite_normativo": "Registro da distribuição",
    "sieve_limite_usada_retida": "retida ≤ 0,5%", "sieve_limite_usada_passante": "passante ≤ 20%", "sieve_registro_distribuicao": "Registro da distribuição",
    "sieve_registrado": "REGISTRADO", "sieve_conforme_ams2430": "CONFORME AMS 2430", "sieve_nao_conforme_ams2430": "NÃO CONFORME AMS 2430",
    "sieve_aviso_usada": "Para mídia em uso, a AMS 2430 controla a fração grosseira e os finos: no máximo 0,5% retido na peneira superior e no máximo 20% passante na peneira de manutenção da designação. Aplique somente quando esta revisão for exigida pelo seu processo, contrato ou cliente.",
    "sieve_referencia_usada": "Critério aplicado: parâmetros de mídia em uso da AMS 2430, com peneiras ASTM E11. A SAE J444 continua sendo a especificação de tamanho para mídia nova adquirida.",
    "sieve_salvar": "Salvar análise", "sieve_historico": "Histórico", "sieve_codigo": "Código / identificador", "sieve_codigo_opcional": "Automático se vazio",
    "sieve_salvo": "Análise salva com o código {codigo}.", "sieve_historico_titulo": "Histórico de análises por peneiras", "sieve_buscar": "Buscar", "sieve_data": "Data (DD/MM/AAAA)",
    "sieve_todas": "Todas", "sieve_situacao_conforme": "Conforme", "sieve_situacao_nao_conforme": "Não conforme", "sieve_situacao_invalida": "Amostra inválida",
    "sieve_nenhum_registro": "Nenhuma análise encontrada.", "sieve_ver": "Ver", "sieve_arquivada": "Análise arquivada — código {codigo}",
    "sieve_registros_exibidos": "São exibidos os 12 resultados mais recentes; refine a busca para localizar análises anteriores.",
    "sieve_limite_aceitavel": "Limite aceitável", "sieve_abertura": "Abertura", "sieve_limite_retida": "Retida ≤ {limite:.0f}%",
    "sieve_limite_acumulada": "Retida acum. ≥ {limite:.0f}% (passante ≤ {passante:.0f}%)",
    "sieve_fundo_criterio": "Passante # {peneira} ≤ {limite:.0f}%\n(não é limite próprio)",
    "sieve_unsupported_j444": "Designação SAE J444 não suportada: {designation!r}",
    "sieve_unsupported_ams2430": "Designação AMS 2430 não suportada: {designation!r}",
    "sieve_invalid_sample_type": "Tipo de amostra inválido. Use 'nova' ou 'usada'.",
    "sieve_invalid_mass": "Massa inválida na peneira {sieve}: {value!r}",
    "sieve_nonnegative_mass": "A massa na peneira {sieve} deve ser um número não negativo.",
    "sieve_empty_mass": "Informe as massas retidas; a massa total deve ser maior que zero.",
    "sieve_invalid_code": "O código deve ter de 3 a 32 caracteres: letras, números, _ ou -.",
    "sieve_duplicate_code": "Já existe uma análise com o código {code}.",
    "sieve_invalid_date": "Informe a data como DD/MM/AAAA ou AAAA-MM-DD.",
    "update_available_title": "Atualização disponível", "update_release_notes_fallback": "Consulte as notas da versão para mais detalhes.",
    "update_available_message": "Há uma nova versão disponível: {version}.\n\nVersão instalada: {installed}.\n\n{details}",
    "update_open_download": "{message}\n\nDeseja abrir o download agora?",
})
_TEXTS["EN"].update({
    "sieve_aba": "Sieve analysis", "sieve_titulo": "Sieve size analysis — SAE J444 / AMS 2430",
    "sieve_ajuda": "Enter the mass retained on each sieve and pan. SAE J444 requires the pan to collect material passing the last sieve, but sets no independent pan/discard limit: it is already assessed by the last sieve's cumulative limit. The sample must total 100.0 g.",
    "sieve_designacao": "Shot designation", "sieve_tipo_amostra": "Shot condition", "sieve_esfera_nova": "New - SAE J444 purchase specification", "sieve_esfera_usada": "Used - AMS 2430 in-process media control",
    "sieve_peneira": "ASTM E11 sieve", "sieve_massa": "Mass retained on sieve (g)", "sieve_fundo": "Pan (material passing the last sieve)", "sieve_fundo_curto": "Pan",
    "sieve_calcular": "Show results", "sieve_resultado": "Result", "sieve_fechar": "Close", "sieve_imprimir": "Print / save as PDF",
    "sieve_impressao_pronta": "The analysis was opened in the browser. Use Print and Save as PDF.", "sieve_impressao_erro": "Could not prepare printing: {erro}",
    "sieve_instrucoes_entrada": "Enter the retained masses and select Show results to view the analysis in a separate window.",
    "sieve_total": "Total mass", "sieve_criterio": "Criterion", "sieve_medido": "Calculated result", "sieve_situacao": "Status",
    "sieve_conforme": "CONFORMING", "sieve_nao_conforme": "NONCONFORMING", "sieve_amostra_invalida": "INVALID SAMPLE",
    "sieve_massa_aviso": "Mass must be 100.0 g (up to 0.1 g difference is accepted for entry checking).",
    "sieve_referencia": "Applied criterion: SAE J444 with ASTM E11 sieves. The pan is mandatory as collector, but is not discard and has no separate limit; its conformity is that of the last sieve. Apply any stricter contractual revision separately.",
    "sieve_erro": "Correct the entered values: ", "sieve_retida": "retained", "sieve_passante": "cumulative passing", "sieve_retida_acumulada": "cumulative retained",
    "sieve_fundo_limite": "Passing last sieve", "sieve_fundo_sem_criterio": "No independent criterion — already assessed at sieve #{peneira}",
    "sieve_referencia_midia_em_uso": "In-process media limits — AMS 2430", "sieve_sem_limite_normativo": "Distribution record",
    "sieve_limite_usada_retida": "retained ≤ 0.5%", "sieve_limite_usada_passante": "passing ≤ 20%", "sieve_registro_distribuicao": "Distribution record",
    "sieve_registrado": "RECORDED", "sieve_conforme_ams2430": "AMS 2430 CONFORMING", "sieve_nao_conforme_ams2430": "AMS 2430 NONCONFORMING",
    "sieve_aviso_usada": "For in-process media, AMS 2430 controls coarse material and fines: no more than 0.5% retained on the upper sieve and no more than 20% passing the maintenance sieve for the designation. Apply it only when this revision is required by your process, contract or customer.",
    "sieve_referencia_usada": "Applied criterion: AMS 2430 in-process media parameters with ASTM E11 sieves. SAE J444 remains the size specification for new purchased media.",
    "sieve_salvar": "Save analysis", "sieve_historico": "History", "sieve_codigo": "Code / identifier", "sieve_codigo_opcional": "Automatic when blank",
    "sieve_salvo": "Analysis saved with code {codigo}.", "sieve_historico_titulo": "Sieve analysis history", "sieve_buscar": "Search", "sieve_data": "Date (DD/MM/YYYY)",
    "sieve_todas": "All", "sieve_situacao_conforme": "Conforming", "sieve_situacao_nao_conforme": "Nonconforming", "sieve_situacao_invalida": "Invalid sample",
    "sieve_nenhum_registro": "No analyses found.", "sieve_ver": "View", "sieve_arquivada": "Archived analysis — code {codigo}",
    "sieve_registros_exibidos": "The 12 most recent results are shown; refine the search to locate earlier analyses.",
    "sieve_limite_aceitavel": "Acceptable limit", "sieve_abertura": "Opening", "sieve_limite_retida": "Retained ≤ {limite:.0f}%",
    "sieve_limite_acumulada": "Cumulative retained ≥ {limite:.0f}% (passing ≤ {passante:.0f}%)",
    "sieve_fundo_criterio": "Passing # {peneira} ≤ {limite:.0f}%\n(no independent limit)",
    "sieve_unsupported_j444": "Unsupported SAE J444 designation: {designation!r}",
    "sieve_unsupported_ams2430": "Unsupported AMS 2430 designation: {designation!r}",
    "sieve_invalid_sample_type": "Invalid sample type. Use 'new' or 'used'.",
    "sieve_invalid_mass": "Invalid mass at sieve {sieve}: {value!r}",
    "sieve_nonnegative_mass": "The mass at sieve {sieve} must be a non-negative number.",
    "sieve_empty_mass": "Enter the retained masses; total mass must be greater than zero.",
    "sieve_invalid_code": "The code must contain 3 to 32 characters: letters, numbers, _ or -.",
    "sieve_duplicate_code": "An analysis with code {code} already exists.",
    "sieve_invalid_date": "Enter the date as DD/MM/YYYY or YYYY-MM-DD.",
    "update_available_title": "Update available", "update_release_notes_fallback": "See the release notes for more details.",
    "update_available_message": "A new version is available: {version}.\n\nInstalled version: {installed}.\n\n{details}",
    "update_open_download": "{message}\n\nOpen the download now?",
})
_TEXTS["ES"].update({
    "sieve_aba": "Granulometría por tamizado", "sieve_titulo": "Análisis granulométrico por tamices — SAE J444 / AMS 2430",
    "sieve_ajuda": "Introduzca la masa retenida en cada tamiz y en el fondo. SAE J444 exige el fondo para recoger el material pasante del último tamiz, pero no define descarte ni límite independiente: ya se evalúa por el límite acumulado del último tamiz. La muestra debe totalizar 100,0 g.",
    "sieve_designacao": "Designación de la esfera", "sieve_tipo_amostra": "Condición de la esfera", "sieve_esfera_nova": "Nueva - especificación SAE J444", "sieve_esfera_usada": "Usada - control de medio AMS 2430",
    "sieve_peneira": "Tamiz ASTM E11", "sieve_massa": "Masa retenida en el tamiz (g)", "sieve_fundo": "Fondo de la pila (material pasante por el último tamiz)", "sieve_fundo_curto": "Fondo",
    "sieve_calcular": "Ver resultados", "sieve_resultado": "Resultado", "sieve_fechar": "Cerrar", "sieve_imprimir": "Imprimir / guardar como PDF",
    "sieve_impressao_pronta": "El análisis se abrió en el navegador. Use Imprimir y Guardar como PDF.", "sieve_impressao_erro": "No se pudo preparar la impresión: {erro}",
    "sieve_instrucoes_entrada": "Introduzca las masas retenidas y seleccione Ver resultados para consultar el análisis en una ventana separada.",
    "sieve_total": "Masa total", "sieve_criterio": "Criterio", "sieve_medido": "Resultado calculado", "sieve_situacao": "Situación",
    "sieve_conforme": "CONFORME", "sieve_nao_conforme": "NO CONFORME", "sieve_amostra_invalida": "MUESTRA INVÁLIDA",
    "sieve_massa_aviso": "La masa debe ser 100,0 g (se acepta una diferencia de hasta 0,1 g para revisar la entrada).",
    "sieve_referencia": "Criterio aplicado: SAE J444 con tamices ASTM E11. El fondo es obligatorio como colector, pero no es descarte ni tiene un límite propio; su conformidad es la del último tamiz. Aplique por separado cualquier revisión contractual más estricta.",
    "sieve_erro": "Corrija los valores introducidos: ", "sieve_retida": "retenida", "sieve_passante": "pasante acumulado", "sieve_retida_acumulada": "retenida acumulada",
    "sieve_fundo_limite": "Pasante del último tamiz", "sieve_fundo_sem_criterio": "Sin criterio independiente — ya evaluado en el tamiz #{peneira}",
    "sieve_referencia_midia_em_uso": "Límites de medio en uso — AMS 2430", "sieve_sem_limite_normativo": "Registro de distribución",
    "sieve_limite_usada_retida": "retenida ≤ 0,5%", "sieve_limite_usada_passante": "pasante ≤ 20%", "sieve_registro_distribuicao": "Registro de distribución",
    "sieve_registrado": "REGISTRADO", "sieve_conforme_ams2430": "CONFORME AMS 2430", "sieve_nao_conforme_ams2430": "NO CONFORME AMS 2430",
    "sieve_aviso_usada": "Para medio en uso, AMS 2430 controla la fracción gruesa y los finos: como máximo 0,5% retenido en el tamiz superior y como máximo 20% pasante por el tamiz de mantenimiento de la designación. Aplíquelo solo cuando esta revisión sea exigida por su proceso, contrato o cliente.",
    "sieve_referencia_usada": "Criterio aplicado: parámetros de medio en uso de la AMS 2430, con tamices ASTM E11. La SAE J444 sigue siendo la especificación de tamaño para medios nuevos adquiridos.",
    "sieve_salvar": "Guardar análisis", "sieve_historico": "Historial", "sieve_codigo": "Código / identificador", "sieve_codigo_opcional": "Automático si está vacío",
    "sieve_salvo": "Análisis guardado con el código {codigo}.", "sieve_historico_titulo": "Historial de análisis por tamices", "sieve_buscar": "Buscar", "sieve_data": "Fecha (DD/MM/AAAA)",
    "sieve_todas": "Todas", "sieve_situacao_conforme": "Conforme", "sieve_situacao_nao_conforme": "No conforme", "sieve_situacao_invalida": "Muestra inválida",
    "sieve_nenhum_registro": "No se encontraron análisis.", "sieve_ver": "Ver", "sieve_arquivada": "Análisis archivado — código {codigo}",
    "sieve_registros_exibidos": "Se muestran los 12 resultados más recientes; refine la búsqueda para localizar análisis anteriores.",
    "sieve_limite_aceitavel": "Límite aceptable", "sieve_abertura": "Abertura", "sieve_limite_retida": "Retenida ≤ {limite:.0f}%",
    "sieve_limite_acumulada": "Retenida acum. ≥ {limite:.0f}% (pasante ≤ {passante:.0f}%)",
    "sieve_fundo_criterio": "Pasante # {peneira} ≤ {limite:.0f}%\n(no es un límite propio)",
    "sieve_unsupported_j444": "Designación SAE J444 no compatible: {designation!r}",
    "sieve_unsupported_ams2430": "Designación AMS 2430 no compatible: {designation!r}",
    "sieve_invalid_sample_type": "Tipo de muestra no válido. Use 'nueva' o 'usada'.",
    "sieve_invalid_mass": "Masa no válida en el tamiz {sieve}: {value!r}",
    "sieve_nonnegative_mass": "La masa en el tamiz {sieve} debe ser un número no negativo.",
    "sieve_empty_mass": "Introduzca las masas retenidas; la masa total debe ser mayor que cero.",
    "sieve_invalid_code": "El código debe tener entre 3 y 32 caracteres: letras, números, _ o -.",
    "sieve_duplicate_code": "Ya existe un análisis con el código {code}.",
    "sieve_invalid_date": "Introduzca la fecha como DD/MM/AAAA o AAAA-MM-DD.",
    "update_available_title": "Actualización disponible", "update_release_notes_fallback": "Consulte las notas de la versión para obtener más detalles.",
    "update_available_message": "Hay una nueva versión disponible: {version}.\n\nVersión instalada: {installed}.\n\n{details}",
    "update_open_download": "{message}\n\n¿Desea abrir la descarga ahora?",
})


def sieve_texts(language: str | None = None) -> dict[str, str]:
    """Retorna o grupo de peneiramento sem formatar seus placeholders."""
    language = language or load_language()
    source = _TEXTS.get(language, _TEXTS[DEFAULT_LANGUAGE])
    return {key.removeprefix("sieve_"): value for key, value in source.items() if key.startswith("sieve_")}
