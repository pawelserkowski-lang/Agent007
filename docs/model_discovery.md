# Model discovery strategy

The agent queries `models.list` during startup and manual refresh to find the best available Gemini model for chat requests.

## Selection rules
1. Filter to entries that support `generateContent`.
2. Strip the `models/` prefix and collapse variants by family name (e.g., `gemini-1.5-pro-*`).
3. Within each family, prefer the `latest` suffix; otherwise select the highest numeric suffix.
4. Choose the first match from the priority list: `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-pro` (override via `MODEL_PRIORITY_FAMILIES` or `config.json`). Priority entries are trimmed and deduplicated before use, falling back to the defaults if the override is empty.
5. If no priority families exist, fall back to the alphabetically first remaining family name.

## Why
- Keeps discovery fast by caching the newest model per family instead of iterating the full list on every request.
- Surfaces the sorted discovered list (`app.available_models`) for diagnostics or future manual model selection.

## Related tests
The unit suite (`tests/test_agent_model_selection.py`) validates:
- Selecting the newest variant in each family.
- Respecting priority ordering with a graceful fallback.
- Caching the discovered list and configured API key during discovery.
