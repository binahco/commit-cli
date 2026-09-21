---
title: "Retrofit: marcador de secretos en llm-client"
labels: [retrofit]
---

## Antes

El CLI manda el diff tal cual al modelo. Si contiene secretos, se envían.

## Después

`llm-client` expone un filtro de redacción (D3.1) usable por cualquier
consumidor antes de construir el provider request.

## Motivo

commit-cli procesa diffs de código fuente, donde los secretos no deberían
enviarse a un LLM; es un riesgo transversal a todos los consumidores.

## Plan

- [ ] Añadir `redact_secrets()` en `packages/llm-client` (regex de API keys/credenciales)
- [ ] Aplicarlo por defecto en `LlmClient` para variables con tag sensible
- [ ] Migrar commit-cli a la nueva versión del core
- [ ] Actualizar `core-consumer.yml`
- [ ] Correr `eval-smoke`
- [ ] Actualizar README ("Recicla de")