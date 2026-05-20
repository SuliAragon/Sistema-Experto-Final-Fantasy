from __future__ import annotations

from common import GRAPHS_DIR, read_json


def main() -> None:
    context_graph = read_json(GRAPHS_DIR / "context_graph.json")
    baseline_graph = read_json(GRAPHS_DIR / "baseline_graph.json")

    context_edges = context_graph["edges"]
    baseline_edges = baseline_graph["edges"]

    context_with_dates = sum(1 for edge in context_edges if edge.get("valido_desde"))
    context_with_sources = sum(1 for edge in context_edges if edge.get("provenance"))

    print("Comparación baseline vs context graph")
    print()
    print(f"- Aristas baseline: {len(baseline_edges)}")
    print(f"- Aristas context graph: {len(context_edges)}")
    print(f"- Aristas con fecha de vigencia: {context_with_dates}")
    print(f"- Aristas con fuente trazable: {context_with_sources}")
    print()
    print("Conclusión breve:")
    print(
        "- El baseline permite saber que existen relaciones entre juegos, plataformas o géneros, "
        "pero no permite justificar de dónde sale cada hecho."
    )
    print(
        "- El context graph añade procedencia y fecha, por lo que sí puede responder preguntas temporales "
        "y citar la página concreta de 3DJuegos usada como evidencia."
    )


if __name__ == "__main__":
    main()
