# Cómo probar el proyecto

## Opción rápida

Si ya están generados los datos, se puede probar directamente el sistema de preguntas:

```bash
python3 src/ask.py --question "¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?"
python3 src/ask.py --question "¿Qué entregas de Final Fantasy aparecen como remakes?"
python3 src/ask.py --question "¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?"
```

## Opción alineada con el enunciado

Esta es la más fiel a la práctica, porque usa el grafo como recuperación y el LLM como motor de inferencia:

```bash
python3 src/ask_llm.py --question "¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?"
python3 src/ask_llm.py --question "¿Qué entregas de Final Fantasy aparecen como remakes?"
python3 src/ask_llm.py --question "¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?"
```

Si quieres inspeccionar además la evidencia que el script recupera del grafo antes de llamar al modelo:

```bash
python3 src/ask_llm.py --question "¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?" --show-evidence
```

## Opción completa

Reconstruir el pipeline desde cero:

```bash
python3 src/obtain_triplets.py
python3 src/merge_triplets.py
python3 src/context_graph.py --triplets triplets/context_triplets_merged.json
python3 src/compare_baseline.py
```

## Opción con LLM

Si se quiere volver a extraer tripletas LLM:

1. Crear `secrets.toml` a partir de `secrets_template.toml`
2. O exportar `OPENROUTER_API_KEY`
3. Ejecutar:

```bash
python3 src/obtain_triplets_llm.py --only final_fantasy_vii_remake.md final_fantasy_vii_rebirth.md final_fantasy_xvi.md
python3 src/merge_triplets.py
python3 src/context_graph.py --triplets triplets/context_triplets_merged.json
```

Para consultar con LLM en tiempo real también hace falta:

- `OPENROUTER_API_KEY`, o
- `secrets.toml` a partir de `secrets_template.toml`

## Resultado esperado

- Grafo JSON en `graphs/`
- Visualización SVG en `figures/context_graph.svg`
- Respuestas citadas desde `ask.py`
