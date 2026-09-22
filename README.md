# commit-cli

> **Semana:** 2 · **Core:** `llm-dev-core` 0.1.0

## Problema

Escribir mensajes de commit consistentes es una fricción repetitiva. Este CLI
toma el `git diff` del árbol de trabajo y **propone** un mensaje en formato
Conventional Commits. Solo propone: nunca hace `git commit`.

## Demo

```bash
cd tu-proyecto
git add -N .            # incluir archivos nuevos (aún no staged) en el diff
commit-cli --staged     # o sin --staged para el árbol de trabajo
```

Un span JSONL se emite a stderr por cada llamada (2.ª telemetría de la semana).

## Arquitectura

```
┌─────────────────────┐   git diff    ┌──────────────────────────────┐
│ tu repo (cwd)       │ ────────────▶ │ commit-cli (este proyecto)   │
└─────────────────────┘               │  · render del prompt         │
                                      │  · LlmClient (llm-client)    │
                                      │  · span JSONL → stderr       │
                                      └──────────────┬───────────────┘
                                                     │ provider
                                                     ▼
                                    ┌──────────────────────────────────┐
                                    │ opencode run (tu sesión, free)   │
                                    │   · o ReplayProvider (cassettes) │
                                    └──────────────────────────────────┘
```

## Recicla de

| Módulo del core | Qué aporta |
|---|---|
| `llm-client` | Llamadas LLM con retry+backoff, span de 20 campos, cache, costo y record/replay sin API key |

## Limitaciones

- No hacemos `git commit`: propone, revisas tú e introduces el commit.
- El diff sale del repo tal cual: si el diff contiene secretos, tú eres responsable de no commitearlos ni pegarlos.
- `opencode run` spawnea un servidor por llamada: latencia de inicio (~segundos) incluida en el span.
- `tokens_input/output` son best-effort (agente, no completion puro); `cost_usd` = 0 para modelos free.

## Roadmap

- [x] Evaluación `eval-smoke` con el dataset de `evals/` (sem. 5, test-kit; ampliada a 3 casos congelados en el retrofit #0 de la sem. 6)
- [ ] Soporte de `--amend`-aware (pegar el mensaje anterior como contexto)
- [ ] Aviso de secretos sobre el diff antes de enviarlo
- [ ] Retrofit al core si `opencode run` pediría un transport contenido (ver `retrofit-issue.md`)