import os
import sys
import subprocess

# 1. Pobieramy klucz bezpośrednio z systemu Windows
api_key = os.environ.get("GOOGLE_API_KEY")

# Sprawdzamy, czy klucz istnieje
if not api_key:
    print("---------------------------------------------------------")
    print("BLAD: Nie znaleziono zmiennej srodowiskowej GOOGLE_API_KEY")
    print("---------------------------------------------------------")
    print("Musisz dodac klucz w ustawieniach systemu Windows:")
    print("1. Wpisz w Start: 'Edytuj zmienne srodowiskowe dla konta'")
    print("2. Kliknij 'Nowa' w sekcji zmiennych uzytkownika")
    print("3. Nazwa: GOOGLE_API_KEY")
    print("4. Wartosc: Twoj klucz (AIza...)")
    print("---------------------------------------------------------")
    input("Nacisnij ENTER, aby zamknac...")
    sys.exit(1)

print("Klucz API wykryty w systemie.")

# 2. Ustawiamy folder roboczy na folder skryptu
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)
sys.path.append(current_dir)

print(f"Uruchamianie Agent007 z: {current_dir}")

# 3. Uruchamiamy launcher
try:
    # Próbujemy zaimportować i uruchomić launcher w tym samym procesie
    # (To szybsze i pozwala widzieć błędy w tej samej konsoli)
    import launcher
except ImportError:
    # Fallback: uruchomienie jako osobny proces
    subprocess.run([sys.executable, "launcher.py"])
except Exception as e:
    print(f"Wystapil blad krytyczny: {e}")
    input("Nacisnij ENTER, aby zamknac...")