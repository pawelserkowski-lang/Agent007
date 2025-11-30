import sys
from pathlib import Path

# Dodajemy bieżący katalog do sys.path, aby Python widział moduł 'src'
sys.path.append(str(Path(__file__).parent))

from src.ui.app import AgentApp

if __name__ == "__main__":
    AgentApp().run()
