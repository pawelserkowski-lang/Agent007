import os

def fix_ui_app():
    file_path = os.path.join("ui", "app.py")
    
    if not os.path.exists(file_path):
        print(f"BŁĄD: Nie znaleziono pliku {file_path}")
        return

    print(f"Otwieram {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    fixed_count = 0
    
    # Sprawdzamy, czy import Clock już istnieje, żeby nie dublować
    has_clock_import = any("from kivy.clock import Clock" in line for line in lines)

    if not has_clock_import:
        # Dodajemy import na samym początku (po innych importach)
        lines.insert(0, "from kivy.clock import Clock\n")

    for line in lines:
        # Szukamy dokładnie tej linii, która powoduje błąd w logach
        if "self.api_key = key_source" in line and "Clock" not in line:
            print(f"Znaleziono błąd w linii: {line.strip()}")
            
            # Pobieramy wcięcie (spacje z przodu), żeby nie zepsuć kodu
            indent = line[:line.find("self.api_key")]
            
            # Zamieniamy niebezpieczne przypisanie na bezpieczne (przez Clock)
            # Używamy setattr, żeby ominąć problem z przypisaniem w lambdzie
            safe_line = f"{indent}Clock.schedule_once(lambda dt: setattr(self, 'api_key', key_source))\n"
            
            new_lines.append(safe_line)
            fixed_count += 1
            print("-> Zamieniono na wersję bezpieczną dla wątków.")
        else:
            new_lines.append(line)

    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"SUKCES! Naprawiono {fixed_count} miejsc w kodzie.")
    else:
        print("Nie znaleziono linii do naprawy. Być może plik jest już naprawiony?")

if __name__ == "__main__":
    fix_ui_app()