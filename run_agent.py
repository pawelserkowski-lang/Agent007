#!/usr/bin/env python
"""
run_agent.py

Jedyny entrypoint dla Agent007 na Windows:

- ustawia katalog roboczy,
- ustawia zmienne środowiskowe dla agenta,
- sprawdza i w razie potrzeby *automatycznie* instaluje zależności Pythona
  (pip, requirements.txt),
- sprawdza, czy jest zainstalowana Ollama:
    * szuka w PATH i typowych katalogach,
    * jeśli nie ma, próbuje cichej instalacji przez `winget install Ollama.Ollama --silent`,
- sprawdza/pobiera model LLM (domyślnie `llama3`),
- uruchamia main.py.
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- konfiguracja bazowa ---

ROOT_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "llama3")
DEFAULT_DB_PATH = os.getenv("DB_PATH", "history.db")
DEFAULT_HISTORY_LIMIT = os.getenv("HISTORY_LIMIT", "50")
DEFAULT_SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful local AI assistant that replies in Polish.",
)

# globalna komenda do uruchamiania Ollamy (np. ["ollama"] albo ["C:\\...\\ollama.exe"])
OLLAMA_CMD = None  # type: ignore[assignment]


def setup_logging() -> None:
    """Konfiguracja loggera tak, żeby zawsze użyć naszych ustawień."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


# --- zależności Pythona ---

REQUIRED_MODULES = {
    "kivy": "kivy[base]==2.3.1",
    "kivymd": "kivymd==1.2.0",
    "dotenv": "python-dotenv>=1.0.0",
    "ollama": "ollama>=0.1.0",
}


def check_python_dependencies():
    """Sprawdza, czy wymagane moduły da się zaimportować."""
    missing: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(module_name)

    if missing:
        logging.warning(
            "Brakujące moduły Pythona: %s",
            ", ".join(missing),
        )
    else:
        logging.info("Wszystkie wymagane moduły Pythona są dostępne.")

    return missing


def ensure_python_dependencies() -> bool:
    """
    Upewnia się, że moduły z REQUIRED_MODULES są zainstalowane.

    Jeśli czegoś brakuje:
    - robi upgrade pip/setuptools/virtualenv,
    - instaluje paczki z requirements.txt.
    """
    missing_before = check_python_dependencies()
    if not missing_before:
        return True

    logging.info(
        "Próbuję automatycznie zainstalować brakujące paczki przez pip (w trybie dość cichym)..."
    )

    # upgrade podstawowych narzędzi
    try:
        subprocess.run(
            [PYTHON, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "virtualenv"],
            check=False,
        )
    except Exception as e:
        logging.warning("Nie udało się zaktualizować pip/setuptools/virtualenv: %s", e)

    # instalacja z requirements.txt
    req_path = ROOT_DIR / "requirements.txt"
    if not req_path.is_file():
        logging.error("Brak pliku requirements.txt w katalogu projektu: %s", req_path)
        return False

    try:
        result = subprocess.run(
            [PYTHON, "-m", "pip", "install", "-r", str(req_path)],
            check=False,
        )
        if result.returncode != 0:
            logging.error(
                "pip install -r requirements.txt zakończyło się kodem %s",
                result.returncode,
            )
    except Exception as e:
        logging.error("Błąd podczas instalacji zależności z requirements.txt: %s", e)
        return False

    # sprawdź ponownie
    missing_after = check_python_dependencies()
    if missing_after:
        logging.error(
            "Po automatycznej instalacji nadal brakuje modułów: %s. "
            "Spróbuj ręcznie:\n  pip install -r requirements.txt",
            ", ".join(missing_after),
        )
        return False

    return True


# --- Ollama: wykrywanie + instalacja + modele ---

def get_ollama_cmd():
    """Zwraca komendę, której używamy do wywoływania Ollamy."""
    global OLLAMA_CMD
    if OLLAMA_CMD is not None:
        return OLLAMA_CMD
    return ["ollama"]


def install_ollama_via_winget() -> bool:
    """
    Próbuje cicho zainstalować Ollamę przez winget:

        winget install --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements
    """
    if os.name != "nt":
        return False

    winget_path = shutil.which("winget")
    if not winget_path:
        logging.warning(
            "Nie znaleziono 'winget' w PATH – nie mogę automatycznie zainstalować Ollamy.\n"
            "Na Windows 10+ możesz ręcznie uruchomić:\n"
            "  winget install --id Ollama.Ollama"
        )
        return False

    logging.info("Próbuję zainstalować Ollamę przez winget (tryb silent)...")
    cmd = [
        winget_path,
        "install",
        "--id",
        "Ollama.Ollama",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
    ]
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            logging.error("winget install Ollama.Ollama zakończyło się kodem %s", result.returncode)
            return False
    except Exception as e:
        logging.error("Błąd podczas wywołania winget install Ollama.Ollama: %s", e)
        return False

    logging.info("Zakończono instalację Ollamy przez winget (sprawdzam binarkę)...")
    return True


