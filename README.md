# DebugDruid

A desktop-oriented Gemini assistant built with KivyMD. The app streamlines session management, file-aware prompts, and Google Search assisted requests while keeping a lightweight local SQLite history.

## Features
- Automatic model discovery that prefers the newest priority Gemini families.
- Sidebar tools for toggling search, theming, and quick diagnostics.
- Session history persisted locally with file and image context support.
- GitHub import card to fetch repository files straight into the chat context with path normalization and a 1 MB safety cap.

## Getting started
1. Install dependencies from `requirements.txt`.
2. Provide your `API_KEY` via environment variable or the in-app field.
   - Optional: override model priorities with `MODEL_PRIORITY_FAMILIES="gemini-1.5-pro,gemini-1.5-flash,gemini-pro"`.
3. Run the application with `python main.py` or use the convenience launcher:

   ```bash
   python launcher.py
   ```

   The launcher prepends the repository to `PYTHONPATH` (deduplicating the root while preserving other entries) and uses your current Python interpreter.
3. Run the application with `python main.py`.

## Tests
Execute the fast unit suite with:

```bash
python -m unittest discover -v
```

## Documentation
Additional design notes live in [`docs/model_discovery.md`](docs/model_discovery.md).
- Audit/playbook for kodowe "Tryb Architekta" (workflow, szablon odpowiedzi, zasady bezpieczeństwa): [`docs/architect_protocol.md`](docs/architect_protocol.md).
- Ideas for future enhancements are collected in [`docs/future_work.md`](docs/future_work.md).
- GitHub integration guide: [`docs/github_integration.md`](docs/github_integration.md).

### Grim-terface spellbook
- Quick-reference for the Grimoire hotkeys and recent patch highlights: [`docs/grim_interface.md`](docs/grim_interface.md).
- Architect-mode helper functions for templating plus language/framework/version detection (Python, JS/TS, C++, Go, PHP, Ruby, Rust + FastAPI/React/Gin/Laravel/Rails/Actix/Rocket) live in [`core/architect.py`](core/architect.py) and are documented in [`docs/architect_protocol.md`](docs/architect_protocol.md).

### Grim-terface spellbook
- Quick-reference for the Grimoire hotkeys and recent patch highlights: [`docs/grim_interface.md`](docs/grim_interface.md).
