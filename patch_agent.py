import os
import re

def patch_file(filepath):
    print(f"Analizuję plik: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 1. Sprawdź czy już nie jest naprawiony
    if any("os.environ.get" in line for line in lines):
        print("Wygląda na to, że plik już pobiera zmienne środowiskowe.")
        return

    # 2. Znajdź linię z ostrzeżeniem o braku klucza
    warning_idx = -1
    for i, line in enumerate(lines):
        if "Brak klucza API" in line:
            warning_idx = i
            break
    
    if warning_idx == -1:
        print("Nie znaleziono miejsca w kodzie, gdzie sprawdzany jest klucz.")
        return

    # 3. Szukamy instrukcji 'if' powyżej ostrzeżenia, aby znaleźć nazwę zmiennej
    var_name = None
    insert_idx = -1
    
    # Skanujemy 10 linii w górę od ostrzeżenia
    for i in range(warning_idx, max(0, warning_idx-10), -1):
        line_content = lines[i].strip()
        # Szukamy wzorca: if not self.api_key: lub if self.api_key is None:
        match = re.search(r"if\s+(not\s+)?([\w\.]+)", line_content)
        if match and "Logger" not in line_content: # Ignorujemy sam log
            # Jeśli znaleziono "if not zmienna", grupa 2 to nazwa zmiennej
            full_match = match.group(2)
            # Oczyszczamy z ewentualnych " is None"
            var_name = full_match.split()[0]
            insert_idx = i
            break

    if not var_name:
        print("Nie udało się automatycznie wykryć nazwy zmiennej.")
        return

    print(f"Wykryto zmienną klucza: '{var_name}'")
    
    # 4. Aplikujemy zmiany
    
    # Dodaj import os na początku, jeśli go nie ma
    if "import os" not in "".join(lines[:30]):
        lines.insert(0, "import os\n")
        insert_idx += 1 # Przesuwamy indeks wstawiania o 1 w dół

    # Pobieramy wcięcie z linii, przed którą wstawiamy
    indent = lines[insert_idx][:len(lines[insert_idx]) - len(lines[insert_idx].lstrip())]
    
    # Kod do wstawienia
    patch_code = [
        f"{indent}# --- AUTO-PATCH: Wczytywanie z ENV ---\n",
        f"{indent}if not {var_name}:\n",
        f"{indent}    {var_name} = os.environ.get('GOOGLE_API_KEY')\n",
        f"{indent}# -------------------------------------\n"
    ]
    
    # Wstawiamy kod PRZED oryginalnym sprawdzeniem
    for line in reversed(patch_code):
        lines.insert(insert_idx, line)

    # 5. Zapisz plik
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUKCES! Zaktualizowano plik main.py.")

# Szukamy pliku main.py w bieżącym folderze i podfolderach
found = False
for root, dirs, files in os.walk("."):
    if "main.py" in files:
        path = os.path.join(root, "main.py")
        # Sprawdzamy czy to ten właściwy plik (czy ma ten konkretny log)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                if "Brak klucza API" in f.read():
                    patch_file(path)
                    found = True
                    break
        except Exception as e:
            print(f"Błąd odczytu {path}: {e}")

if not found:
    print("Nie znaleziono odpowiedniego pliku main.py.")