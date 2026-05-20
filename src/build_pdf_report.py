from __future__ import annotations

import argparse
import re
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = ROOT / "report" / "informe_final.md"
GRAPH_SVG = ROOT / "figures" / "context_graph.svg"
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"

PAGE_WIDTH = 92
PAGE_HEIGHT = 56


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_inline(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("**", "")
    text = text.replace("*", "")
    return text


def replace_mermaid_block(markdown: str) -> str:
    replacement = """
Arquitectura resumida del pipeline:

- URLs semilla de 3DJuegos
- scraping.py
- Markdown en data/raw_md
- obtain_triplets.py (reglas)
- obtain_triplets_llm.py (OpenRouter)
- merge_triplets.py
- context_graph.py
- graphs/context_graph.json
- ask.py y ask_llm.py
""".strip()
    return re.sub(r"```mermaid.*?```", replacement, markdown, flags=re.S)


def markdown_to_lines(markdown: str) -> list[str]:
    markdown = replace_mermaid_block(markdown)
    lines: list[str] = []
    in_code = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            in_code = not in_code
            if not in_code:
                lines.append("")
            continue

        if in_code:
            wrapped = textwrap.wrap(line, width=PAGE_WIDTH) or [""]
            lines.extend(wrapped)
            continue

        if not line.strip():
            lines.append("")
            continue

        if line.startswith("# "):
            title = normalize_inline(line[2:]).upper()
            lines.extend(["", title, "=" * min(len(title), PAGE_WIDTH), ""])
            continue

        if line.startswith("## "):
            title = normalize_inline(line[3:]).upper()
            lines.extend(["", title, "-" * min(len(title), PAGE_WIDTH), ""])
            continue

        if line.startswith("### "):
            title = normalize_inline(line[4:])
            lines.extend(["", title, ""])
            continue

        if line.startswith("- "):
            bullet_text = normalize_inline(line[2:])
            wrapped = textwrap.wrap(
                bullet_text,
                width=PAGE_WIDTH - 4,
                initial_indent="- ",
                subsequent_indent="  ",
            )
            lines.extend(wrapped)
            continue

        if re.match(r"\d+\.\s", line):
            text = normalize_inline(line)
            wrapped = textwrap.wrap(
                text,
                width=PAGE_WIDTH - 2,
                subsequent_indent="   ",
            )
            lines.extend(wrapped)
            continue

        paragraph = normalize_inline(line)
        wrapped = textwrap.wrap(paragraph, width=PAGE_WIDTH) or [""]
        lines.extend(wrapped)

    return cleanup_blank_lines(lines)


def cleanup_blank_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        blank = line.strip() == ""
        if blank and previous_blank:
            continue
        cleaned.append(line)
        previous_blank = blank
    return cleaned


def build_cover_page() -> list[str]:
    cover = [
        "",
        "",
        "PROYECTO 8",
        "",
        "DEL SISTEMA EXPERTO AL CONTEXT GRAPH",
        "",
        "Sistema experto moderno sobre la saga Final Fantasy",
        "usando 3DJuegos, context graph y OpenRouter",
        "",
        "",
        "Entrega en formato PDF",
        "",
        "Contenido:",
        "- Objetivos y justificacion del dominio",
        "- Arquitectura del pipeline",
        "- Construccion del grafo y metadatos",
        "- Preguntas y respuestas con citas",
        "- Comparacion baseline vs context graph",
        "- Reflexion final",
        "",
        "",
        "Autor: SuliAragon",
    ]
    while len(cover) < PAGE_HEIGHT:
        cover.append("")
    return cover[:PAGE_HEIGHT]


def paginate(lines: list[str]) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if len(current) >= PAGE_HEIGHT:
            pages.append(current)
            current = []
        current.append(line)

    if current:
        pages.append(current)

    return pages


def render_pages_to_text(pages: list[list[str]]) -> str:
    chunks: list[str] = []
    total = len(pages)
    for index, page in enumerate(pages, start=1):
        body = list(page)
        while len(body) < PAGE_HEIGHT - 2:
            body.append("")
        body.append("")
        body.append(f"Pagina {index} de {total}")
        chunks.append("\n".join(body))
    return "\f".join(chunks)


def build_body_pdf(text_path: Path, pdf_path: Path) -> None:
    command = [
        "cupsfilter",
        "-m",
        "application/pdf",
        str(text_path),
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    pdf_path.write_bytes(result.stdout)


def build_graph_pdf(svg_path: Path, pdf_path: Path) -> None:
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(pdf_path), str(svg_path)],
        check=True,
    )


def merge_pdfs(inputs: list[Path], output: Path) -> None:
    subprocess.run(["pdfunite", *[str(path) for path in inputs], str(output)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un PDF final del informe de entrega")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "proyecto8_final_fantasy_entrega.pdf",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    markdown = read_markdown(REPORT_MD)
    cover_page = build_cover_page()
    body_lines = markdown_to_lines(markdown)
    pages = [cover_page] + paginate(body_lines)
    text_payload = render_pages_to_text(pages)

    body_txt = TMP_DIR / "report_body.txt"
    body_pdf = TMP_DIR / "report_body.pdf"
    graph_pdf = TMP_DIR / "graph_page.pdf"

    body_txt.write_text(text_payload, encoding="utf-8")
    build_body_pdf(body_txt, body_pdf)
    build_graph_pdf(GRAPH_SVG, graph_pdf)
    merge_pdfs([body_pdf, graph_pdf], args.output)

    print(args.output)


if __name__ == "__main__":
    main()
