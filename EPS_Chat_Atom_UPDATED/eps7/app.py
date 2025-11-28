
from __future__ import annotations
from .model_manager.manager import get_models, group_by_provider

def main() -> None:
    models = get_models(force_refresh=True)
    grouped = group_by_provider(models)
    for pid, items in grouped.items():
        print(f"=== Provider: {pid} ({len(items)} models) ===")
        for m in items:
            caps = ", ".join(m.capabilities) if m.capabilities else "-"
            print(f" - {m.model_id} :: {m.display_name} [{caps}]")

if __name__ == "__main__":
    main()
