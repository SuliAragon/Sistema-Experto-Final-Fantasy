from __future__ import annotations

import argparse
from pathlib import Path

from common import TRIPLETS_DIR, read_json, write_json


def deduplicate(triples: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[dict[str, object]] = []
    for triple in triples:
        key = (
            str(triple.get("subject", "")),
            str(triple.get("predicate", "")),
            str(triple.get("object", "")),
            str(triple.get("source", "")),
        )
        if key not in seen:
            seen.add(key)
            result.append(triple)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Combina tripletas baseline/rule-based con tripletas LLM")
    parser.add_argument("--base", type=Path, default=TRIPLETS_DIR / "context_triplets.json")
    parser.add_argument("--llm", type=Path, default=TRIPLETS_DIR / "llm_triplets.json")
    parser.add_argument("--output", type=Path, default=TRIPLETS_DIR / "context_triplets_merged.json")
    args = parser.parse_args()

    base = read_json(args.base)
    llm = read_json(args.llm)
    merged = deduplicate(list(base) + list(llm))
    write_json(args.output, merged)
    print(f"Tripletas base: {len(base)}")
    print(f"Tripletas LLM: {len(llm)}")
    print(f"Tripletas combinadas: {len(merged)}")


if __name__ == "__main__":
    main()
