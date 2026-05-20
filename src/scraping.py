from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common import DATA_DIR, RAW_DIR, ensure_dirs, now_iso, reader_candidates, reader_url, slugify_url, write_json, write_text


def load_seed_urls(seed_file: Path) -> list[str]:
    return [
        line.strip()
        for line in seed_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def fetch_markdown(url: str) -> str:
    for target in reader_candidates(url):
        try:
            request = Request(
                target,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8", errors="replace")
                if payload.startswith("Title:"):
                    return payload
        except (HTTPError, URLError, TimeoutError):
            pass

        result = subprocess.run(
            ["/bin/zsh", "-lc", f'curl -L "{target}"'],
            capture_output=True,
            text=True,
        )
        payload = result.stdout
        if result.returncode == 0 and payload.startswith("Title:"):
            return payload

    raise RuntimeError(f"No se pudo descargar una versión válida de {url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga páginas en Markdown usando r.jina.ai")
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DATA_DIR / "seed_urls.txt",
        help="Fichero con URLs iniciales",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Pausa entre descargas para no martillear la fuente",
    )
    args = parser.parse_args()

    ensure_dirs()
    urls = load_seed_urls(args.seed_file)
    manifest: list[dict[str, str]] = []

    for url in urls:
        slug = slugify_url(url)
        target = RAW_DIR / f"{slug}.md"
        print(f"Descargando {url}")
        try:
            markdown = fetch_markdown(url)
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            print(f"  ERROR: {exc}")
            continue

        write_text(target, markdown)
        manifest.append(
            {
                "url": url,
                "reader_url": reader_url(url),
                "file": str(target.relative_to(DATA_DIR.parent)),
                "downloaded_at": now_iso(),
            }
        )
        time.sleep(args.delay)

    write_json(DATA_DIR / "manifest.json", manifest)
    print(f"Guardadas {len(manifest)} páginas en {RAW_DIR}")


if __name__ == "__main__":
    main()
