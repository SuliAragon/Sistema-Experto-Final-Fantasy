from __future__ import annotations

import argparse
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from common import GRAPHS_DIR, read_json


def load_edges(path: Path) -> list[dict[str, object]]:
    graph = read_json(path)
    return graph["edges"]


def build_index(edges: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    index: dict[str, list[dict[str, object]]] = defaultdict(list)
    for edge in edges:
        index[str(edge["predicate"])].append(edge)
    return index


def parse_year(date_text: str) -> int | None:
    match = re.search(r"(19|20)\d{2}", date_text)
    return int(match.group(0)) if match else None


def normalize_date(date_text: str) -> str:
    text = date_text.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text

    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    match = re.fullmatch(r"(\d{1,2}) de ([a-záéíóú]+) de (\d{4})", text.lower())
    if not match:
        return text

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    month = months.get(month_name)
    if not month:
        return text
    return date(year, month, day).isoformat()


def cite(edge: dict[str, object]) -> str:
    source = edge.get("provenance", "desconocida")
    valid_from = edge.get("valido_desde") or edge.get("fecha_extraccion") or "sin fecha"
    return f"Fuente: {source} | Fecha: {valid_from}"


def answer_ps5_after_year(index: dict[str, list[dict[str, object]]], year: int) -> str:
    platforms = {edge["subject"] for edge in index["available_on"] if edge["object"] == "PS5"}
    release_edges = [edge for edge in index["released_on"] if edge["subject"] in platforms]
    selected = [edge for edge in release_edges if (parse_year(str(edge["object"])) or 0) > year]
    if not selected:
        return "No tengo contexto suficiente para responder con evidencia."

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for edge in selected:
        grouped[(str(edge["subject"]), normalize_date(str(edge["object"])))].append(edge)

    lines = ["Juegos de Final Fantasy en PS5 posteriores al año indicado:"]
    for (game, normalized_date), grouped_edges in sorted(grouped.items(), key=lambda item: item[0][1]):
        citations = " | ".join(sorted({cite(edge) for edge in grouped_edges}))
        lines.append(f"- {game} -> lanzamiento: {normalized_date} ({citations})")
    return "\n".join(lines)


def answer_remakes(index: dict[str, list[dict[str, object]]]) -> str:
    remake_edges = index["is_remake_of"]
    if not remake_edges:
        return "No tengo contexto suficiente para responder con evidencia."
    lines = ["Remakes detectados en las fuentes:"]
    for edge in remake_edges:
        lines.append(f"- {edge['subject']} es remake de {edge['object']} ({cite(edge)})")
    return "\n".join(lines)


def answer_multi_hop_remake_square(index: dict[str, list[dict[str, object]]]) -> str:
    remakes = {edge["subject"]: edge for edge in index["is_remake_of"]}
    square_games = {
        edge["subject"]: edge
        for edge in index["developed_by"]
        if str(edge["object"]).lower() == "square enix"
    }
    intersection = sorted(set(remakes) & set(square_games))
    if not intersection:
        return "No tengo contexto suficiente para responder con evidencia."

    lines = ["Remakes desarrollados por Square Enix encontrados en el grafo:"]
    for game in intersection:
        remake_edge = remakes[game]
        dev_edge = square_games[game]
        lines.append(
            f"- {game} -> original: {remake_edge['object']} "
            f"({cite(remake_edge)}; {cite(dev_edge)})"
        )
    return "\n".join(lines)


def answer(question: str, edges: list[dict[str, object]]) -> str:
    index = build_index(edges)
    normalized = question.lower()

    if "ps5" in normalized:
        year_match = re.search(r"(19|20)\d{2}", normalized)
        year = int(year_match.group(0)) if year_match else 2020
        return answer_ps5_after_year(index, year)

    if "remake" in normalized and ("square enix" in normalized or "original" in normalized):
        return answer_multi_hop_remake_square(index)

    if "remake" in normalized:
        return answer_remakes(index)

    return "No tengo contexto suficiente para responder con evidencia."


def main() -> None:
    parser = argparse.ArgumentParser(description="Hace preguntas al context graph")
    parser.add_argument("--question", required=True, help="Pregunta en lenguaje natural")
    parser.add_argument(
        "--graph",
        type=Path,
        default=GRAPHS_DIR / "context_graph.json",
        help="Grafo JSON con metadatos",
    )
    args = parser.parse_args()

    edges = load_edges(args.graph)
    print(answer(args.question, edges))


if __name__ == "__main__":
    main()
