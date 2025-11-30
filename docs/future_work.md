# Future enhancements

This document tracks incremental improvements that would strengthen DebugDruid without changing its current behavior.

## Reliability and observability
- Add structured logging (JSON) and optional log file rotation to make support diagnostics easier.
- Emit basic metrics (model choice, request durations, error counts) to a local CSV or Prometheus endpoint for lightweight monitoring.
- Capture model-discovery outcomes in a small cache file so startup can fall back to a previously working model when offline.

## User experience
- Add keyboard shortcuts to mirror the Grim-terface hotkeys inside the Kivy interface for faster navigation.
- Provide a condensed status bar in the main view (API key state, model, search toggle) so users don’t need to open the sidebar.
- Offer a first-run tour that explains model discovery, search toggles, and how file/image contexts are applied.

## Testing
- Extend the `send_message` integration coverage to include Google Search tool activation, image attachments, and HTML preview handling.
- Add a headless smoke test for the Kivy UI layout (e.g., using a mocked window provider) to catch missing IDs or binding errors early.

## Launcher and packaging
- Provide a `--venv` flag to create and reuse a project-local virtual environment before launching the app.
- Publish a simple executable bundle (PyInstaller or Briefcase) that wraps the launcher behavior for non-Python users.
