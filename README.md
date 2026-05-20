# Proyecto 8: Final Fantasy como Context Graph

Este proyecto implementa un sistema experto moderno sobre la saga **Final Fantasy** a partir de fuentes de **3DJuegos**. El flujo funciona sin API key y también incluye una vía LLM con OpenRouter:

1. `scraping.py` descarga páginas en Markdown usando `r.jina.ai`.
2. `obtain_triplets.py` extrae tripletas y metadatos con reglas específicas para 3DJuegos.
3. `obtain_triplets_llm.py` extrae tripletas con OpenRouter cuando hay API key válida.
4. `merge_triplets.py` combina extracción por reglas y extracción LLM.
5. `context_graph.py` construye un context graph y una versión baseline sin metadatos.
6. `ask.py` responde preguntas apoyándose en evidencia del grafo.
7. `ask_llm.py` usa el grafo como recuperación de evidencia y OpenRouter como motor de inferencia.
8. `compare_baseline.py` genera una comparación corta entre baseline y context graph.

## Estructura

```text
Proyecto 8/
├── data/
│   ├── raw_md/
│   └── seed_urls.txt
├── figures/
├── graphs/
├── report/
│   └── guion_pdf.md
├── secrets_template.toml
└── src/
    ├── ask.py
    ├── common.py
    ├── compare_baseline.py
    ├── context_graph.py
    ├── ask_llm.py
    ├── merge_triplets.py
    ├── obtain_triplets.py
    ├── obtain_triplets_llm.py
    └── scraping.py
```

## Cómo ejecutarlo

```bash
python3 src/scraping.py
python3 src/obtain_triplets.py
python3 src/obtain_triplets_llm.py --only final_fantasy_vii_remake.md final_fantasy_vii_rebirth.md final_fantasy_xvi.md
python3 src/merge_triplets.py
python3 src/context_graph.py --triplets triplets/context_triplets_merged.json
python3 src/ask.py --question "¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?"
python3 src/ask_llm.py --question "¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?"
python3 src/compare_baseline.py
```

## Cómo probarlo tú mismo

- Demo rápida: lanza directamente `ask.py` con las tres preguntas del proyecto.
- Demo alineada con el enunciado: lanza `ask_llm.py`, que usa OpenRouter en tiempo real sobre evidencia recuperada del grafo.
- Reconstrucción del grafo: ejecuta `obtain_triplets.py`, `merge_triplets.py` y `context_graph.py`.
- Extracción LLM: usa `obtain_triplets_llm.py` con `OPENROUTER_API_KEY` o `secrets.toml`.

Guía ampliada:

- [report/como_probarlo.md](/Users/jesusaragonmonzon/Documents/BigData%202025_2026/Modelo%20Inteligencia%20Artificial/Proyecto%208/report/como_probarlo.md)
- [report/requisitos_entrega.md](/Users/jesusaragonmonzon/Documents/BigData%202025_2026/Modelo%20Inteligencia%20Artificial/Proyecto%208/report/requisitos_entrega.md)

## Salidas esperadas

- `data/raw_md/*.md`: páginas scrapeadas.
- `triplets/context_triplets.json`: tripletas con procedencia, fecha y confianza.
- `triplets/llm_triplets.json`: tripletas extraídas con OpenRouter.
- `triplets/context_triplets_merged.json`: combinación de reglas + LLM.
- `triplets/baseline_triplets.json`: mismas tripletas sin metadatos.
- `graphs/context_graph.json`: nodos y aristas del context graph.
- `graphs/baseline_graph.json`: versión reducida.
- `figures/context_graph.svg`: visualización parcial del grafo.

## Nota sobre LLM

La práctica pide extracción con LLM. El proyecto ya incluye esa vía mediante OpenRouter. La credencial se puede pasar por `OPENROUTER_API_KEY` o guardando un `secrets.toml` local a partir de `secrets_template.toml`. La extracción por reglas se mantiene como baseline reproducible y como respaldo cuando la API no está disponible.
