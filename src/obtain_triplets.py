from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import RAW_DIR, TRIPLETS_DIR, ensure_dirs, normalize_label, normalize_space, now_iso, read_text, write_json


TRIPLET_KEYS = (
    "subject",
    "predicate",
    "object",
    "source",
    "fecha_extraccion",
    "valido_desde",
    "valido_hasta",
    "confianza",
    "evidence",
)


def make_triplet(
    subject: str,
    predicate: str,
    obj: str,
    source: str,
    evidence: str,
    *,
    valido_desde: str | None = None,
    valido_hasta: str | None = None,
    confianza: float = 0.85,
) -> dict[str, object]:
    payload = {
        "subject": normalize_label(subject),
        "predicate": predicate,
        "object": normalize_label(obj),
        "source": source,
        "fecha_extraccion": now_iso(),
        "valido_desde": valido_desde,
        "valido_hasta": valido_hasta,
        "confianza": round(confianza, 2),
        "evidence": normalize_space(evidence)[:500],
    }
    return payload


def source_url(markdown: str) -> str:
    match = re.search(r"URL Source:\s*(https?://\S+)", markdown)
    return match.group(1) if match else "desconocida"


def parse_detail_page(markdown: str) -> list[dict[str, object]]:
    triples: list[dict[str, object]] = []
    url = source_url(markdown)

    title_match = re.search(r"Sobre el juego\s+.*?\n# ([^\n]+)\n", markdown, re.S)
    if not title_match:
        title_match = re.search(r"\n# ([^\n|]+?)(?: para [^|\n]+)?(?: \| 3DJuegos)?\n", markdown)
    if not title_match:
        return triples
    game = normalize_label(title_match.group(1))

    universe_match = re.search(r"Universo\s+\n+\[Juegos de ([^\]]+)\]", markdown)
    if universe_match:
        triples.append(
            make_triplet(
                game,
                "belongs_to_universe",
                universe_match.group(1),
                url,
                universe_match.group(0),
                confianza=0.95,
            )
        )

    release_match = re.search(r"Fecha de lanzamiento:\s*\[([^\]]+)\]", markdown)
    if release_match:
        release_date = normalize_label(release_match.group(1))
        triples.append(
            make_triplet(
                game,
                "released_on",
                release_date,
                url,
                release_match.group(0),
                valido_desde=release_date,
                confianza=0.95,
            )
        )

    platform_block = re.search(r"· Plataforma\s+\n+([^\n]+)", markdown)
    if platform_block:
        platforms = [token for token in normalize_space(platform_block.group(1)).split() if token]
        for platform in platforms:
            triples.append(
                make_triplet(
                    game,
                    "available_on",
                    platform,
                    url,
                    platform_block.group(0),
                    confianza=0.9,
                )
            )

    metadata_line = re.search(
        r"Tipo:(.*?)Desarrollador:\[(.*?)\].*?Editor:\[(.*?)\].*?Género:(.*?)(?:Jugadores:|Duración:|Idioma:|Lanzamiento:)",
        markdown,
        re.S,
    )
    if metadata_line:
        raw_type, developer, editor, raw_genres = metadata_line.groups()
        raw_type = raw_type.split("Comprar Para:", 1)[0]
        raw_type = normalize_space(re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: m.group(0).split("[", 1)[1].split("]", 1)[0], raw_type))
        developer = normalize_label(developer)
        editor = normalize_label(editor)
        triples.append(make_triplet(game, "developed_by", developer, url, developer, confianza=0.95))
        triples.append(make_triplet(game, "published_by", editor, url, editor, confianza=0.95))

        if raw_type:
            if "Remake de" in raw_type:
                original = normalize_label(raw_type.split("Remake de", 1)[1])
                triples.append(make_triplet(game, "is_remake_of", original, url, raw_type, confianza=0.92))
                triples.append(make_triplet(game, "has_type", "Remake", url, raw_type, confianza=0.92))
            else:
                triples.append(make_triplet(game, "has_type", raw_type, url, raw_type, confianza=0.88))

        genre_names = re.findall(r"\[([^\]]+)\]", raw_genres)
        seen: set[str] = set()
        for genre in genre_names:
            genre = normalize_label(genre)
            if genre and genre not in seen:
                triples.append(make_triplet(game, "has_genre", genre, url, genre, confianza=0.88))
                seen.add(genre)

    review_label = re.search(r"\[Analisis\].*?\n\n“([^”]+)”", markdown, re.S)
    if review_label:
        triples.append(
            make_triplet(
                game,
                "has_review_label",
                review_label.group(1),
                url,
                review_label.group(0),
                confianza=0.9,
            )
        )

    score_match = re.search(r"\n“[^”]+”\n\n(\d+(?:,\d+)?)\n", markdown)
    if score_match:
        triples.append(
            make_triplet(
                game,
                "has_reader_score",
                score_match.group(1).replace(",", "."),
                url,
                score_match.group(0),
                confianza=0.75,
            )
        )

    return triples


