import os
import re

# Tekst, którego szukamy, aby zlokalizować miejsce sprawdzania klucza
TARGET_LOG = "Brak klucza API"

def patch_file(filepath):
    print(f"--> Znaleziono cel w pliku: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Sprawdzenie czy patch już jest
    if any("os.environ.get" in line for line in lines):
        print("   [INFO] Ten plik już obsługuje zmienne środowiskowe.")
        return

    # Szukamy linii z logiem błędu
    warning_idx = -1
    for i, line in enumerate(lines):
        if TARGET_LOG in line:
            warning_idx = i
            break
    
    if warning_idx == -1:
        return

    # Szukamy zmiennej w warunku if powyżej logu
    var_name = None
    insert_idx = -1
    
    # Skanujemy 15 linii w górę
    for i in range(warning_idx, max(0, warning_idx-15), -1):
        line = lines[i].strip()
        # Szukamy: if not self.zmienna lub if self.zmienna is None
        # Regex łapie: "if not self.api_key" -> grupa 2 to "self.api_key"
        match = re.search(r"if\s+(not\s+)?([a-zA-Z0-9_.]+)", line)
        
        # Ignorujemy linię, jeśli to ta sama linia co log (rzadkie, ale możliwe)
        if match and TARGET_LOG not in line:
            full_var = match.group(2)
            # Czyścimy z ewentualnych dopisków typu " is None"
            var_name = full_var.split()[0]
            insert_idx = i
            break

    if not var_name:
        print(f"   [BLAD] Nie udało się znaleźć nazwy zmiennej w pliku {filepath}.")
        print("   Spróbuj poszukać ręcznie.")
        return

    print(f"   [INFO] Wykryto zmienną: '{var_name}'")
    
    # --- APLIKOWANIE ZMIAN ---
    
    # 1. Dodaj import os na początku pliku (jeśli brak)
    if "import os" not in "".join(lines[:50]):
        lines.insert(0, "import os\n")
        insert_idx += 1

    # 2. Pobierz wcięcie (indentację)
    indent = lines[insert_idx][:len(lines[insert_idx]) - len(lines[insert_idx].lstrip())]
    
    # 3. Przygotuj kod do wstawienia
    new_code = [
        f"{indent}# --- PATCH: Auto-load from ENV ---\n",
        f"{indent}if not {var_name}:\n",
        f"{indent}    {var_name} = os.environ.get('GOOGLE_API_KEY')\n",
        f"{indent}# -------------------------------\n"
    ]
    
    # Wstawiamy przed warunkiem if
    for line in reversed(new_code):
        lines.insert(insert_idx, line)

    # Zapisujemy plik
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"   [SUKCES] Plik {filepath} został naprawiony!")

# --- GŁÓWNA PĘTLA SZUKAJĄCA ---
print("Rozpoczynam przeszukiwanie wszystkich plików .py...")
found_any = False

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if TARGET_LOG in content:
                        patch_file(path)
                        found_any = True
            except Exception as e:
                print(f"Błąd odczytu {path}: {e}")

if not found_any:
    print("\n[FATAL] Nie znaleziono pliku z komunikatem 'Brak klucza API'.")
    print("Upewnij się, że jesteś w głównym folderze Agent007.")