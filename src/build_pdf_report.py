from __future__ import annotations

import argparse
import base64
import html
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIG_GRAPH = ROOT / "figures" / "context_graph.svg"
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"

PAGE_W = 1240
PAGE_H = 1754
MARGIN_X = 92
MARGIN_Y = 96

BG = "#f5efe6"
PAPER = "#fffdf9"
TEXT = "#211d1b"
MUTED = "#6e6258"
ACCENT = "#8b5e3c"
ACCENT_2 = "#d9c0a7"
LINE = "#e5d8ca"


@dataclass
class Cursor:
    x: int
    y: int


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def chars_for_width(width: int, font_size: int, factor: float = 0.56) -> int:
    return max(18, int(width / (font_size * factor)))


def wrap(text: str, width: int, font_size: int) -> list[str]:
    chunks = textwrap.wrap(
        text,
        width=chars_for_width(width, font_size),
        break_long_words=False,
        break_on_hyphens=False,
    )
    return chunks or [text]


def add_text_block(parts: list[str], cursor: Cursor, text: str, *, width: int, font_size: int, color: str = TEXT, line_gap: int = 8, font_weight: str = "400") -> None:
    lines = wrap(text, width, font_size)
    for line in lines:
        parts.append(
            f'<text x="{cursor.x}" y="{cursor.y}" font-size="{font_size}" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="{font_weight}" fill="{color}">{esc(line)}</text>'
        )
        cursor.y += font_size + line_gap


def add_label(parts: list[str], cursor: Cursor, text: str) -> None:
    parts.append(
        f'<text x="{cursor.x}" y="{cursor.y}" font-size="18" letter-spacing="2" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" fill="{ACCENT}">{esc(text.upper())}</text>'
    )
    cursor.y += 36


def add_heading(parts: list[str], cursor: Cursor, text: str, size: int = 42) -> None:
    parts.append(
        f'<text x="{cursor.x}" y="{cursor.y}" font-size="{size}" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" fill="{TEXT}">{esc(text)}</text>'
    )
    cursor.y += size + 22


def add_rule(parts: list[str], y: int) -> None:
    parts.append(f'<line x1="{MARGIN_X}" y1="{y}" x2="{PAGE_W - MARGIN_X}" y2="{y}" stroke="{LINE}" stroke-width="2"/>')


def add_bullets(parts: list[str], cursor: Cursor, items: list[str], *, width: int, font_size: int = 25) -> None:
    for item in items:
        bullet_x = cursor.x
        text_x = cursor.x + 26
        text_width = width - 26
        lines = wrap(item, text_width, font_size)
        parts.append(f'<circle cx="{bullet_x + 8}" cy="{cursor.y - 8}" r="4" fill="{ACCENT}"/>')
        first = True
        for line in lines:
            parts.append(
                f'<text x="{text_x}" y="{cursor.y}" font-size="{font_size}" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" fill="{TEXT}">{esc(line)}</text>'
            )
            cursor.y += font_size + 8
            if first:
                first = False
        cursor.y += 6


def page_shell(page_number: int, total_pages: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}" height="{PAGE_H}" viewBox="0 0 {PAGE_W} {PAGE_H}">',
        f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{BG}"/>',
        f'<rect x="34" y="34" width="{PAGE_W - 68}" height="{PAGE_H - 68}" rx="26" fill="{PAPER}" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="{PAGE_W - MARGIN_X}" y="{PAGE_H - 54}" text-anchor="end" font-size="20" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" fill="{MUTED}">Página {page_number} de {total_pages}</text>',
    ]


def finish(parts: list[str]) -> str:
    return "\n".join(parts + ["</svg>"])


