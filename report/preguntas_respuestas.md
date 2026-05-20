# Preguntas y respuestas del sistema

## 1. ¿Qué juegos de Final Fantasy salieron en PS5 después de 2020?

Respuesta actual del sistema:

- Final Fantasy XVI -> lanzamiento: 22 de junio de 2023.  
  Fuente: `https://www.3djuegos.com/universo/0f0f0f0/11/final-fantasy/`
- Final Fantasy XVI -> lanzamiento: 17 de septiembre de 2024.  
  Fuente: `https://www.3djuegos.com/universo/0f0f0f0/11/final-fantasy/`
- Final Fantasy VII: Rebirth -> lanzamiento: 29 de febrero de 2024.  
  Fuente: `https://www.3djuegos.com/juegos/final-fantasy-vii-rebirth/`
- Final Fantasy XVI -> lanzamiento: 17 de septiembre de 2024.  
  Fuente: `https://www.3djuegos.com/juegos/final-fantasy-xvi/`
- Final Fantasy XVI -> lanzamiento: 8 de junio de 2025.  
  Fuente: `https://www.3djuegos.com/universo/0f0f0f0/11/final-fantasy/`

## 2. ¿Qué entregas de Final Fantasy aparecen como remakes?

Respuesta actual del sistema:

- Final Fantasy VII Remake es remake de Final Fantasy VII.  
  Fuente: `http://www.3djuegos.com/juegos/final-fantasy-vii-remake/`

## 3. ¿Qué remake de Final Fantasy desarrollado por Square Enix aparece en nuestras fuentes y de qué juego original proviene?

Esta es la pregunta multi-hop del proyecto.

Ruta en el grafo:

`Final Fantasy VII Remake -> developed_by -> Square Enix`  
`Final Fantasy VII Remake -> is_remake_of -> Final Fantasy VII`

Respuesta actual del sistema:

- Final Fantasy VII Remake -> original: Final Fantasy VII.  
  Fuente: `http://www.3djuegos.com/juegos/final-fantasy-vii-remake/`

## Nota metodológica

Esta versión del pipeline ya combina dos capas:

- extracción por reglas sobre el Markdown de 3DJuegos;
- extracción LLM con OpenRouter usando `openai/gpt-4.1-mini` sobre varias fichas clave.

En la ejecución actual se han añadido `39` tripletas LLM y el grafo híbrido resultante alcanza `653` aristas. En el PDF conviene explicar que esta combinación mejora la calidad semántica de relaciones como `is_remake_of`, `developed_by` o `published_by`, mientras que la extracción por reglas sigue siendo útil como baseline reproducible.
