# Checklist de entrega

## Antes de subir el repo

- [ ] Comprobar que `secrets.toml` no aparece en `git status`
- [ ] Comprobar que `.gitignore` contiene `secrets.toml`
- [ ] Verificar que el proyecto arranca con:
  - [ ] `python3 src/ask.py --question "..."`
  - [ ] `python3 src/ask_llm.py --question "..."`
- [ ] Verificar que existe `figures/context_graph.svg`
- [ ] Verificar que existe `graphs/context_graph.json`
- [ ] Verificar que existe `triplets/context_triplets_merged.json`

## Archivos recomendados para entregar

- [ ] `README.md`
- [ ] `src/`
- [ ] `data/seed_urls.txt`
- [ ] `triplets/context_triplets_merged.json`
- [ ] `graphs/context_graph.json`
- [ ] `figures/context_graph.svg`
- [ ] `report/informe_final.md` o su versión exportada a PDF

## Lo que no debe subirse

- [ ] `secrets.toml`
- [ ] claves API en texto plano
- [ ] basura local de terminal o cachés innecesarias

## Verificación mínima de demo

- [ ] Pregunta temporal sobre PS5
- [ ] Pregunta sobre remakes
- [ ] Pregunta multi-hop sobre remake + desarrollador + juego original