def ensure_ollama_available() -> bool:
    """
    Sprawdza, czy Ollama jest dostępna:
    - najpierw przez PATH,
    - potem przez typowe ścieżki Windows,
    - jeśli nadal nie ma i jest Windows, próbuje cichej instalacji przez winget,
      a potem ponownie ją odnaleźć.

    Ustawia globalne OLLAMA_CMD.
    """
    global OLLAMA_CMD

    # 1) PATH
    path_in_path = shutil.which("ollama")
    if path_in_path:
        OLLAMA_CMD = [path_in_path]
        try:
            result = subprocess.run(
                OLLAMA_CMD + ["--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logging.info("Wykryto Ollama: %s", result.stdout.strip())
        except Exception as e:
            logging.error("Błąd przy sprawdzaniu wersji Ollama: %s", e)
            return False
        return True

    # 2) typowe lokalizacje Windows
    if os.name == "nt":
        candidates: list[Path] = []

        localapp = os.getenv("LOCALAPPDATA")
        if localapp:
            candidates.append(Path(localapp) / "Programs" / "Ollama" / "ollama.exe")

        program_files = os.getenv("ProgramFiles", r"C:\Program Files")
        candidates.append(Path(program_files) / "Ollama" / "ollama.exe")
        candidates.append(Path(program_files) / "Ollama" / "bin" / "ollama.exe")

        for exe in candidates:
            if exe.is_file():
                OLLAMA_CMD = [str(exe)]
                logging.warning(
                    "Znalazłem ollama.exe pod %s, ale nie ma jej w PATH. "
                    "Użyję tej ścieżki lokalnie w run_agent.py.",
                    exe,
                )
                try:
                    result = subprocess.run(
                        OLLAMA_CMD + ["--version"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    logging.info("Wykryto Ollama: %s", result.stdout.strip())
                except Exception as e:
                    logging.error(
                        "Błąd przy sprawdzaniu wersji Ollama (z lokalnej ścieżki): %s",
                        e,
                    )
                    return False
                return True

        # 3) spróbuj cichej instalacji przez winget
        if install_ollama_via_winget():
            # po instalacji spróbuj jeszcze raz PATH + typowe katalogi
            logging.info("Ponownie szukam Ollamy po instalacji przez winget...")
            return ensure_ollama_available()

    logging.error(
        "Nie znaleziono komendy 'ollama' ani w PATH, ani w typowych lokalizacjach.\n"
        "Zainstaluj Ollama ręcznie (np. z https://ollama.com/download lub przez winget):\n"
        "  winget install --id Ollama.Ollama"
    )
    return False


def ensure_model_pulled(model_name: str) -> bool:
    """
    Sprawdza, czy model jest dostępny w Ollamie,
    a jeśli nie – próbuje wykonać `<ollama> pull <model_name>`.
    """
    cmd = get_ollama_cmd()

    try:
        result = subprocess.run(
            cmd + ["list"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as e:
        logging.error("Nie udało się pobrać listy modeli z Ollamy: %s", e)
        return False

    if model_name in result.stdout:
        logging.info("Model '%s' jest już dostępny w Ollama.", model_name)
        return True

    logging.info(
        "Model '%s' nie jest dostępny – próbuję: %s pull %s",
        model_name,
        cmd[0],
        model_name,
    )
    try:
        pull_proc = subprocess.run(
            cmd + ["pull", model_name],
            text=True,
        )
        if pull_proc.returncode == 0:
            logging.info("Pomyślnie pobrano model '%s'.", model_name)
            return True

        logging.error(
            "%s pull %s zakończyło się kodem %s.",
            cmd[0],
            model_name,
            pull_proc.returncode,
        )
        return False
    except Exception as e:
        logging.error("Błąd podczas `%s pull %s`: %s", cmd[0], model_name, e)
        return False


# --- uruchamianie main.py ---

def run_main() -> int:
    """Uruchamia main.py w katalogu projektu i loguje wynik."""
    cmd = [PYTHON, "main.py"]
    logging.info("Uruchamiam: %s", " ".join(cmd))

    # Nie przechwytujemy wyjścia – Kivy będzie logować prosto do konsoli
    proc = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
    )

    logging.info("main.py zakończył się kodem %s", proc.returncode)
    return proc.returncode


def main() -> int:
    setup_logging()
    logging.info("=== Starting Agent007 runner ===")

    # katalog roboczy = folder tego skryptu
    os.chdir(ROOT_DIR)
    logging.debug("Working directory set to %s", ROOT_DIR)

    # zmienne środowiskowe dla agenta
    os.environ["MODEL_NAME"] = DEFAULT_MODEL_NAME
    os.environ["DB_PATH"] = DEFAULT_DB_PATH
    os.environ["HISTORY_LIMIT"] = str(DEFAULT_HISTORY_LIMIT)
    os.environ["SYSTEM_PROMPT"] = DEFAULT_SYSTEM_PROMPT

    logging.debug(
        "Env: MODEL_NAME=%s, DB_PATH=%s, HISTORY_LIMIT=%s, SYSTEM_PROMPT=%s",
        os.environ["MODEL_NAME"],
        os.environ["DB_PATH"],
        os.environ["HISTORY_LIMIT"],
        os.environ["SYSTEM_PROMPT"],
    )

    # 1) zależności Pythona
    if not ensure_python_dependencies():
        logging.error("Nie udało się przygotować środowiska Pythona – przerywam.")
        logging.info("=== Agent007 runner finished (failure) ===")
        return 1

    # 2) Ollama + model
    if not ensure_ollama_available():
        logging.error("Ollama niedostępna – przerywam.")
        logging.info("=== Agent007 runner finished (failure) ===")
        return 1

    if not ensure_model_pulled(DEFAULT_MODEL_NAME):
        logging.error(
            "Model '%s' niedostępny i nie udało się go pobrać.\n"
            "Spróbuj ręcznie w PowerShell:\n"
            "  %s pull %s",
            DEFAULT_MODEL_NAME,
            get_ollama_cmd()[0],
            DEFAULT_MODEL_NAME,
        )
        logging.info("=== Agent007 runner finished (failure) ===")
        return 1

    # 3) main.py
    code = run_main()
    logging.info("=== Agent007 runner finished ===")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
