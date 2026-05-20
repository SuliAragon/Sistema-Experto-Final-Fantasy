from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common import GRAPHS_DIR, load_openrouter_config, read_json


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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


def edge_citation(edge: dict[str, object]) -> str:
    source = str(edge.get("provenance", "desconocida"))
    valid_from = edge.get("valido_desde") or edge.get("fecha_extraccion") or "sin fecha"
    return f"Fuente: {source} | Fecha: {valid_from}"


def evidence_record(edge: dict[str, object]) -> dict[str, object]:
    return {
        "subject": edge["subject"],
        "predicate": edge["predicate"],
        "object": edge["object"],
        "source": edge.get("provenance", "desconocida"),
        "date": edge.get("valido_desde") or edge.get("fecha_extraccion") or "sin fecha",
        "confidence": edge.get("confianza"),
        "evidence": edge.get("evidence", ""),
    }


def retrieve_ps5_after_year(index: dict[str, list[dict[str, object]]], year: int) -> list[dict[str, object]]:
    platform_edges = [edge for edge in index["available_on"] if edge["object"] == "PS5"]
    platforms = {edge["subject"] for edge in platform_edges}
    release_edges = [edge for edge in index["released_on"] if edge["subject"] in platforms]
    selected = [edge for edge in release_edges if (parse_year(str(edge["object"])) or 0) > year]

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for edge in selected:
        grouped[(str(edge["subject"]), normalize_date(str(edge["object"])))].append(edge)

    results: list[dict[str, object]] = []
    for (game, _), group_edges in sorted(grouped.items(), key=lambda item: item[0][1]):
        best_edge = sorted(
            group_edges,
            key=lambda edge: (
                str(edge.get("provenance", "")).startswith("https://www.3djuegos.com/juegos/"),
                bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(edge["object"]))),
                float(edge.get("confianza", 0)),
            ),
            reverse=True,
        )[0]
        results.append(
            evidence_record(
                sorted(
                    [edge for edge in platform_edges if edge["subject"] == game],
                    key=lambda edge: (
                        str(edge.get("provenance", "")).startswith("https://www.3djuegos.com/juegos/"),
                        float(edge.get("confianza", 0)),
                    ),
                    reverse=True,
                )[0]
            )
        )
        results.append(evidence_record(best_edge))
    return results


def retrieve_remakes(index: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    return [evidence_record(edge) for edge in index["is_remake_of"]]


def retrieve_multi_hop_remake_square(index: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    remakes = {edge["subject"]: edge for edge in index["is_remake_of"]}
    developers = {
        edge["subject"]: edge
        for edge in index["developed_by"]
        if str(edge["object"]).lower() == "square enix"
    }

    results: list[dict[str, object]] = []
    for game in sorted(set(remakes) & set(developers)):
        results.append(evidence_record(remakes[game]))
        results.append(evidence_record(developers[game]))
    return results


def retrieve_generic(question: str, edges: list[dict[str, object]], limit: int = 18) -> list[dict[str, object]]:
    tokens = {token for token in re.findall(r"[a-z0-9áéíóúüñ]+", question.lower()) if len(token) > 2}
    scored: list[tuple[int, dict[str, object]]] = []
    for edge in edges:
        haystack = " ".join(
            [
                str(edge.get("subject", "")),
                str(edge.get("predicate", "")),
                str(edge.get("object", "")),
                str(edge.get("evidence", "")),
            ]
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score > 0:
            scored.append((score, edge))

    scored.sort(key=lambda item: (item[0], float(item[1].get("confianza", 0))), reverse=True)
    return [evidence_record(edge) for _, edge in scored[:limit]]


def retrieve_evidence(question: str, edges: list[dict[str, object]]) -> list[dict[str, object]]:
    index = build_index(edges)
    normalized = question.lower()

    if "ps5" in normalized:
        year_match = re.search(r"(19|20)\d{2}", normalized)
        year = int(year_match.group(0)) if year_match else 2020
        return retrieve_ps5_after_year(index, year)

    if "remake" in normalized and ("square enix" in normalized or "original" in normalized):
        return retrieve_multi_hop_remake_square(index)

    if "remake" in normalized:
        return retrieve_remakes(index)

    return retrieve_generic(question, edges)


def build_prompt(question: str, evidence: list[dict[str, object]]) -> str:
    evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    return f"""
Responde la pregunta del usuario usando EXCLUSIVAMENTE la evidencia estructurada proporcionada.

Reglas:
- No inventes hechos.
- Si la evidencia no basta, responde exactamente: No tengo contexto suficiente.
- Responde en español.
- Cita siempre la fuente y la fecha de cada hecho relevante.
- Si hay varios hechos, usa viñetas breves.
- Si la pregunta es multi-hop, razona solo conectando hechos presentes en la evidencia.

Pregunta:
{question}

Evidencia:
{evidence_json}
""".strip()


def post_openrouter(body: dict[str, Any], api_key: str) -> dict[str, Any]:
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = Request(
        OPENROUTER_URL,
        data=raw,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError):
        result = subprocess.run(
            [
                "curl",
                "--max-time",
                "90",
                "-L",
                OPENROUTER_URL,
                "-H",
                f"Authorization: Bearer {api_key}",
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                "@-",
            ],
            input=json.dumps(body, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)


def answer_with_llm(question: str, evidence: list[dict[str, object]], api_key: str, model: str) -> str:
    if not evidence:
        return "No tengo contexto suficiente."

    body = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": "Eres un sistema experto que responde solo con evidencia recuperada desde un context graph.",
            },
            {
                "role": "user",
                "content": build_prompt(question, evidence),
            },
        ],
    }
    response = post_openrouter(body, api_key)
    if "error" in response:
        raise RuntimeError(str(response["error"]))
    return str(response["choices"][0]["message"]["content"]).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pregunta al context graph usando LLM como motor de inferencia")
    parser.add_argument("--question", required=True, help="Pregunta en lenguaje natural")
    parser.add_argument(
        "--graph",
        type=Path,
        default=GRAPHS_DIR / "context_graph.json",
        help="Grafo JSON con metadatos",
    )
    parser.add_argument(
        "--show-evidence",
        action="store_true",
        help="Muestra también la evidencia recuperada antes de la respuesta final",
    )
    args = parser.parse_args()

    config = load_openrouter_config()
    if not config["api_key"]:
        raise SystemExit("Falta OPENROUTER_API_KEY o secrets.toml con [openrouter].api_key")

    edges = load_edges(args.graph)
    evidence = retrieve_evidence(args.question, edges)

    if args.show_evidence:
        print("EVIDENCIA RECUPERADA:")
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        print()

    print(answer_with_llm(args.question, evidence, config["api_key"], config["model"]))


if __name__ == "__main__":
    main()