def graph_png_data_uri() -> str:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    graph_png = TMP_DIR / "graph_pretty.png"
    subprocess.run(
        ["rsvg-convert", "-w", "1020", "-h", "1020", "-o", str(graph_png), str(FIG_GRAPH)],
        check=True,
    )
    payload = base64.b64encode(graph_png.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def build_cover(total_pages: int) -> str:
    parts = page_shell(1, total_pages)
    parts.append(f'<rect x="34" y="34" width="{PAGE_W - 68}" height="420" rx="26" fill="{ACCENT}"/>')
    parts.append(f'<rect x="{MARGIN_X}" y="520" width="{PAGE_W - (MARGIN_X * 2)}" height="190" rx="18" fill="{ACCENT_2}" opacity="0.45"/>')
    c = Cursor(MARGIN_X, 140)
    parts.append(f'<text x="{c.x}" y="{c.y}" font-size="22" letter-spacing="3" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" fill="{PAPER}">PROYECTO 8</text>')
    c.y += 64
    parts.append(f'<text x="{c.x}" y="{c.y}" font-size="58" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" fill="{PAPER}">Del sistema experto</text>')
    c.y += 70
    parts.append(f'<text x="{c.x}" y="{c.y}" font-size="58" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" font-weight="700" fill="{PAPER}">al context graph</text>')
    c.y += 86
    add_text_block(
        parts,
        c,
        "Sistema experto moderno sobre la saga Final Fantasy usando 3DJuegos, context graph y OpenRouter.",
        width=840,
        font_size=31,
        color=PAPER,
        line_gap=10,
    )
    c = Cursor(MARGIN_X, 580)
    add_label(parts, c, "Resumen")
    add_text_block(
        parts,
        c,
        "El proyecto construye un context graph con procedencia, fecha y confianza para responder preguntas sobre Final Fantasy. Combina scraping, extracción de tripletas por reglas y por LLM, construcción del grafo y consulta final con OpenRouter sobre evidencia recuperada.",
        width=1040,
        font_size=28,
        line_gap=10,
    )
    c.y += 18
    add_label(parts, c, "Contenido")
    add_bullets(
        parts,
        c,
        [
            "Objetivos del sistema experto y justificación del dominio",
            "Arquitectura del pipeline y scripts utilizados",
            "Construcción del context graph y comparación con baseline",
            "Preguntas, respuestas citadas y ejemplo multi-hop",
            "Conclusión sobre context graph frente a RAG vectorial",
        ],
        width=1040,
        font_size=28,
    )
    parts.append(f'<text x="{MARGIN_X}" y="{PAGE_H - 180}" font-size="24" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" fill="{MUTED}">Autor: SuliAragon</text>')
    parts.append(f'<text x="{MARGIN_X}" y="{PAGE_H - 140}" font-size="24" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" fill="{MUTED}">Módulo: Modelos de Inteligencia Artificial</text>')
    return finish(parts)


def build_page_2(total_pages: int) -> str:
    parts = page_shell(2, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Dominio y objetivos")
    add_heading(parts, c, "Final Fantasy como caso de estudio", 46)
    add_text_block(parts, c, "Este proyecto toma la saga Final Fantasy como dominio porque es un entorno claramente relacional: hay entregas principales, remakes, plataformas, fechas de lanzamiento, géneros y desarrolladores. Esa estructura permite formular preguntas que no dependen solo de recuperar texto, sino de conectar hechos entre sí.", width=1040, font_size=28, line_gap=10)
    c.y += 18
    add_text_block(parts, c, "La fuente principal ha sido 3DJuegos, usando tanto el universo general de Final Fantasy como fichas concretas de juegos clave como Final Fantasy VII Remake, Final Fantasy VII Rebirth y Final Fantasy XVI.", width=1040, font_size=28, line_gap=10)
    c.y += 24
    add_label(parts, c, "Objetivo del sistema")
    add_bullets(parts, c, [
        "Identificar juegos, plataformas, géneros, desarrolladores y fechas.",
        "Representar relaciones como is_remake_of, developed_by, published_by y available_on.",
        "Responder preguntas simples y multi-hop con citas de fuente y fecha.",
        "Combinar un grafo con un LLM como motor de inferencia final.",
    ], width=1040, font_size=28)
    c.y += 10
    add_label(parts, c, "Arquitectura")
    add_bullets(parts, c, [
        "scraping.py descarga páginas en Markdown a través de r.jina.ai.",
        "obtain_triplets.py extrae tripletas mediante reglas sobre el texto.",
        "obtain_triplets_llm.py extrae tripletas con OpenRouter en fichas clave.",
        "merge_triplets.py combina reglas y LLM.",
        "context_graph.py construye el grafo y su visualización parcial.",
        "ask_llm.py recupera evidencia del grafo y usa OpenRouter para responder.",
    ], width=1040, font_size=27)
    return finish(parts)


def build_page_3(total_pages: int) -> str:
    parts = page_shell(3, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Context graph")
    add_heading(parts, c, "Modelado, metadatos y resultados", 46)
    add_text_block(parts, c, "El sistema genera dos versiones del conocimiento: un baseline sin metadatos y un context graph enriquecido con procedencia, fecha de extracción, validez temporal y confianza. Eso permite justificar cada respuesta y filtrar hechos según contexto temporal.", width=1040, font_size=28, line_gap=10)
    c.y += 28
    add_bullets(parts, c, [
        "Aristas baseline: 626",
        "Aristas del context graph híbrido: 653",
        "Nodos del grafo final: 450",
        "Tripletas añadidas mediante LLM: 39",
        "Aristas con fecha de vigencia: 152",
        "Aristas con fuente trazable: 653",
    ], width=1040, font_size=29)
    c.y += 24
    add_text_block(parts, c, "Las tripletas generadas por LLM han sido especialmente útiles para relaciones semánticas como is_remake_of, developed_by, published_by y has_type, mientras que la extracción por reglas ha servido como baseline reproducible y como red de seguridad cuando la API no aporta cobertura adicional.", width=1040, font_size=28, line_gap=10)
    c.y += 24
    add_label(parts, c, "Sistema experto clásico frente a context graph")
    add_bullets(parts, c, [
        "Base de conocimiento: el grafo de tripletas.",
        "Motor de inferencia: recuperación de evidencia más respuesta del LLM.",
        "Interfaz: scripts de consulta ask.py y ask_llm.py.",
        "Capa de contexto: source, fecha_extraccion, valido_desde, valido_hasta y confianza.",
    ], width=1040, font_size=27)
    return finish(parts)


def build_graph_page(total_pages: int, data_uri: str) -> str:
    parts = page_shell(4, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Visualización")
    add_heading(parts, c, "Context graph parcial de Final Fantasy", 46)
    add_text_block(parts, c, "La figura muestra una parte representativa del grafo. Se han limitado los nodos para mantener la legibilidad y enseñar relaciones visibles entre juegos, géneros y universos del dominio.", width=1040, font_size=27, line_gap=10)
    card_x = MARGIN_X
    card_y = 270
    card_w = PAGE_W - (MARGIN_X * 2)
    card_h = 1180
    parts.append(f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="22" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>')
    parts.append(f'<image href="{data_uri}" x="{card_x + 30}" y="{card_y + 40}" width="{card_w - 60}" height="{card_h - 120}" preserveAspectRatio="xMidYMid meet"/>')
    parts.append(f'<text x="{card_x + 30}" y="{card_y + card_h - 34}" font-size="22" font-family="Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif" fill="{MUTED}">Figura 1. Visualización parcial del context graph construido a partir de Final Fantasy y 3DJuegos.</text>')
    return finish(parts)


def build_page_5(total_pages: int) -> str:
    parts = page_shell(5, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Preguntas y respuestas")
    add_heading(parts, c, "Consulta temporal sobre PS5", 46)
    add_text_block(parts, c, "Pregunta: ¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?", width=1040, font_size=31, line_gap=10)
    c.y += 18
    add_bullets(parts, c, [
        "Final Fantasy XVI, con salida en PS5 el 22 de junio de 2023. Fuente: https://www.3djuegos.com/universo/0f0f0f0/11/final-fantasy/",
        "Final Fantasy VII: Rebirth, con fecha de lanzamiento el 29 de febrero de 2024 y evidencia de disponibilidad en PS5. Fuente: https://www.3djuegos.com/juegos/final-fantasy-vii-rebirth/",
    ], width=1040, font_size=27)
    c.y += 22
    add_text_block(parts, c, "Esta pregunta combina la relación available_on con released_on y aplica un filtro temporal posterior a 2020. Es un buen ejemplo de por qué el contexto estructurado mejora frente a recuperar solo texto parecido.", width=1040, font_size=28, line_gap=10)
    c.y += 28
    add_heading(parts, c, "Consulta sobre remakes", 40)
    add_text_block(parts, c, "Pregunta: ¿Qué entregas de Final Fantasy aparecen como remakes?", width=1040, font_size=30, line_gap=10)
    c.y += 18
    add_bullets(parts, c, [
        "Final Fantasy VII Remake aparece como remake de Final Fantasy VII. Fuente: http://www.3djuegos.com/juegos/final-fantasy-vii-remake/",
    ], width=1040, font_size=27)
    return finish(parts)


def build_page_6(total_pages: int) -> str:
    parts = page_shell(6, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Pregunta multi-hop")
    add_heading(parts, c, "Remake + desarrollador + juego original", 46)
    add_text_block(parts, c, "Pregunta: ¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?", width=1040, font_size=30, line_gap=10)
    c.y += 22
    add_text_block(parts, c, "Ruta de razonamiento en el grafo:", width=1040, font_size=28, line_gap=10, color=MUTED, font_weight="700")
    c.y += 8
    add_bullets(parts, c, [
        "Final Fantasy VII Remake -> developed_by -> Square Enix",
        "Final Fantasy VII Remake -> is_remake_of -> Final Fantasy VII",
    ], width=1040, font_size=28)
    c.y += 24
    add_text_block(parts, c, "Respuesta del sistema:", width=1040, font_size=28, line_gap=10, color=MUTED, font_weight="700")
    c.y += 8
    add_bullets(parts, c, [
        "El remake identificado es Final Fantasy VII Remake.",
        "Proviene del juego original Final Fantasy VII.",
        "Está desarrollado por Square Enix.",
        "Fuente principal: http://www.3djuegos.com/juegos/final-fantasy-vii-remake/",
    ], width=1040, font_size=28)
    c.y += 20
    add_text_block(parts, c, "Esta es la pregunta que mejor representa el objetivo del proyecto, porque no se resuelve con un único hecho sino conectando varias relaciones del context graph y dejando que el LLM redacte la respuesta final usando solo esa evidencia.", width=1040, font_size=28, line_gap=10)
    return finish(parts)


def build_page_7(total_pages: int) -> str:
    parts = page_shell(7, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Comparación")
    add_heading(parts, c, "Baseline frente a context graph", 46)
    add_bullets(parts, c, [
        "El baseline conserva relaciones sujeto-predicado-objeto, pero no justifica el origen exacto de cada hecho.",
        "El context graph añade procedencia, fecha y confianza por arista.",
        "Gracias a esos metadatos se pueden responder preguntas temporales con citas verificables.",
        "La versión final permite además recuperar evidencia y usar un LLM como motor de inferencia sin dejarle inventar contexto.",
    ], width=1040, font_size=28)
    c.y += 26
    add_label(parts, c, "Estrategia de control")
    add_bullets(parts, c, [
        "Usar Markdown de r.jina.ai para simplificar el scraping.",
        "Mantener una extracción por reglas como baseline reproducible.",
        "Complementar con OpenRouter solo en fichas clave.",
        "Obligar a que ask_llm.py responda únicamente con evidencia recuperada del grafo.",
        "Citar siempre fuente y fecha en la respuesta final.",
    ], width=1040, font_size=28)
    return finish(parts)


def build_page_8(total_pages: int) -> str:
    parts = page_shell(8, total_pages)
    c = Cursor(MARGIN_X, MARGIN_Y)
    add_label(parts, c, "Reflexión final")
    add_heading(parts, c, "Context graph o RAG vectorial", 46)
    add_text_block(parts, c, "Un RAG vectorial bastaría cuando solo necesitamos recuperar fragmentos relevantes de texto y las relaciones entre entidades no son el núcleo del problema. En cambio, un context graph merece la pena cuando importan las conexiones entre hechos, la procedencia, la vigencia temporal y las preguntas multi-hop.", width=1040, font_size=29, line_gap=10)
    c.y += 26
    add_bullets(parts, c, [
        "RAG vectorial: útil para recuperar texto sin demasiada estructura relacional.",
        "Context graph: útil cuando la relación entre entidades cambia la respuesta.",
        "LLM acotado por evidencia: útil para redactar respuestas claras sin renunciar a la trazabilidad.",
    ], width=1040, font_size=28)
    c.y += 26
    add_text_block(parts, c, "En este proyecto, Final Fantasy ha servido como dominio manejable y muy relacional para demostrar la idea central del enunciado: el conocimiento experto no se deja dentro del modelo, sino alrededor del modelo, en forma de contexto verificable.", width=1040, font_size=29, line_gap=10)
    c.y += 34
    add_heading(parts, c, "Conclusión", 40)
    add_text_block(parts, c, "La versión final combina scraping, extracción estructurada, metadatos de contexto, visualización del grafo y un LLM que responde usando evidencia recuperada. El resultado es un sistema más explicable, más trazable y más fiel al patrón moderno de sistema experto que pide la práctica.", width=1040, font_size=29, line_gap=10)
    return finish(parts)


def render_pages() -> list[str]:
    total = 8
    graph_uri = graph_png_data_uri()
    return [
        build_cover(total),
        build_page_2(total),
        build_page_3(total),
        build_graph_page(total, graph_uri),
        build_page_5(total),
        build_page_6(total),
        build_page_7(total),
        build_page_8(total),
    ]


def svg_to_pdf(svg_path: Path, pdf_path: Path) -> None:
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(svg_path)], check=True)


def merge_pdfs(pdf_paths: list[Path], output_pdf: Path) -> None:
    subprocess.run(["pdfunite", *[str(p) for p in pdf_paths], str(output_pdf)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un PDF editorial para la entrega final")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "proyecto8_final_fantasy_entrega.pdf")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    svg_pages = render_pages()
    pdf_paths: list[Path] = []
    for index, svg in enumerate(svg_pages, start=1):
        svg_path = TMP_DIR / f"pretty_page_{index:02d}.svg"
        pdf_path = TMP_DIR / f"pretty_page_{index:02d}.pdf"
        svg_path.write_text(svg, encoding="utf-8")
        svg_to_pdf(svg_path, pdf_path)
        pdf_paths.append(pdf_path)

    merge_pdfs(pdf_paths, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
