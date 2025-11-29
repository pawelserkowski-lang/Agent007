# DebugDruid

A desktop-oriented Gemini assistant built with KivyMD. The app streamlines session management, file-aware prompts, and Google Search assisted requests while keeping a lightweight local SQLite history.

## Features
- Automatic model discovery that prefers the newest priority Gemini families.
- Sidebar tools for toggling search, theming, and quick diagnostics.
- Session history persisted locally with file and image context support.

## Getting started
1. Install dependencies from `requirements.txt`.
2. Provide your `API_KEY` via environment variable or the in-app field.
   - Optional: override model priorities with `MODEL_PRIORITY_FAMILIES="gemini-1.5-pro,gemini-1.5-flash,gemini-pro"`.
3. Run the application with `python main.py`.

## Tests
Execute the fast unit suite with:

```bash
python -m unittest discover -v
```

## Documentation
Additional design notes live in [`docs/model_discovery.md`](docs/model_discovery.md).

### Grim-terface spellbook
- Quick-reference for the Grimoire hotkeys and recent patch highlights: [`docs/grim_interface.md`](docs/grim_interface.md).
