# Requisitos de entrega

Fuente oficial del enunciado:

- <https://davidlms.github.io/material-modelos-ia/docs/proyectos/proyecto8/>

## Qué pide el proyecto

1. Elegir un tema o dominio.
2. Escoger una fuente estructurable y actualizada.
3. Hacer scraping de la fuente.
4. Extraer tripletas con metadatos:
   - `sujeto`, `predicado`, `objeto`
   - `fuente`
   - `fecha_extraccion`
   - `valido_desde`
   - `valido_hasta` cuando aplique
   - `confianza`
5. Construir el context graph.
6. Hacer al menos 3 preguntas distintas.
7. Incluir al menos 1 pregunta multi-hop.
8. Visualizar una parte representativa del grafo, entre 50 y 100 nodos como máximo.
9. Comparar brevemente el sistema con una versión sin metadatos.

## Qué debe incluir el PDF

- Objetivos concretos del sistema experto y justificación del dominio elegido.
- Diagrama o descripción de componentes: scraping, extracción, grafo y consulta.
- Scripts utilizados, comentados.
- Imagen con la visualización parcial del grafo.
- Las tres preguntas con sus respuestas y las fuentes citadas.
- Opinión razonada sobre cuándo usar context graph y cuándo basta un RAG vectorial.

## ¿Exigen que sea ejecutable?

El enunciado no dice literalmente que haya que entregar una aplicación empaquetada o una interfaz gráfica. Lo que sí deja implícito es que el trabajo debe poder demostrarse con scripts reales:

- scraping;
- extracción de tripletas;
- construcción del grafo;
- consultas;
- visualización;
- respuestas con citas.

Conclusión práctica:

- No necesitas una app bonita.
- Sí conviene mucho que el proyecto sea reproducible y ejecutable por scripts.
- Para ir seguro, la entrega debería incluir instrucciones claras de ejecución y los ficheros ya generados.

## Recomendación para esta entrega

Entregar:

- código fuente;
- datos generados más importantes;
- visualización del grafo;
- PDF final;
- instrucciones de ejecución mínimas en `README.md`.
