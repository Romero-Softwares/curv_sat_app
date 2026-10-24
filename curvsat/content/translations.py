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
        "report_heading": "Gerenciar Dados e Relatório", "pn_registry": "Cadastro por Router, PN ou SN", "search_pn": "Buscar Router, PN ou SN",
        "search_pn_placeholder": "Digite todo ou parte do Router, PN ou SN", "results": "Resultados", "search": "Buscar", "none_found": "Nenhum cadastro encontrado",
        "piece_identification": "Identificação e especificação", "process_data": "Dados do equipamento e processo", "value": "Valor",
        "standard": "Norma a ser atendida", "notes": "Observações", "save_update_pn": "Salvar / atualizar PN", "delete_pn": "Excluir PN",
        "generate_html": "Gerar relatório HTML", "piece_pn": "Peça / PN", "reference": "Referência", "reference_cmm": "Referência CMM", "repair": "Reparo", "equipment": "Equipamento",
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
        "app_title": "Almen Saturation Curve Calculator", "measurements": "Almen Strip Measurements", "add_row": "+ Row", "remove_row": "- Row", "example": "Example", "settings": "Settings", "calculate": "Calculate and Plot", "generate_report": "Manage Data and Report", "print_chart": "Print chart", "technical_tables": "Technical tables", "system_references": "SYSTEM STANDARD REFERENCES", "exposure": "Exposure", "arc_height": "Arc height", "blade_deviation": "Strip / deviation", "no_deviation": "No deviation", "saturation_time": "Sat. time (T)", "intensity": "Intensity H(T)", "point_2t": "Point (2T)", "height_2t": "Height H(2T)", "fit": "Fit R²", "deviations": "Deviations", "none_applied": "none applied", "chart_title": "Almen Saturation Curve", "measured_points": "Compensated measured points", "fitted_curve": "Fitted curve ($R^2={r2:.3f}$)", "saturation_point": "Saturation T ({value:.2f} {unit})", "row_incomplete": "Fill in exposure and arc height on row {index}.", "invalid_numbers": "Use valid numbers on row {index}.", "error": "Error: {message}", "print_windows_only": "Direct printing is only available on Windows.", "chart_sent_to_printer": "Chart sent to the default printer.", "print_error": "Could not start printing: {message}", "settings_title": "Curve settings", "general_parameters": "General parameters", "language": "System language", "arc_unit": "Arc height unit", "almen_type": "Almen strip type", "exposure_unit": "Exposure unit", "registered_references": "Registered standards references", "individual_deviations": "Individual strip deviations ({unit})", "deviation_help": "Register one row for each strip with its own deviation. Enter the deviation as indicated measurement − actual value; it is subtracted only from the associated arc height.", "blade_id": "Strip identification", "deviation": "Deviation", "remove": "Remove", "add_blade": "+ Add strip / deviation", "apply_settings": "Apply settings", "blade": "Strip", "invalid_deviation": "Error: enter a valid numeric deviation for strip {index}.", "blade_required": "Error: identify strip {index}.", "unique_blades": "Error: use unique names other than 'No deviation'.", "finite_deviations": "Error: strip deviations must be finite.", "report_title": "Manage Data and Report", "report_heading": "Manage Data and Report", "pn_registry": "Router, PN or SN registry", "search_pn": "Search Router, PN or SN", "search_pn_placeholder": "Type all or part of the Router, PN or SN", "results": "Results", "search": "Search", "none_found": "No records found", "piece_identification": "Identification and specification", "process_data": "Equipment and process data", "value": "Value", "standard": "Required standard", "notes": "Notes", "save_update_pn": "Save / update PN", "delete_pn": "Delete PN", "generate_html": "Generate HTML report", "piece_pn": "Part / PN", "reference": "Reference", "repair": "Repair", "equipment": "Equipment", "no_information": "Not informed.", "report_subtitle": "Technical record of the test and process parameters", "issued": "Issued on {date}", "piece_information": "Part information", "standard_to_meet": "Required standard", "process_parameters": "Process parameters", "curve_results": "Curve results", "saturation_chart": "Saturation chart", "save_report": "Save technical report", "html_report": "HTML report", "all_files": "All files", "report_file": "almen_saturation_curve_report.html", "pn_loaded": "PN {pn} record loaded.", "save_pn_error": "Could not save PN: {message}", "pn_saved": "PN {pn} record saved/updated.", "pn_required_delete": "Enter the Part / PN to delete.", "delete_registry": "Delete record", "delete_confirmation": "Permanently delete PN {pn} record?", "delete_pn_error": "Could not delete PN: {message}", "pn_removed": "PN {pn} record deleted.", "pn_not_found": "PN {pn} was not found.", "report_generated": "Technical report generated successfully.", "save_report_error": "Could not save report: {message}", "technical_title": "Technical tables — shot peening media", "technical_heading": "Technical media and standards tables", "technical_subtitle": "Quick reference for shot analysis, grain size, media types and applicable standards.", "tab_analysis": "Shot analysis", "tab_grain_size": "Grain size", "tab_media_types": "Media types", "tab_standards": "Standards",
    },
    "ES": {
        "app_title": "Calculadora de Curva de Saturación Almen", "measurements": "Mediciones de la Lámina Almen", "add_row": "+ Fila", "remove_row": "- Fila", "example": "Ejemplo", "settings": "Configuración", "calculate": "Calcular y Generar Gráfico", "generate_report": "Gestionar Datos e Informe", "print_chart": "Imprimir gráfico", "technical_tables": "Tablas técnicas", "system_references": "REFERENCIAS NORMATIVAS DEL SISTEMA", "exposure": "Exposición", "arc_height": "Altura de arco", "blade_deviation": "Lámina / desviación", "no_deviation": "Sin desviación", "saturation_time": "Tiempo sat. (T)", "intensity": "Intensidad H(T)", "point_2t": "Punto (2T)", "height_2t": "Altura H(2T)", "fit": "Ajuste R²", "deviations": "Desviaciones", "none_applied": "ninguna aplicada", "chart_title": "Curva de Saturación Almen", "measured_points": "Puntos medidos compensados", "fitted_curve": "Curva ajustada ($R^2={r2:.3f}$)", "saturation_point": "Saturación T ({value:.2f} {unit})", "row_incomplete": "Complete exposición y altura de arco en la fila {index}.", "invalid_numbers": "Use números válidos en la fila {index}.", "error": "Error: {message}", "print_windows_only": "La impresión directa solo está disponible en Windows.", "chart_sent_to_printer": "Gráfico enviado a la impresora predeterminada.", "print_error": "No se pudo iniciar la impresión: {message}", "settings_title": "Configuración de la curva", "general_parameters": "Parámetros generales", "language": "Idioma del sistema", "arc_unit": "Unidad de altura de arco", "almen_type": "Tipo de lámina Almen", "exposure_unit": "Unidad de exposición", "registered_references": "Referencias normativas registradas", "individual_deviations": "Desviaciones individuales por lámina ({unit})", "deviation_help": "Registre una fila para cada lámina que posea su propia desviación. Introduzca la desviación como medición indicada − valor real; solo se restará de la altura de arco asociada.", "blade_id": "Identificación de la lámina", "deviation": "Desviación", "remove": "Eliminar", "add_blade": "+ Añadir lámina / desviación", "apply_settings": "Aplicar configuración", "blade": "Lámina", "invalid_deviation": "Error: introduzca una desviación numérica válida en la lámina {index}.", "blade_required": "Error: identifique la lámina {index}.", "unique_blades": "Error: use identificaciones únicas y distintas de 'Sin desviación'.", "finite_deviations": "Error: las desviaciones deben ser finitas.", "report_title": "Gestionar Datos e Informe", "report_heading": "Gestionar Datos e Informe", "pn_registry": "Registro por Router, PN o SN", "search_pn": "Buscar Router, PN o SN", "search_pn_placeholder": "Escriba todo o parte del Router, PN o SN", "results": "Resultados", "search": "Buscar", "none_found": "No se encontraron registros", "piece_identification": "Identificación y especificación", "process_data": "Datos del equipo y proceso", "value": "Valor", "standard": "Norma requerida", "notes": "Observaciones", "save_update_pn": "Guardar / actualizar PN", "delete_pn": "Eliminar PN", "generate_html": "Generar informe HTML", "piece_pn": "Pieza / PN", "reference": "Referencia", "repair": "Reparación", "equipment": "Equipo", "no_information": "No informado.", "report_subtitle": "Registro técnico de ensayo y parámetros del proceso", "issued": "Emitido el {date}", "piece_information": "Información de la pieza", "standard_to_meet": "Norma requerida", "process_parameters": "Parámetros del proceso", "curve_results": "Resultados de la curva", "saturation_chart": "Gráfico de saturación", "save_report": "Guardar informe técnico", "html_report": "Informe HTML", "all_files": "Todos los archivos", "report_file": "informe_curva_saturacion_almen.html", "pn_loaded": "Registro del PN {pn} cargado.", "save_pn_error": "No se pudo guardar el PN: {message}", "pn_saved": "Registro del PN {pn} guardado/actualizado.", "pn_required_delete": "Introduzca la Pieza / PN que desea eliminar.", "delete_registry": "Eliminar registro", "delete_confirmation": "¿Eliminar definitivamente el registro del PN {pn}?", "delete_pn_error": "No se pudo eliminar el PN: {message}", "pn_removed": "Registro del PN {pn} eliminado.", "pn_not_found": "No se encontró el PN {pn}.", "report_generated": "Informe técnico generado correctamente.", "save_report_error": "No se pudo guardar el informe: {message}", "technical_title": "Tablas técnicas — medios de shot peening", "technical_heading": "Tablas técnicas de medios y normas", "technical_subtitle": "Referencia rápida para análisis de esferas, granulometría, tipos de medios y normas aplicables.", "tab_analysis": "Análisis de esferas", "tab_grain_size": "Granulometría", "tab_media_types": "Tipos de medios", "tab_standards": "Normas",
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
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C",
    "deviation_placeholder": "Ex.: 0,005", "point_2t_legend": "Ponto 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Faixa de intensidade de peening: {value} {unit}",
    "shot": "Esfera", "hardness": "Dureza", "nozzle": "Bico", "injector": "Injetor", "distance": "Distância", "angle": "Ângulo", "pressure": "Pressão",
    "registered_deviations": "Desvios de lâmina cadastrados", "standard_default": "SAE J443 e SAE J2597", "standard_other": "Outra norma (informar em observações)",
    "pn_required_save": "Informe a Peça / PN para salvar o cadastro.", "pn_required_remove": "Informe a Peça / PN a remover.",
    "invalid_arc_unit": "Unidade da altura do arco inválida.", "deviation_not_finite": "O desvio da lâmina deve ser um número finito.",
    "deviation_per_height": "Informe um desvio para cada altura do arco medida.", "negative_compensated": "O desvio informado torna alguma altura do arco compensada negativa.",
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
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C",
    "deviation_placeholder": "E.g.: 0.005", "point_2t_legend": "Point 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Peening intensity range: {value} {unit}",
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
    "almen_type_n": "N", "almen_type_a": "A", "almen_type_c": "C",
    "deviation_placeholder": "Ej.: 0,005", "point_2t_legend": "Punto 2T ({value:.2f} {unit})", "required_peening_intensity_legend": "Rango de intensidad de peening: {value} {unit}",
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
    "report_reprint_ready": "Relatório {number} aberto para reimpressão.",
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
    "report_reprint_ready": "Report {number} opened for reprint.",
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
    "report_reprint_ready": "Informe {number} abierto para reimpresión.",
    "report_generated_numbered": "Informe {number} generado y archivado correctamente.",
})

