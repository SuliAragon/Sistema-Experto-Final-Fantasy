from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common import RAW_DIR, TRIPLETS_DIR, ensure_dirs, load_openrouter_config, normalize_label, normalize_space, read_text, write_json


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def extract_source_url(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("URL Source:"):
            return line.split("URL Source:", 1)[1].strip()
    return "desconocida"


def extract_relevant_text(markdown: str) -> str:
    start = markdown.find("Sobre el juego")
    end = markdown.find("## Videos")
    if start != -1 and end != -1 and end > start:
        return markdown[start:end].strip()
    return markdown[:6000].strip()


def build_prompt(markdown: str, extraction_date: str) -> str:
    source_url = extract_source_url(markdown)
    trimmed = extract_relevant_text(markdown)
    return f"""
Extrae tripletas factuales desde esta página de videojuego.

Devuelve SOLO JSON válido con esta forma:
{{
  "triplets": [
    {{
      "subject": "...",
      "predicate": "...",
      "object": "...",
      "source": "...",
      "fecha_extraccion": "{extraction_date}",
      "valido_desde": null,
      "valido_hasta": null,
      "confianza": 0.0,
      "evidence": "..."
    }}
  ]
}}

Reglas:
- Usa solo hechos explícitos en el texto.
- Predicados en snake_case.
- Incluye entre 6 y 14 tripletas.
- Incluye siempre source con ESTE valor exacto: {source_url}
- confianza entre 0 y 1.
- evidence debe ser un fragmento corto del texto fuente.
- Prioriza relaciones como released_on, available_on, developed_by, published_by, has_genre, is_remake_of, belongs_to_universe, has_type.
- Si hay varias plataformas, crea una tripleta por plataforma.
- Si falta un dato, no lo inventes.
- No expliques nada fuera del JSON.

Texto fuente:
{trimmed}
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


def normalize_triplets(triplets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in triplets:
        subject = normalize_label(str(item.get("subject", "")))
        predicate = normalize_label(str(item.get("predicate", ""))).lower().replace(" ", "_")
        obj = normalize_label(str(item.get("object", "")))
        if not subject or not predicate or not obj:
            continue
        normalized.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "source": normalize_space(str(item.get("source", ""))),
                "fecha_extraccion": str(item.get("fecha_extraccion", "")),
                "valido_desde": item.get("valido_desde"),
                "valido_hasta": item.get("valido_hasta"),
                "confianza": float(item.get("confianza", 0.7)),
                "evidence": normalize_space(str(item.get("evidence", "")))[:500],
            }
        )
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae tripletas con OpenRouter desde páginas Markdown")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output", type=Path, default=TRIPLETS_DIR / "llm_triplets.json")
    parser.add_argument("--date", default="2026-05-20")
    parser.add_argument("--only", nargs="*", help="Lista opcional de ficheros .md concretos")
    args = parser.parse_args()

    ensure_dirs()
    config = load_openrouter_config()
    if not config["api_key"]:
        raise SystemExit("Falta OPENROUTER_API_KEY o secrets.toml con [openrouter].api_key")

    files = sorted(args.raw_dir.glob("*.md"))
    if args.only:
        wanted = set(args.only)
        files = [path for path in files if path.name in wanted]

    all_triplets: list[dict[str, Any]] = []
    for path in files:
        markdown = read_text(path)
        body = {
            "model": config["model"],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Eres un extractor de conocimiento preciso."},
                {"role": "user", "content": build_prompt(markdown, args.date)},
            ],
        }
        print(f"Extrayendo con LLM: {path.name}", flush=True)
        response = post_openrouter(body, config["api_key"])
        if "error" in response:
            raise SystemExit(f"OpenRouter devolvió error para {path.name}: {response['error']}")
        content = response["choices"][0]["message"]["content"]
        payload = json.loads(content)
        all_triplets.extend(normalize_triplets(payload.get("triplets", [])))

    write_json(args.output, all_triplets)
    print(f"Tripletas LLM guardadas en {args.output}")


if __name__ == "__main__":
    main()