def parse_universe_page(markdown: str) -> list[dict[str, object]]:
    triples: list[dict[str, object]] = []
    url = source_url(markdown)
    universe_name = "Final Fantasy"
    lines = markdown.splitlines()
    pending_description: dict[str, str] = {}

    for index, line in enumerate(lines):
        if not line.startswith("[![Image "):
            continue

        title_match = re.search(r": ([^\]]+)\]", line)
        link_match = re.search(r"\]\((https?://www\.3djuegos\.com/juegos/[^)]+)\)", line)
        platform_match = re.search(r"\)\)([A-Za-z0-9 +]+)\[", line)
        date_match = re.search(r" / ([^\n]+)$", line)
        genres = re.findall(r"\[([^\]]+)\]\(https?://www\.3djuegos\.com/generos/[^)]+\)", line)

        if not title_match or not link_match:
            continue

        title = normalize_label(title_match.group(1))
        game_url = link_match.group(1)
        platform = normalize_label(platform_match.group(1)) if platform_match else None
        release_date = normalize_label(date_match.group(1)) if date_match else None

        triples.append(
            make_triplet(
                title,
                "belongs_to_universe",
                universe_name,
                url,
                line,
                confianza=0.9,
            )
        )

        triples.append(
            make_triplet(
                title,
                "has_source_page",
                game_url,
                url,
                line,
                confianza=0.9,
            )
        )

        if platform:
            triples.append(
                make_triplet(
                    title,
                    "available_on",
                    platform,
                    url,
                    line,
                    confianza=0.88,
                )
            )

        if release_date:
            triples.append(
                make_triplet(
                    title,
                    "released_on",
                    release_date,
                    url,
                    line,
                    valido_desde=release_date,
                    confianza=0.88,
                )
            )

        for genre in genres:
            triples.append(
                make_triplet(
                    title,
                    "has_genre",
                    genre,
                    url,
                    line,
                    confianza=0.82,
                )
            )

        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if next_line and not next_line.startswith("[![Image ") and len(next_line) > 20:
            pending_description[title] = next_line

    for title, description in pending_description.items():
        triples.append(
            make_triplet(
                title,
                "has_summary",
                description,
                url,
                description,
                confianza=0.7,
            )
        )

    return triples


def deduplicate(triples: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[dict[str, object]] = []
    for triple in triples:
        key = (
            str(triple["subject"]),
            str(triple["predicate"]),
            str(triple["object"]),
            str(triple["source"]),
        )
        if key not in seen:
            seen.add(key)
            result.append(triple)
    return result


def to_baseline(triples: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {
            "subject": str(item["subject"]),
            "predicate": str(item["predicate"]),
            "object": str(item["object"]),
        }
        for item in triples
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae tripletas y metadatos desde Markdown de 3DJuegos")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Carpeta con páginas scrapeadas",
    )
    args = parser.parse_args()

    ensure_dirs()
    triples: list[dict[str, object]] = []

    for markdown_file in sorted(args.raw_dir.glob("*.md")):
        markdown = read_text(markdown_file)
        if "/universo/" in source_url(markdown):
            triples.extend(parse_universe_page(markdown))
        else:
            triples.extend(parse_detail_page(markdown))

    triples = deduplicate(triples)
    baseline = to_baseline(triples)

    write_json(TRIPLETS_DIR / "context_triplets.json", triples)
    write_json(TRIPLETS_DIR / "baseline_triplets.json", baseline)
    print(f"Tripletas con metadatos: {len(triples)}")
    print(f"Tripletas baseline: {len(baseline)}")


if __name__ == "__main__":
    main()
