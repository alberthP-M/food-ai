"""Build the polished Spanish technical report PDF for Food AI Recommender.

The report keeps the technical content of the project but uses the visual
language of the reference deck: white canvas, cyan/purple accents, condensed
headings, geometric decorations and compact evidence cards.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
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
OUTPUT = ROOT / "output" / "pdf" / "informe_tecnico_final.pdf"
EVALUATION = ROOT / "backend" / "artifacts" / "evaluation.json"
WEIGHTS = ROOT / "backend" / "artifacts" / "weight_search.json"
SCREENSHOTS = ROOT / "docs" / "screenshots"
AUTHOR = "Alberto Orlando Paredes Mamani"
REPO_URL = "https://github.com/alberthP-M/food-ai"

NAVY = colors.HexColor("#202638")
CYAN = colors.HexColor("#16B8E5")
PURPLE = colors.HexColor("#7D55E8")
ORANGE = colors.HexColor("#F08A19")
MUTED = colors.HexColor("#5F6A80")
LINE = colors.HexColor("#D7DEE9")
PALE_CYAN = colors.HexColor("#E9F8FC")
PALE_PURPLE = colors.HexColor("#F0EBFF")
PALE_ORANGE = colors.HexColor("#FFF2E1")
PALE_GRAY = colors.HexColor("#F5F7FA")
WHITE = colors.white


def register_fonts() -> None:
    """Register local Arial variants for stable PDF rendering."""

    font_dir = Path("/System/Library/Fonts/Supplemental")
    fonts = {
        "Arial": font_dir / "Arial.ttf",
        "Arial-Bold": font_dir / "Arial Bold.ttf",
        "Arial-Italic": font_dir / "Arial Italic.ttf",
        "ArialNarrow": font_dir / "Arial Narrow.ttf",
        "ArialNarrow-Bold": font_dir / "Arial Narrow Bold.ttf",
    }
    for name, path in fonts.items():
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))


class ResultBars(Flowable):
    """Compact bar chart for the primary metric."""

    def __init__(self, values: list[tuple[str, float, str]], width: float = 166 * mm, height: float = 57 * mm):
        super().__init__()
        self.values = values
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return min(self.width, availWidth), self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PALE_GRAY)
        c.setStrokeColor(LINE)
        c.roundRect(0, 0, self.width, self.height, 5 * mm, fill=1, stroke=1)
        c.setFillColor(PURPLE)
        c.setFont("Arial-Bold", 9)
        c.drawString(7 * mm, self.height - 10 * mm, "PRECISION@3 · COMPARACIÓN")

        left = 16 * mm
        bottom = 13 * mm
        chart_w = self.width - 27 * mm
        chart_h = self.height - 28 * mm
        max_value = 0.7
        for tick in (0.0, 0.2, 0.4, 0.6, 0.7):
            y = bottom + chart_h * tick / max_value
            c.setStrokeColor(colors.HexColor("#DFE5EE"))
            c.setLineWidth(0.4)
            c.line(left, y, left + chart_w, y)
            c.setFillColor(MUTED)
            c.setFont("Arial", 6.5)
            c.drawRightString(left - 2 * mm, y - 2, f"{tick:.1f}")

        slot = chart_w / len(self.values)
        bar_w = 23 * mm
        for index, (label, value, color_hex) in enumerate(self.values):
            x = left + index * slot + (slot - bar_w) / 2
            h = chart_h * value / max_value
            c.setFillColor(colors.HexColor(color_hex))
            c.roundRect(x, bottom, bar_w, h, 1.2 * mm, fill=1, stroke=0)
            c.setFillColor(NAVY)
            c.setFont("Arial-Bold", 7.5)
            c.drawCentredString(x + bar_w / 2, bottom + h + 3, f"{value:.4f}")
            c.setFillColor(MUTED)
            c.setFont("Arial", 7)
            words = label.split(" ")
            if len(words) > 1:
                midpoint = max(1, len(words) // 2)
                c.drawCentredString(x + bar_w / 2, 7.5 * mm, " ".join(words[:midpoint]))
                c.drawCentredString(x + bar_w / 2, 4 * mm, " ".join(words[midpoint:]))
            else:
                c.drawCentredString(x + bar_w / 2, 5.5 * mm, label)
        c.restoreState()


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def fmt(value: float) -> str:
    return f"{value:.4f}"


def section_title(number: str, title: str, styles: dict[str, ParagraphStyle]) -> list:
    return [
        Spacer(1, 3 * mm),
        Paragraph(f"{number} / {title.upper()}", styles["section_kicker"]),
        Paragraph(title, styles["report_h2"]),
        HRFlowable(width="100%", thickness=0.8, color=LINE, spaceBefore=1, spaceAfter=4),
    ]


def table(data, widths, styles, header=True, compact=False):
    converted = []
    for row_index, row in enumerate(data):
        converted.append([
            cell if isinstance(cell, Paragraph) else p(str(cell), styles["table_header"] if header and row_index == 0 else styles["table"])
            for cell in row
        ])
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    pad = 3.5 if compact else 5
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ]
    t.setStyle(TableStyle(commands))
    return t


def card(text: str, style: ParagraphStyle, background=PALE_CYAN, border=CYAN):
    return Table([[Paragraph(text, style)]], colWidths=[180 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.75, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))


def evidence_pages(styles: dict[str, ParagraphStyle]) -> list:
    cases = [
        ("01 · Caso válido", "01-caso-valido.png", 1560 / 1440),
        ("02 · Caso difícil", "02-caso-dificil.png", 1578 / 1440),
        ("03 · Caso de seguridad", "03-caso-seguridad.png", 1270 / 1440),
        ("04 · Entrada inválida", "04-entrada-invalida.png", 1153 / 1440),
    ]
    story = []
    for index, (label, filename, aspect_ratio) in enumerate(cases):
        path = SCREENSHOTS / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing screenshot: {path}")
        story.append(Paragraph(label, styles["screenshot_caption"]))
        image = Image(str(path), width=170 * mm, height=170 * mm * aspect_ratio)
        image.hAlign = "CENTER"
        story.append(image)
        if index < len(cases) - 1:
            story.append(PageBreak())
    return story


def bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"<font color='{CYAN.hexval()}'>&bull;</font> {text}", styles["body"])


def draw_decorations(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    if doc.page == 1:
        # Cover: large accent shapes and a quiet lower ring.
        canvas.setFillColor(CYAN)
        canvas.saveState()
        canvas.translate(width - 55 * mm, height - 10 * mm)
        canvas.rotate(180)
        path = canvas.beginPath()
        path.moveTo(0, 0)
        path.lineTo(26 * mm, 0)
        path.lineTo(20 * mm, 15 * mm)
        path.lineTo(6 * mm, 15 * mm)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.restoreState()
        canvas.setFillColor(PURPLE)
        path = canvas.beginPath()
        path.moveTo(width / 2 - 15 * mm, 0)
        path.lineTo(width / 2 + 15 * mm, 0)
        path.lineTo(width / 2 + 10 * mm, 13 * mm)
        path.lineTo(width / 2 - 10 * mm, 13 * mm)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.setStrokeColor(PURPLE)
        canvas.setLineWidth(0.8)
        canvas.circle(width - 33 * mm, 42 * mm, 21 * mm, fill=0, stroke=1)
        canvas.setStrokeColor(CYAN)
        canvas.circle(width - 33 * mm, 42 * mm, 24 * mm, fill=0, stroke=1)
        for angle in range(0, 360, 60):
            import math
            x = width - 33 * mm + 25 * mm * math.cos(math.radians(angle))
            y = 42 * mm + 25 * mm * math.sin(math.radians(angle))
            canvas.setFillColor(CYAN)
            canvas.circle(x, y, 0.7 * mm, fill=1, stroke=0)
    else:
        # Repeated language of the reference deck: top trapezoid, outline polygon,
        # bottom accent and dotted ring.
        canvas.setFillColor(PURPLE if doc.page % 2 == 0 else CYAN)
        path = canvas.beginPath()
        path.moveTo(71 * mm, height)
        path.lineTo(103 * mm, height)
        path.lineTo(97 * mm, height - 14 * mm)
        path.lineTo(77 * mm, height - 14 * mm)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)

        canvas.setStrokeColor(CYAN if doc.page % 2 == 0 else PURPLE)
        canvas.setLineWidth(0.7)
        path = canvas.beginPath()
        path.moveTo(width - 42 * mm, height - 14 * mm)
        path.lineTo(width - 18 * mm, height - 14 * mm)
        path.lineTo(width - 18 * mm, height - 49 * mm)
        path.lineTo(width - 35 * mm, height - 66 * mm)
        path.lineTo(width - 42 * mm, height - 66 * mm)
        path.close()
        canvas.drawPath(path, fill=0, stroke=1)

        canvas.setFillColor(CYAN if doc.page % 2 == 0 else PURPLE)
        path = canvas.beginPath()
        path.moveTo(width / 2 - 15 * mm, 0)
        path.lineTo(width / 2 + 15 * mm, 0)
        path.lineTo(width / 2 + 10 * mm, 12 * mm)
        path.lineTo(width / 2 - 10 * mm, 12 * mm)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)

        canvas.setStrokeColor(PURPLE)
        canvas.setLineWidth(0.45)
        canvas.circle(19 * mm, 28 * mm, 22 * mm, fill=0, stroke=1)
        canvas.setStrokeColor(CYAN)
        canvas.circle(19 * mm, 28 * mm, 25 * mm, fill=0, stroke=1)
        for angle in range(0, 360, 60):
            import math
            x = 19 * mm + 26 * mm * math.cos(math.radians(angle))
            y = 28 * mm + 26 * mm * math.sin(math.radians(angle))
            canvas.setFillColor(CYAN)
            canvas.circle(x, y, 0.55 * mm, fill=1, stroke=0)

    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Arial", 7.5)
    canvas.drawString(18 * mm, 8.5 * mm, "FOOD AI · INFORME TÉCNICO")
    canvas.drawRightString(width - 18 * mm, 8.5 * mm, f"{doc.page:02d}")
    canvas.restoreState()


def build() -> None:
    register_fonts()
    evaluation = json.loads(EVALUATION.read_text(encoding="utf-8"))
    weights = json.loads(WEIGHTS.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="cover_kicker", parent=styles["Normal"], fontName="Arial-Bold", fontSize=9,
        leading=12, textColor=CYAN, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="cover_title", parent=styles["Title"], fontName="ArialNarrow-Bold", fontSize=31,
        leading=33, textColor=NAVY, alignment=TA_LEFT, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="cover_subtitle", parent=styles["Normal"], fontName="Arial", fontSize=12.5,
        leading=17, textColor=MUTED, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="cover_author", parent=styles["Normal"], fontName="Arial-Bold", fontSize=10.5,
        leading=14, textColor=NAVY, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="cover_repo", parent=styles["Normal"], fontName="Arial", fontSize=8.5,
        leading=11, textColor=PURPLE, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="section_kicker", parent=styles["Normal"], fontName="Arial-Bold", fontSize=8.2,
        leading=10, textColor=PURPLE, spaceBefore=4, spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="report_h2", parent=styles["Heading2"], fontName="ArialNarrow-Bold", fontSize=18,
        leading=21, textColor=NAVY, spaceBefore=1, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="report_h3", parent=styles["Heading3"], fontName="Arial-Bold", fontSize=10.5,
        leading=13, textColor=PURPLE, spaceBefore=5, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="body", parent=styles["BodyText"], fontName="Arial", fontSize=9.2,
        leading=13.3, textColor=NAVY, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="small", parent=styles["BodyText"], fontName="Arial", fontSize=8.2,
        leading=10.5, textColor=MUTED, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="table", parent=styles["BodyText"], fontName="Arial", fontSize=7.7,
        leading=9.5, textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="table_header", parent=styles["BodyText"], fontName="Arial-Bold", fontSize=7.7,
        leading=9.5, textColor=WHITE,
    ))
    styles.add(ParagraphStyle(
        name="callout", parent=styles["BodyText"], fontName="Arial-Bold", fontSize=9.5,
        leading=13, textColor=NAVY, spaceBefore=3, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="warning", parent=styles["BodyText"], fontName="Arial", fontSize=8.9,
        leading=12.5, textColor=colors.HexColor("#72410D"), spaceBefore=3, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="mono", parent=styles["BodyText"], fontName="Courier", fontSize=7.9,
        leading=10.3, textColor=NAVY, spaceBefore=3, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="metric", parent=styles["BodyText"], fontName="ArialNarrow-Bold", fontSize=16,
        leading=17, textColor=NAVY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="metric_label", parent=styles["BodyText"], fontName="Arial-Bold", fontSize=7.2,
        leading=9, textColor=PURPLE, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="screenshot_caption", parent=styles["BodyText"], fontName="Arial-Bold", fontSize=8.5,
        leading=10, textColor=PURPLE, alignment=TA_CENTER, spaceAfter=2,
    ))

    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm, title="Informe técnico - Food AI Recommender",
        author=AUTHOR,
    )
    story = []

    # Cover
    story += [Spacer(1, 22 * mm), Paragraph("PROYECTO FINAL · MACHINE LEARNING", styles["cover_kicker"])]
    story += [Paragraph("Food AI<br/>Recommender", styles["cover_title"])]
    story += [Paragraph("Recomendación semántica de platos según preferencias, restricciones y lenguaje natural.", styles["cover_subtitle"])]
    story += [Paragraph(AUTHOR, styles["cover_author"])]
    story += [Paragraph(f'Repositorio: <link href="{REPO_URL}">{REPO_URL}</link>', styles["cover_repo"])]
    story += [HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceBefore=3, spaceAfter=12)]
    story += [Paragraph("Una implementación funcional para web, kiosko y aplicación de meseros: recibe una frase, aplica seguridad determinista y entrega un top-3 explicable.", styles["body"])]
    story += [Spacer(1, 7 * mm)]
    metrics = Table([
        [p("80", styles["metric"]), p("100", styles["metric"]), p("3", styles["metric"])],
        [p("PLATOS", styles["metric_label"]), p("CONSULTAS ANOTADAS", styles["metric_label"]), p("RESULTADOS VISIBLES", styles["metric_label"])],
    ], colWidths=[56 * mm, 62 * mm, 56 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_CYAN),
        ("BOX", (0, 0), (-1, -1), 0.8, CYAN),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story += [metrics, Spacer(1, 13 * mm)]
    story += [card("<font color='#7D55E8'>RESULTADO PRINCIPAL</font><br/><font size='11'>La línea base obtiene 0.6121 en prueba y el modelo híbrido 0.4727. La comparación se presenta de forma honesta: el sistema funciona, pero el embedding todavía debe mejorar su ordenamiento en este dataset sintético.</font>", styles["callout"], PALE_PURPLE, PURPLE)]
    story += [Spacer(1, 16 * mm), Paragraph("Informe preparado para la presentación individual · 2026", styles["small"]), PageBreak()]

    story += section_title("01", "Problema y objetivo", styles)
    story += [p("Los menús digitales tradicionales obligan al cliente a navegar por categorías, leer descripciones y aplicar filtros manuales. La experiencia se vuelve lenta cuando la persona tiene restricciones dietéticas, alergias, preferencias de sabor o un presupuesto concreto.", styles["body"])]
    story += [p("El objetivo es implementar un sistema que reciba una solicitud en lenguaje natural, por texto o voz, y devuelva los tres platos disponibles más relevantes respetando las restricciones registradas del restaurante.", styles["body"])]
    story += [card("<font color='#16B8E5'>PREGUNTA EXPERIMENTAL</font><br/>¿La recuperación semántica de platos mejora la precisión de las primeras recomendaciones frente a una búsqueda tradicional ordenada por popularidad?", styles["callout"], PALE_CYAN, CYAN)]

    story += section_title("02", "Alcance funcional y arquitectura", styles)
    story += [p("El sistema demuestra la funcionalidad principal solicitada por la asignatura, sin intentar construir toda la plataforma POS. El foco evaluable es la comprensión de la consulta y la recuperación segura de platos.", styles["body"])]
    architecture = [
        ["ENTRADA DEL CLIENTE", "BACKEND FASTAPI", "RESULTADO VISIBLE"],
        ["Texto o voz en frontend", "Parser + filtro seguro + embeddings + ranking híbrido", "Top-3, explicación, aviso de seguridad"],
        ["Web · kiosko · meseros", "Catálogo CSV + índice vectorial", "Respuesta JSON y carrito simulado"],
    ]
    story += [table(architecture, [53 * mm, 74 * mm, 53 * mm], styles, compact=True)]
    story += [Spacer(1, 3 * mm), card("<font color='#F08A19'>SEGURIDAD PRIMERO</font><br/>Las restricciones de disponibilidad y alérgenos se resuelven con reglas deterministas antes del ranking. La IA interpreta el lenguaje natural y calcula relevancia; no decide por sí sola si un plato es médicamente seguro.", styles["warning"], PALE_ORANGE, ORANGE)]
    story += [PageBreak()]

    story += section_title("03", "Dataset y preparación", styles)
    story += [p("El dataset es sintético y reproducible porque el restaurante todavía no dispone de un historial público de pedidos. El generador mantiene la semilla 20261010 y produce un menú amplio para probar consultas naturales variadas.", styles["body"])]
    dataset = [
        ["ELEMENTO", "DESCRIPCIÓN"],
        ["Menú", "80 platos con nombre, descripción, ingredientes, categoría, precio, dietas, alérgenos, picante, disponibilidad, tiempo, calorías, proteína y popularidad."],
        ["Consultas", "100 solicitudes en español con variaciones coloquiales, restricciones, rangos de precio y casos sin coincidencia segura."],
        ["Particiones", "20 de ajuste de pesos, 20 de validación y 60 de prueba. De estas últimas, 55 se puntúan y 5 son pruebas operativas de seguridad."],
        ["Anotación", "Cada consulta contiene identificadores de platos relevantes y el indicador scored para separar ranking de operación segura."],
        ["Reproducibilidad", "backend/scripts/generate_dataset.py con semilla fija 20261010."],
    ]
    story += [table(dataset, [32 * mm, 148 * mm], styles, compact=True)]
    story += [Spacer(1, 3 * mm), p("La preparación normaliza acentos y expresiones frecuentes, extrae restricciones estructuradas y construye un texto enriquecido por plato para el encoder multilingüe.", styles["body"])]

    story += section_title("04", "Modelo y línea base", styles)
    story += [p("El modelo reutilizado es sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 mediante FastEmbed y ONNX Runtime. No se realiza fine-tuning: cada plato y la consulta se transforman en embeddings y se comparan con similitud coseno.", styles["body"])]
    model_steps = [
        ["PASO", "FLUJO DE INFERENCIA"],
        ["01", "Interpretar la consulta en español y extraer dietas, alérgenos, proteína, picante, categoría y precio."],
        ["02", "Eliminar del catálogo los platos no disponibles o incompatibles con restricciones de seguridad."],
        ["03", "Calcular similitud semántica entre la consulta y los candidatos restantes."],
        ["04", "Reordenar con 55% semántica, 25% coincidencia estructurada y 20% popularidad."],
        ["05", "Entregar las tres primeras opciones con explicación basada en los datos reales del catálogo."],
    ]
    story += [table(model_steps, [16 * mm, 164 * mm], styles, compact=True)]
    story += [Spacer(1, 3 * mm), p("La línea base usa exactamente los mismos filtros de disponibilidad y seguridad y ordena los candidatos por popularidad. La comparación es justa: ambos sistemas reciben el mismo conjunto elegible.", styles["body"])]
    story += [PageBreak()]

    story += section_title("05", "Métrica y validación", styles)
    story += [p("La métrica primaria es Precision@3: la cantidad de platos relevantes que aparecen dentro de las tres primeras recomendaciones dividida entre 3. Es adecuada porque la interfaz muestra tres opciones y el objetivo operativo es recuperar candidatos útiles en esa primera pantalla.", styles["body"])]
    metrics_table = [
        ["SPLIT", "CONSULTAS", "SISTEMA", "PRECISION@3"],
        ["Validación", "20", "Pesos seleccionados", fmt(weights["selected_precision_at_3"])],
        ["Prueba", str(evaluation["query_count"]), "Línea base: filtros + popularidad", fmt(evaluation["baseline_precision_at_3"])],
        ["Prueba", str(evaluation["query_count"]), "Recomendador híbrido", fmt(evaluation["model_precision_at_3"])],
    ]
    story += [table(metrics_table, [28 * mm, 27 * mm, 84 * mm, 41 * mm], styles, compact=True)]
    story += [Spacer(1, 4 * mm), ResultBars([
        ("Pesos validación", weights["selected_precision_at_3"], "#7D55E8"),
        ("Línea base", evaluation["baseline_precision_at_3"], "#16B8E5"),
        ("Modelo híbrido", evaluation["model_precision_at_3"], "#F08A19"),
    ])]
    story += [Spacer(1, 3 * mm), card("<font color='#F08A19'>LECTURA HONESTA</font><br/>Los pesos 0.55 / 0.25 / 0.20 se eligieron únicamente con validación. La prueba final no se utilizó para ajustar parámetros. En este dataset sintético la línea base supera al modelo; se reporta y se analiza como una limitación, no como un resultado oculto.", styles["warning"], PALE_ORANGE, ORANGE)]

    story += section_title("06", "Análisis de errores", styles)
    errors = [
        ["TIPO", "CONSULTA", "RESULTADO OBSERVADO", "LECTURA TÉCNICA"],
        ["Acierto del modelo", "Busco fideos con verduras", "Recupera noodles con tofu, pasta vegetal y pasta con garbanzos.", "La semántica encuentra platos aunque no todos usen la palabra exacta pasta."],
        ["Base superior", "Sin gluten y sin soya", "La línea base prioriza platos populares compatibles.", "El embedding conserva candidatos parecidos, pero el orden por popularidad resulta mejor."],
        ["Seguridad", "Alergia a pescado y quiero salmón", "No devuelve recomendaciones.", "El filtro determinista bloquea la contradicción antes del ranking."],
    ]
    story += [table(errors, [28 * mm, 41 * mm, 56 * mm, 55 * mm], styles, compact=True)]
    story += [PageBreak()]

    story += section_title("07", "Backend, frontend y seguridad", styles)
    components = [
        ["COMPONENTE", "IMPLEMENTACIÓN"],
        ["Backend", "FastAPI con /api/health, /api/ready, /api/menu, /api/recommend, /api/feedback y /api/evaluation."],
        ["Estado del modelo", "La interfaz espera /api/ready y distingue loading, ready y error antes de permitir inferencia."],
        ["Frontend", "Entrada escrita, botón de voz, canal de demostración, restricciones detectadas, top-3, explicaciones y carrito simulado."],
        ["Validación", "Longitud, canal y top_k; mensajes de error; 12 pruebas automáticas y healthcheck de Docker."],
        ["Seguridad", "Aviso visible: confirmar ingredientes y contaminación cruzada con el personal; un alérgeno no registrado no garantiza seguridad."],
    ]
    story += [table(components, [35 * mm, 145 * mm], styles, compact=True)]

    story += section_title("08", "Escenarios para la demostración", styles)
    demo = [
        ["CASO", "ENTRADA", "QUÉ SE DEMUESTRA"],
        ["Válido", "Vegetariano, sin lactosa y poco picante", "Extracción de restricciones + top-3 explicable."],
        ["Difícil", "Sin gluten con pollo y menor a Bs 50", "Combinación de dieta, ingrediente y presupuesto."],
        ["Seguridad", "Alergia a pescado y quiero salmón", "El filtro rechaza la contradicción antes de la IA."],
        ["Inválido", "Texto vacío o de un carácter", "Validación del backend y mensaje claro al usuario."],
        ["Voz", "Dictado desde el navegador", "Speech API transcribe y reutiliza el mismo endpoint."],
    ]
    story += [table(demo, [27 * mm, 77 * mm, 76 * mm], styles, compact=True)]
    story += [Spacer(1, 3 * mm), card("<font color='#16B8E5'>DÓNDE ACTÚA LA IA</font><br/>La IA actúa en la interpretación semántica de la frase y en el cálculo de similitud entre la consulta y los platos. Los filtros de alergias, disponibilidad y validación son reglas deterministas para mantener trazabilidad y seguridad.", styles["callout"], PALE_CYAN, CYAN)]

    story += section_title("09", "Evidencia visual del flujo", styles)
    story += [p("Las capturas se obtuvieron ejecutando el frontend conectado al backend real con Docker. Muestran el estado listo del modelo, la interpretación de restricciones, el resultado útil, el bloqueo de una contradicción de alergia y el manejo de una entrada inválida.", styles["body"])]
    story += evidence_pages(styles)
    story += [PageBreak()]

    story += section_title("10", "Pruebas y ejecución", styles)
    story += [p("La suite automática cubre extracción de restricciones, filtros de seguridad, ausencia de candidatos, comparación con línea base, health check, recomendaciones válidas e inputs inválidos. La última ejecución produjo 12 pruebas exitosas.", styles["body"])]
    story += [p("Comandos reproducibles:", styles["report_h3"])]
    story += [p("docker compose up --build<br/>Abrir http://localhost:8080<br/>API Swagger: http://localhost:8000/docs<br/>Pruebas: cd backend && MODEL_BACKEND=tfidf pytest -q", styles["mono"])]
    story += [p("La primera ejecución necesita conexión a Internet para descargar el modelo preentrenado. Después, el volumen model_cache conserva la caché del encoder.", styles["body"])]
    story += [PageBreak()]

    story += section_title("11", "Limitaciones y trabajo futuro", styles)
    for item in [
        "El dataset es sintético y las consultas todavía no representan toda la diversidad de clientes reales.",
        "La línea base supera al modelo en la prueba actual; se debe mejorar la cobertura semántica y la anotación.",
        "El historial de pedidos y la personalización individual quedan como extensión posterior.",
        "El reconocimiento de voz depende de Web Speech API y del navegador.",
        "La calidad final depende de que el administrador mantenga ingredientes y alérgenos actualizados.",
    ]:
        story.append(bullet(item, styles))

    story += section_title("12", "Conclusión", styles)
    story += [p("La entrega demuestra un flujo completo de Machine Learning aplicado a un sistema de comidas: dataset reproducible, preparación, embeddings, filtros de seguridad, ranking híbrido, línea base, evaluación separada, API, frontend, pruebas y Docker.", styles["body"])]
    story += [card("<font color='#7D55E8'>MENSAJE FINAL</font><br/>El producto no intenta adivinar una dieta médica: convierte una intención cotidiana en una búsqueda de menú segura, explicable y lista para integrarse en los canales del restaurante.", styles["callout"], PALE_PURPLE, PURPLE)]

    refs = [
        ["ARTEFACTO", "UBICACIÓN"],
        ["Generador y dataset", "backend/scripts/generate_dataset.py; backend/data/menu.csv; backend/data/evaluation_queries.jsonl"],
        ["Modelo e índice", "backend/app/recommendation.py; backend/scripts/build_index.py; backend/artifacts/"],
        ["Evaluación", "backend/scripts/tune_weights.py; backend/scripts/evaluate.py; backend/artifacts/evaluation.json"],
        ["Aplicación", "backend/app/main.py; frontend/index.html; frontend/app.js; docker-compose.yml"],
        ["Modelo preentrenado", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 mediante FastEmbed."],
    ]
    story += [KeepTogether(section_title("13", "Referencias y artefactos", styles) + [table(refs, [43 * mm, 137 * mm], styles, compact=True)])]

    doc.build(story, onFirstPage=draw_decorations, onLaterPages=draw_decorations)
    print(OUTPUT)


if __name__ == "__main__":
    build()
