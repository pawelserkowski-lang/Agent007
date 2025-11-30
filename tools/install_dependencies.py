import sys
import subprocess
import os

def install_packages():
    print("--- AGENT 007: DEPENDENCY INSTALLER ---")
    
    # Lista wymagań zgodna z Twoim zamówieniem
    requirements = [
        "kivy>=2.3.0",
        "kivymd>=1.2.0",
        "google-generativeai>=0.4.0",
        "python-dotenv",
        "Pillow",
        "docutils"
    ]

    # Krok 1: Upgrade pip (częsty powód błędów instalacji Kivy)
    print("[SYSTEM] Aktualizacja pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        print(f"[OSTRZEŻENIE] Nie udało się zaktualizować pip: {e}")

    # Krok 2: Instalacja pakietów
    for package in requirements:
        print(f"[INSTALACJA] Pobieranie komponentu: {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[OK] {package} gotowe.")
        except subprocess.CalledProcessError:
            print(f"[BŁĄD] Krytyczny błąd instalacji dla: {package}")
            print("Spróbuj uruchomić ten skrypt jako Administrator.")
            return

    print("\n" + "="*40)
    print("[SUKCES] Środowisko jest gotowe.")
    print("Uruchom teraz: python main.py")
    print("="*40)
    
    # Pauza, żeby okno nie zniknęło od razu przy uruchomieniu dwuklikiem
    if os.name == 'nt':
        os.system("pause")

if __name__ == "__main__":
    install_packages()