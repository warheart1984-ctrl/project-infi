## Summary

AAIS **v1.24.0 — Release 28** adds six **Story Forge expansion** subsystems, **Coherence Layer v1.23**, a **frontier model provider catalog** (twelve adapters including NVIDIA Nemotron 3), optional **chat latency caches**, and **genome boot fixes** for `aais start` / `genome-gate`.

## What's new

### Release 28 — Story Forge expansion fabric

- Six governed organs: Story Forge Launcher, Movie Renderer Lane, Text-Game-to-Video, Game Front Door, Text-to-3D World Lane, World Pack Lane
- Status APIs under `GET /legacy_api/api/jarvis/<organ>/status`
- Coherence Layer v1.23 with `story_forge_expansion_layer` and `story_forge_expansion_bundle_aligned`
- **169** subsystem genomes at MVP batch (163 prior + 6 new)

### Frontier model providers

Twelve OpenAI-compatible adapters register in the provider picker. Each stays **off** until its key is set in `.env`:

OpenAI, Google Gemini, Mistral, DeepSeek, xAI (Grok), Groq, Together, Fireworks, Perplexity, **NVIDIA Nemotron 3**, Azure OpenAI, Moonshot, AI21 — plus Claude, OpenRouter, and local presets.

### Runtime

- Optional caches: `AAIS_COHERENCE_FABRIC_CACHE_SEC`, `AAIS_GOVERNED_PIPELINE_CACHE_SEC`, `AAIS_SLINGSHOT_CACHE_SEC`
- Genome lineage symmetry fixes for launcher boot

## Upgrade

1. Pull tag `v1.24.0` (or `main` at this release).
2. `cp .env.example .env` — set only the provider keys you use.
3. `python -m aais prepare --data-dir ./.runtime/aais-data`
4. Restart AAIS after changing keys.

No breaking API changes for existing chat sessions.

## Installing API keys

1. `cp .env.example .env`
2. Set keys for providers you use (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `NVIDIA_API_KEY` for Nemotron 3 Nano)
3. Restart AAIS and check `GET /legacy_api/api/jarvis/providers`
4. Set session `preferred_provider` to the provider id

Full table: [README — Installing API keys](../../README.md#installing-api-keys-frontier-models) · [FRONTIER_MODEL_ADAPTERS.md](../providers/FRONTIER_MODEL_ADAPTERS.md)

## Verification

```bash
make alt28-gate alt28-1-gate alt28-2-gate alt28-governed-gate
python tools/governance/_alt28_coherence_v123.py
curl -fsS http://127.0.0.1:8000/health
```

**Changelog:** [CHANGELOG.md §1.24.0](../../CHANGELOG.md) · **Release doc:** [v1.24.0-release28-storyforge-expansion-fabric.md](./v1.24.0-release28-storyforge-expansion-fabric.md)
