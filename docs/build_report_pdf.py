"""Build the Spanish technical report PDF for the Food AI recommender."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "informe_tecnico.pdf"
EVALUATION = ROOT / "backend" / "artifacts" / "evaluation.json"
WEIGHTS = ROOT / "backend" / "artifacts" / "weight_search.json"

GREEN = colors.HexColor("#087f5b")
DARK = colors.HexColor("#173129")
MUTED = colors.HexColor("#5a6b65")
CREAM = colors.HexColor("#f7f4ee")
PALE_GREEN = colors.HexColor("#e5f4ee")
PALE_ORANGE = colors.HexColor("#fff2df")
ORANGE = colors.HexColor("#b76516")
LINE = colors.HexColor("#d8e3dd")


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def fmt(value: float) -> str:
    return f"{value:.4f}"


def section_title(number: str, title: str, styles: dict[str, ParagraphStyle]) -> list:
    return [
        Spacer(1, 5 * mm),
        Paragraph(f"{number}. {title}", styles["report_h2"]),
        HRFlowable(width="100%", thickness=0.8, color=LINE, spaceBefore=1, spaceAfter=4),
    ]


def table(data, widths, styles, header=True, font_size=8.5):
    converted = []
    for row in data:
        converted.append([cell if isinstance(cell, Paragraph) else p(str(cell), styles["table"]) for cell in row])
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
        for col in range(len(data[0])):
            converted[0][col] = Paragraph(str(data[0][col]), styles["table_header"])
    t.setStyle(TableStyle(commands))
    return t


def bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"<font color='{GREEN.hexval()}'>&bull;</font> {text}", styles["body"])


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "Food AI Recommender | Informe técnico")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def build() -> None:
    evaluation = json.loads(EVALUATION.read_text(encoding="utf-8"))
    weights = json.loads(WEIGHTS.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="cover_kicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10,
        leading=13, textColor=GREEN, tracking=1.1, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="cover_title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=29,
        leading=32, textColor=DARK, alignment=TA_LEFT, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="cover_subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=13,
        leading=19, textColor=MUTED, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="report_h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=16,
        leading=20, textColor=DARK, spaceBefore=8, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="report_h3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11,
        leading=14, textColor=GREEN, spaceBefore=6, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5,
        leading=14, textColor=DARK, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="small", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.4,
        leading=11, textColor=MUTED, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="table", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.2,
        leading=10.5, textColor=DARK,
    ))
    styles.add(ParagraphStyle(
        name="table_header", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.2,
        leading=10.5, textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10,
        leading=14, textColor=DARK, backColor=PALE_GREEN, borderColor=GREEN,
        borderWidth=0.7, borderPadding=9, spaceBefore=3, spaceAfter=9,
    ))
    styles.add(ParagraphStyle(
        name="warning", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2,
        leading=13, textColor=colors.HexColor("#6b3b0d"), backColor=PALE_ORANGE,
        borderColor=ORANGE, borderWidth=0.7, borderPadding=9, spaceBefore=3, spaceAfter=9,
    ))
    styles.add(ParagraphStyle(
        name="mono", parent=styles["BodyText"], fontName="Courier", fontSize=8.2,
        leading=11, textColor=DARK, backColor=CREAM, borderColor=LINE, borderWidth=0.5,
        borderPadding=7, spaceBefore=3, spaceAfter=7,
    ))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=20 * mm, title="Informe técnico - Food AI Recommender",
        author="Proyecto de Maestría",
    )
    story = []

    # Cover
    story += [Spacer(1, 22 * mm), Paragraph("PROYECTO FINAL DE MACHINE LEARNING", styles["cover_kicker"])]
    story += [Paragraph("Food AI Recommender", styles["cover_title"])]
    story += [Paragraph("Recomendación semántica de platos según preferencias, restricciones y lenguaje natural", styles["cover_subtitle"])]
    story += [Spacer(1, 8 * mm)]
    story += [Table([[p("80 platos", styles["report_h3"]), p("100 consultas anotadas", styles["report_h3"]), p("Precision@3", styles["report_h3"])]],
                    colWidths=[53 * mm, 62 * mm, 53 * mm], style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), PALE_GREEN), ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
                        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]))]
    story += [Spacer(1, 18 * mm), Paragraph("Entrega funcional con dataset reproducible, modelo de embeddings, línea base, API FastAPI, frontend web, pruebas y Docker.", styles["body"])]
    story += [Spacer(1, 30 * mm), Paragraph("Documento preparado para la presentación individual", styles["small"]), PageBreak()]

    story += section_title("1", "Problema y objetivo", styles)
    story += [p("Los menús digitales tradicionales obligan al cliente a navegar por categorías, leer descripciones y aplicar filtros manuales. Esta experiencia se vuelve lenta cuando el cliente tiene restricciones dietéticas, alergias, preferencias de sabor o un presupuesto concreto.", styles["body"])]
    story += [p("El objetivo es implementar un sistema que reciba una solicitud en lenguaje natural, por texto o voz, y devuelva los tres platos disponibles más relevantes respetando las restricciones registradas del restaurante.", styles["body"])]
    story += [p("Pregunta experimental: ¿la recuperación semántica de platos mejora la precisión de las primeras recomendaciones frente a una búsqueda tradicional ordenada por popularidad?", styles["callout"])]

    story += section_title("2", "Alcance funcional y arquitectura", styles)
    story += [p("El sistema demuestra la funcionalidad principal solicitada por la asignatura, sin intentar construir toda la plataforma POS. El foco evaluable es la comprensión de la consulta y la recuperación segura de platos.", styles["body"])]
    architecture = [
        ["Entrada del cliente", "Backend FastAPI", "Resultado visible"],
        ["Texto o voz en frontend", "Parser + filtro seguro + embeddings + ranking híbrido", "Top-3, explicación, aviso de seguridad"],
        ["Canales: web, kiosko, mesero", "Catálogo CSV + índice vectorial", "Respuesta JSON y simulación de carrito"],
    ]
    story += [table(architecture, [55 * mm, 70 * mm, 55 * mm], styles)]
    story += [Spacer(1, 3 * mm), p("Las restricciones de disponibilidad y alérgenos se resuelven con reglas deterministas antes del ranking. La IA interpreta el lenguaje natural y calcula la relevancia semántica; no decide por sí sola si un plato es médicamente seguro.", styles["warning"])]

    story += section_title("3", "Dataset y preparación", styles)
    story += [p("El dataset es sintético y reproducible porque el restaurante todavía no dispone de un historial público de pedidos. El generador mantiene la semilla 20261010 y produce un menú suficientemente amplio para probar consultas naturales variadas.", styles["body"])]
    dataset = [
        ["Elemento", "Descripción"],
        ["Menú", "80 platos con nombre, descripción, ingredientes, categoría, precio, dietas, alérgenos, picante, disponibilidad, tiempo, calorías, proteína y popularidad."],
        ["Consultas", "100 solicitudes en español con variaciones coloquiales, restricciones, rangos de precio y casos sin coincidencia segura."],
        ["Particiones", "20 de ajuste de pesos, 20 de validación y 60 de prueba. De estas últimas, 55 se puntúan y 5 son pruebas operativas de seguridad."],
        ["Anotación", "Cada consulta contiene identificadores de platos relevantes y el indicador scored para separar ranking de operación segura."],
        ["Reproducibilidad", "backend/scripts/generate_dataset.py con semilla fija 20261010."],
    ]
    story += [table(dataset, [33 * mm, 147 * mm], styles)]
    story += [p("La preparación normaliza acentos y expresiones frecuentes, extrae restricciones estructuradas y construye un texto enriquecido por plato para el encoder multilingüe.", styles["body"])]

    story += section_title("4", "Modelo y línea base", styles)
    story += [p("El modelo reutilizado es sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 mediante FastEmbed y ONNX Runtime. No se realiza fine-tuning: cada plato y la consulta se transforman en embeddings y se comparan con similitud coseno.", styles["body"])]
    model_steps = [
        ["1", "Interpretar la consulta en español y extraer dietas, alérgenos, proteína, picante, categoría y precio."],
        ["2", "Eliminar del catálogo los platos no disponibles o incompatibles con restricciones de seguridad."],
        ["3", "Calcular similitud semántica entre la consulta y los candidatos restantes."],
        ["4", "Reordenar con 55% semántica, 25% coincidencia estructurada y 20% popularidad."],
        ["5", "Entregar las tres primeras opciones con explicación basada en los datos reales del catálogo."],
    ]
    story += [table([["Paso", "Flujo de inferencia"]] + model_steps, [15 * mm, 165 * mm], styles)]
    story += [Spacer(1, 3 * mm), p("La línea base usa exactamente los mismos filtros de disponibilidad y seguridad y ordena los candidatos por popularidad. La comparación es justa: ambos sistemas reciben el mismo conjunto elegible.", styles["body"])]

    story += section_title("5", "Métrica y validación", styles)
    story += [p("La métrica primaria es Precision@3: la cantidad de platos relevantes que aparecen dentro de las tres primeras recomendaciones dividida entre 3. Es adecuada porque la interfaz muestra tres opciones y el objetivo operativo es recuperar candidatos útiles en esa primera pantalla.", styles["body"])]
    metrics = [
        ["Split", "Consultas", "Sistema", "Precision@3"],
        ["Validación", "20", "Pesos seleccionados", fmt(weights["selected_precision_at_3"])],
        ["Prueba", str(evaluation["query_count"]), "Línea base: filtros + popularidad", fmt(evaluation["baseline_precision_at_3"])],
        ["Prueba", str(evaluation["query_count"]), "Recomendador híbrido", fmt(evaluation["model_precision_at_3"])],
    ]
    story += [table(metrics, [30 * mm, 26 * mm, 83 * mm, 41 * mm], styles)]
    story += [Spacer(1, 3 * mm), p("Los pesos 0.55 / 0.25 / 0.20 se eligieron únicamente con el split de validación. La prueba final no se utilizó para ajustar parámetros. En este dataset sintético la línea base supera al modelo; se reporta de forma explícita y se analiza como una limitación, no como un resultado oculto.", styles["warning"])]

    story += section_title("6", "Resultados y análisis de errores", styles)
    errors = [
        ["Tipo", "Consulta", "Resultado observado", "Lectura técnica"],
        ["Acierto del modelo", "Busco fideos con verduras", "Recupera noodles con tofu, pasta vegetal y pasta con garbanzos.", "La semántica encuentra platos aunque no todos usen la palabra exacta pasta."],
        ["Base superior", "Sin gluten y sin soya", "La línea base prioriza platos populares compatibles.", "El embedding conserva candidatos parecidos, pero el orden por popularidad resulta mejor."],
        ["Seguridad", "Alergia a pescado y quiero salmón", "No devuelve recomendaciones.", "El filtro determinista bloquea la contradicción antes del ranking."],
    ]
    story += [table(errors, [28 * mm, 43 * mm, 54 * mm, 55 * mm], styles)]
    story += [p("El resultado sugiere que la siguiente iteración debe incorporar consultas reales anonimizadas, mejores anotaciones de relevancia y un reordenador supervisado entrenado sin contaminar la prueba final.", styles["body"])]

    story += section_title("7", "Backend, frontend y seguridad", styles)
    components = [
        ["Backend", "FastAPI con /api/health, /api/ready, /api/menu, /api/recommend, /api/feedback y /api/evaluation."],
        ["Estado del modelo", "La interfaz espera /api/ready y distingue loading, ready y error antes de permitir inferencia."],
        ["Frontend", "Entrada escrita, botón de voz, canal de demostración, restricciones detectadas, top-3, explicaciones y carrito simulado."],
        ["Validación", "Longitud, canal y top_k; mensajes de error; 12 pruebas automáticas y healthcheck de Docker."],
        ["Seguridad", "Aviso visible: confirmar ingredientes y contaminación cruzada con el personal; un alérgeno no registrado no garantiza seguridad."],
    ]
    story += [table([["Componente", "Implementación"]] + components, [35 * mm, 145 * mm], styles)]

    story += section_title("8", "Pruebas y ejecución", styles)
    story += [p("La suite automática cubre extracción de restricciones, filtros de seguridad, ausencia de candidatos, comparación con línea base, health check, recomendaciones válidas e inputs inválidos. La última ejecución produjo 12 pruebas exitosas.", styles["body"])]
    story += [p("Comandos reproducibles:", styles["report_h3"])]
    story += [p("docker compose up --build<br/>Abrir http://localhost:8080<br/>API Swagger: http://localhost:8000/docs<br/>Pruebas: cd backend && MODEL_BACKEND=tfidf pytest -q", styles["mono"])]
    story += [p("La primera ejecución necesita conexión a Internet para descargar el modelo preentrenado. Después, el volumen model_cache conserva la caché del encoder.", styles["body"])]

    story += section_title("9", "Limitaciones y trabajo futuro", styles)
    for item in [
        "El dataset es sintético y las consultas todavía no representan la diversidad de clientes reales.",
        "La línea base supera al modelo en la prueba actual; se debe mejorar la cobertura semántica y la anotación.",
        "El historial de pedidos y la personalización individual quedan como extensión posterior.",
        "El reconocimiento de voz depende de Web Speech API y del navegador.",
        "La calidad final depende de que el administrador mantenga ingredientes y alérgenos actualizados.",
    ]:
        story.append(bullet(item, styles))

    story += section_title("10", "Conclusión", styles)
    story += [p("La entrega demuestra un flujo completo de Machine Learning aplicado a un sistema de comidas: dataset reproducible, preparación, embeddings, filtros de seguridad, ranking híbrido, línea base, evaluación separada, API, frontend, pruebas y Docker.", styles["body"])]
    story += [p("La propuesta es útil para web, kiosko y aplicación de meseros porque permite formular pedidos como una persona los expresaría. Su evolución natural es conectar el catálogo real, registrar feedback explícito y entrenar un reordenador con datos autorizados, manteniendo la validación determinista de alergias.", styles["body"])]

    refs = [
        ["Artefacto", "Ubicación"],
        ["Generador y dataset", "backend/scripts/generate_dataset.py; backend/data/menu.csv; backend/data/evaluation_queries.jsonl"],
        ["Modelo e índice", "backend/app/recommendation.py; backend/scripts/build_index.py; backend/artifacts/"],
        ["Evaluación", "backend/scripts/tune_weights.py; backend/scripts/evaluate.py; backend/artifacts/evaluation.json"],
        ["Aplicación", "backend/app/main.py; frontend/index.html; frontend/app.js; docker-compose.yml"],
        ["Modelo preentrenado", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, usado mediante FastEmbed."],
    ]
    story += [KeepTogether(section_title("11", "Referencias y artefactos", styles) + [table(refs, [42 * mm, 138 * mm], styles)])]

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