_TEXTS["PT"].update({
    "current_month_reports_hint": "Exibindo os relatórios do mês atual. Pesquise para localizar qualquer relatório anterior.",
    "report_year": "Ano", "report_month": "Mês", "delete_report": "Excluir",
    "delete_report_confirmation": "Excluir definitivamente o relatório {number}? Esta ação será sincronizada com os outros computadores.",
    "report_deleted": "Relatório {number} excluído.",
    "tooltip_delete_report": "Exclui este relatório após confirmação.",
})
_TEXTS["EN"].update({
    "current_month_reports_hint": "Showing reports from the current month. Search to find any earlier report.",
    "report_year": "Year", "report_month": "Month", "delete_report": "Delete",
    "delete_report_confirmation": "Permanently delete report {number}? This action will be synchronized with the other computers.",
    "report_deleted": "Report {number} deleted.",
    "tooltip_delete_report": "Deletes this report after confirmation.",
})
_TEXTS["ES"].update({
    "current_month_reports_hint": "Mostrando los informes del mes actual. Busque para localizar informes anteriores.",
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
    "tooltip_search_pn": "Busca cadastros pelo Router, PN ou SN informado.",
    "tooltip_save_update_pn": "Salva um novo cadastro de PN ou atualiza o cadastro atual.",
    "tooltip_delete_pn": "Exclui permanentemente o cadastro de PN informado.",
    "tooltip_generate_html": "Gera, numera e arquiva o relatório técnico em HTML.",
    "tooltip_reprint_report": "Abre a versão arquivada do relatório para reimpressão.",
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
    "tooltip_search_pn": "Searches records by the entered Router, PN or SN.",
    "tooltip_save_update_pn": "Saves a new PN record or updates the current record.",
    "tooltip_delete_pn": "Permanently deletes the entered PN record.",
    "tooltip_generate_html": "Generates, numbers and archives the HTML technical report.",
    "tooltip_reprint_report": "Opens the archived report version for reprinting.",
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
    "tooltip_search_pn": "Busca registros por el Router, PN o SN ingresado.",
    "tooltip_save_update_pn": "Guarda un nuevo registro de PN o actualiza el registro actual.",
    "tooltip_delete_pn": "Elimina permanentemente el registro de PN ingresado.",
    "tooltip_generate_html": "Genera, numera y archiva el informe técnico en HTML.",
    "tooltip_reprint_report": "Abre la versión archivada del informe para reimprimir.",
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
    "tooltip_developer_info": "Mostra as informacoes do desenvolvedor do sistema.",
    "tooltip_license_sync": "Mostra a licenca do sistema e a chave de sincronizacao em nuvem.",
    "tooltip_about_system": "Mostra a versao e as informacoes gerais do sistema.",
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
