import os

# Ścieżki do plików
KV_FILE = os.path.join("ui", "layout.kv")
BACKUP_FILE = KV_FILE + ".bak"

# Poprawny szablon z prawidłowymi wcięciami (4 spacje różnicy)
# {indent} to wcięcie bazowe (tam gdzie stoi TextInput)
NEW_WIDGET_TEMPLATE = """{indent}TextInput:
{indent}    text: root.text
{indent}    readonly: True
{indent}    background_color: 0, 0, 0, 0
{indent}    foreground_color: 1, 1, 1, 1
{indent}    cursor_color: 0, 0, 0, 0
{indent}    multiline: True
{indent}    size_hint_y: None
{indent}    height: self.minimum_height
{indent}    font_size: "16sp"
{indent}    padding: [10, 10]
{indent}    background_normal: ''
{indent}    background_active: ''
"""

def fix_indentation_bug():
    print("--- Rozpoczynam naprawę wcięć w ui/layout.kv ---")

    # 1. Sprawdź czy mamy kopię zapasową (powinna być po poprzednim kroku)
    if not os.path.exists(BACKUP_FILE):
        print(f"[BŁĄD] Nie znaleziono pliku kopii: {BACKUP_FILE}")
        print("Nie mogę przywrócić oryginału. Spróbuj cofnąć zmiany ręcznie.")
        return

    print(f"[INFO] Wczytuję oryginał z: {BACKUP_FILE}")
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    inside_label = False
    label_indent_level = 0

    for line in lines:
        # Szukamy momentu, gdzie zaczyna się MDLabel
        if "MDLabel:" in line:
            inside_label = True
            
            # Obliczamy wcięcie (ilość spacji przed MDLabel)
            indent_str = line.split("MDLabel")[0]
            label_indent_level = len(indent_str)
            
            # Wstawiamy nasz poprawny blok TextInput z zachowaniem wcięcia
            formatted_block = NEW_WIDGET_TEMPLATE.format(indent=indent_str)
            new_lines.append(formatted_block)
            continue

        # Jeśli jesteśmy wewnątrz starego bloku MDLabel, musimy pominąć jego właściwości
        if inside_label:
            # Sprawdzamy wcięcie bieżącej linii
            current_indent = len(line) - len(line.lstrip())
            
            # Jeśli linia jest pusta, po prostu ją dodajemy (chyba że to koniec bloku)
            if not line.strip():
                new_lines.append(line)
                continue

            # Jeśli wcięcie jest większe niż wcięcie MDLabel, to znaczy że to jego właściwość -> POMIJAMY
            if current_indent > label_indent_level:
                continue
            else:
                # Wcięcie wróciło do poziomu rodzica lub wyżej -> koniec bloku MDLabel
                inside_label = False
                new_lines.append(line)
        else:
            # Przepisujemy wszystkie inne linie bez zmian
            new_lines.append(line)

    # Zapisujemy naprawiony plik
    with open(KV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"[SUKCES] Plik {KV_FILE} został nadpisany poprawną wersją.")
    print("Teraz struktura wcięć powinna być prawidłowa.")

if __name__ == "__main__":
    fix_indentation_bug()