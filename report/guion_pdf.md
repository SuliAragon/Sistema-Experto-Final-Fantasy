# Guion del PDF

## 1. Objetivo del sistema experto

- Dominio: saga Final Fantasy.
- Fuente principal: 3DJuegos.
- Propósito: responder preguntas sobre juegos, plataformas, fechas, remakes, desarrolladores y relaciones dentro de la saga usando evidencia estructurada.

## 2. Arquitectura del sistema

- Scraping: `src/scraping.py`
- Extracción de tripletas: `src/obtain_triplets.py`
- Construcción del context graph: `src/context_graph.py`
- Consulta del sistema: `src/ask.py`
- Comparación con baseline: `src/compare_baseline.py`

## 3. Sistema experto clásico frente a context graph

- Base de conocimiento: tripletas del grafo.
- Motor de inferencia: reglas de consulta + ensamblado de evidencia.
- Interfaz de usuario: script `ask.py`.
- Extensión a context graph: fuente, fecha de extracción, vigencia y confianza.

## 4. Preguntas propuestas

1. ¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?
2. ¿Qué entregas de Final Fantasy aparecen como remakes en nuestras fuentes?
3. ¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?

La tercera es multi-hop:

`juego -> desarrollado_por -> Square Enix`  
`juego -> es_remake_de -> juego original`

## 5. Comparación baseline vs context graph

- El baseline conserva la estructura `sujeto-predicado-objeto`.
- El context graph añade procedencia, fecha y confianza.
- Gracias a los metadatos se puede:
  - citar la URL de origen;
  - diferenciar hechos por fecha;
  - filtrar preguntas temporales como “después de 2020”;
  - rechazar respuestas si no hay contexto suficiente.

## 6. Conclusión personal

Explica cuándo usarías:

- `context graph`: cuando importan relaciones, trazabilidad, vigencia y citación.
- `RAG vectorial`: cuando necesitas recuperar texto relevante sin demasiada estructura relacional.
