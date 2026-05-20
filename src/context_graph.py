from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from common import FIGURES_DIR, GRAPHS_DIR, TRIPLETS_DIR, ensure_dirs, read_json, write_json


def infer_node_type(label: str, outgoing_predicates: set[str], incoming_predicates: set[str]) -> str:
    if "belongs_to_universe" in incoming_predicates:
        return "universe"
    if any(predicate in outgoing_predicates for predicate in {"available_on", "developed_by", "released_on"}):
        return "game"
    if any(predicate in incoming_predicates for predicate in {"available_on"}):
        return "platform"
    if any(predicate in incoming_predicates for predicate in {"developed_by", "published_by"}):
        return "company"
    if any(predicate in incoming_predicates for predicate in {"has_genre"}):
        return "genre"
    if any(predicate in incoming_predicates for predicate in {"released_on"}):
        return "date"
    if any(predicate in incoming_predicates for predicate in {"has_review_label"}):
        return "review"
    return "entity"


def build_graph(triples: list[dict[str, object]]) -> dict[str, object]:
    nodes: dict[str, dict[str, object]] = {}
    outgoing: dict[str, set[str]] = {}
    incoming: dict[str, set[str]] = {}

    for triple in triples:
        subject = str(triple["subject"])
        obj = str(triple["object"])
        predicate = str(triple["predicate"])

        outgoing.setdefault(subject, set()).add(predicate)
        incoming.setdefault(obj, set()).add(predicate)

    all_labels = set(outgoing) | set(incoming)
    for label in all_labels:
        nodes[label] = {
            "id": label,
            "label": label,
            "type": infer_node_type(label, outgoing.get(label, set()), incoming.get(label, set())),
        }

    edges = []
    for triple in triples:
        edge = {
            "subject": str(triple["subject"]),
            "object": str(triple["object"]),
            "predicate": str(triple["predicate"]),
        }
        if "source" in triple:
            edge["provenance"] = triple["source"]
        for key in ("fecha_extraccion", "valido_desde", "valido_hasta", "confianza", "evidence"):
            if key in triple:
                edge[key] = triple[key]
        edges.append(edge)

    return {"nodes": list(nodes.values()), "edges": edges}


def choose_subgraph(graph: dict[str, object], max_nodes: int = 60) -> dict[str, object]:
    nodes = graph["nodes"]
    edges = graph["edges"]
    degrees = Counter()
    for edge in edges:
        degrees[edge["subject"]] += 1
        degrees[edge["object"]] += 1

    selected = []
    selected_ids: set[str] = set()

    for node in sorted(nodes, key=lambda item: (item["type"] != "universe", -degrees[item["id"]], item["label"])):
        if len(selected) >= max_nodes:
            break
        if degrees[node["id"]] == 0:
            continue
        selected.append(node)
        selected_ids.add(node["id"])

    selected_edges = [
        edge
        for edge in edges
        if edge["subject"] in selected_ids and edge["object"] in selected_ids
    ]
    return {"nodes": selected, "edges": selected_edges}


def node_color(node_type: str) -> str:
    palette = {
        "universe": "#6b4f2a",
        "game": "#2b6cb0",
        "platform": "#2f855a",
        "company": "#805ad5",
        "genre": "#dd6b20",
        "date": "#718096",
        "review": "#c53030",
        "entity": "#4a5568",
    }
    return palette.get(node_type, "#4a5568")


def render_svg(graph: dict[str, object], output_path: Path) -> None:
    width = 1600
    height = 1200
    center_x = width / 2
    center_y = height / 2

    rings = {
        "universe": 0,
        "game": 1,
        "platform": 2,
        "company": 2,
        "genre": 2,
        "date": 3,
        "review": 3,
        "entity": 3,
    }
    radii = {0: 120, 1: 260, 2: 430, 3: 560}

    nodes_by_ring: dict[int, list[dict[str, object]]] = {0: [], 1: [], 2: [], 3: []}
    for node in graph["nodes"]:
        nodes_by_ring[rings.get(node["type"], 3)].append(node)

    positions: dict[str, tuple[float, float]] = {}
    for ring, ring_nodes in nodes_by_ring.items():
        if not ring_nodes:
            continue
        if ring == 0:
            if len(ring_nodes) == 1:
                positions[ring_nodes[0]["id"]] = (center_x, center_y)
                continue
            radius = radii[ring]
            for index, node in enumerate(sorted(ring_nodes, key=lambda item: item["label"])):
                angle = (2 * math.pi * index) / max(1, len(ring_nodes))
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions[node["id"]] = (x, y)
            continue
        radius = radii[ring]
        for index, node in enumerate(sorted(ring_nodes, key=lambda item: item["label"])):
            angle = (2 * math.pi * index) / max(1, len(ring_nodes))
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node["id"]] = (x, y)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7fafc"/>',
        '<text x="50" y="60" font-size="28" font-family="Arial" fill="#1a202c">Context graph parcial de Final Fantasy</text>',
    ]

    for edge in graph["edges"]:
        x1, y1 = positions[edge["subject"]]
        x2, y2 = positions[edge["object"]]
        svg_parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#cbd5e0" stroke-width="1.5" />'
        )

    for edge in graph["edges"][:80]:
        x1, y1 = positions[edge["subject"]]
        x2, y2 = positions[edge["object"]]
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        svg_parts.append(
            f'<text x="{mx:.1f}" y="{my:.1f}" font-size="11" font-family="Arial" fill="#4a5568">{edge["predicate"]}</text>'
        )

    for node in graph["nodes"]:
        x, y = positions[node["id"]]
        color = node_color(node["type"])
        svg_parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="26" fill="{color}" opacity="0.95" />')
        svg_parts.append(
            f'<text x="{x:.1f}" y="{y + 45:.1f}" text-anchor="middle" '
            'font-size="13" font-family="Arial" fill="#1a202c">'
            f'{node["label"][:28]}</text>'
        )

    svg_parts.append("</svg>")
    output_path.write_text("\n".join(svg_parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Construye el context graph y una visualización SVG")
    parser.add_argument(
        "--triplets",
        type=Path,
        default=TRIPLETS_DIR / "context_triplets.json",
        help="Tripletas con metadatos",
    )
    args = parser.parse_args()

    ensure_dirs()
    triples = read_json(args.triplets)
    baseline = read_json(TRIPLETS_DIR / "baseline_triplets.json")

    context_graph = build_graph(triples)
    baseline_graph = build_graph(baseline)

    write_json(GRAPHS_DIR / "context_graph.json", context_graph)
    write_json(GRAPHS_DIR / "baseline_graph.json", baseline_graph)

    subgraph = choose_subgraph(context_graph, max_nodes=60)
    render_svg(subgraph, FIGURES_DIR / "context_graph.svg")

    print(f"Nodos context graph: {len(context_graph['nodes'])}")
    print(f"Aristas context graph: {len(context_graph['edges'])}")
    print(f"Visualización guardada en {FIGURES_DIR / 'context_graph.svg'}")


if __name__ == "__main__":
    main()
