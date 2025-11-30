import sys
import subprocess
import os

def install_requirements():
    print(f"--- AGENT 007: DIAGNOSTYKA I INSTALACJA ---")
    print(f"[SYSTEM] Wykryty interpreter: {sys.executable}")
    
    requirements = [
        "kivy>=2.3.0",
        "kivymd>=1.2.0",
        "google-generativeai>=0.4.0",
        "python-dotenv",
        "Pillow",
        "docutils"
    ]

    print("\n[SYSTEM] Rozpoczynam instalację pakietów...")
    
    # 1. Upgrade pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except:
        print("[INFO] Pip jest prawdopodobnie aktualny lub pominięto upgrade.")

    # 2. Instalacja zależności
    failed = []
    for package in requirements:
        print(f"\n>>> Instaluję: {package}")
        try:
            # Używamy flagi --user, aby ominąć problemy z uprawnieniami
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
        except subprocess.CalledProcessError:
            print(f"[BŁĄD] Nie udało się zainstalować {package}")
            failed.append(package)

    print("\n" + "="*40)
    if failed:
        print(f"[OSTRZEŻENIE] Problemy z pakietami: {failed}")
    else:
        print("[SUKCES] Wszystkie biblioteki zainstalowane poprawnie.")
        print("Możesz uruchomić system.")
    print("="*40)

if __name__ == "__main__":
    install_requirements()
    if os.name == 'nt':
        input("Naciśnij Enter, aby zamknąć...")