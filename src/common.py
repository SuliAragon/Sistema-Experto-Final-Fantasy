from __future__ import annotations

import json
import os
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw_md"
TRIPLETS_DIR = ROOT / "triplets"
GRAPHS_DIR = ROOT / "graphs"
FIGURES_DIR = ROOT / "figures"


def ensure_dirs() -> None:
    for directory in (RAW_DIR, TRIPLETS_DIR, GRAPHS_DIR, FIGURES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    raw = f"{parsed.netloc}{parsed.path}".strip("/")
    raw = raw.replace("/", "_")
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", raw).strip("-").lower()


def reader_url(url: str) -> str:
    return f"https://r.jina.ai/http://{url}"


def reader_candidates(url: str) -> list[str]:
    stripped = url.strip()
    no_scheme = re.sub(r"^https?://", "", stripped)
    return [
        f"https://r.jina.ai/http://{stripped}",
        f"https://r.jina.ai/http://{no_scheme}",
        f"https://r.jina.ai/http://http://{no_scheme}",
    ]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_label(value: str) -> str:
    return normalize_space(value).strip(" .")


def load_openrouter_config() -> dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()

    secrets_path = ROOT / "secrets.toml"
    if secrets_path.exists():
        with secrets_path.open("rb") as handle:
            payload = tomllib.load(handle)
        openrouter = payload.get("openrouter", {})
        if not api_key:
            api_key = str(openrouter.get("api_key", "")).strip()
        if not model:
            model = str(openrouter.get("model", "")).strip()

    return {
        "api_key": api_key,
        "model": model or "openai/gpt-4.1-mini",
    }
