import os
import re
import shutil

# Szukamy w katalogu ui
SEARCH_DIR = "ui"

# Definicja zamiennika (TextInput zamiast MDLabel)
# Używamy formatu KV string, który jest najczęstszy w KivyMD
NEW_WIDGET_KV = """
    TextInput:
        text: root.text
        readonly: True
        background_color: 0, 0, 0, 0
        foreground_color: 1, 1, 1, 1
        cursor_color: 0, 0, 0, 0
        multiline: True
        size_hint_y: None
        height: self.minimum_height
        font_size: "16sp"
        padding: [10, 10]
        # Poniższe opcje usuwają obramowanie w niektórych motywach
        background_normal: ''
        background_active: ''
"""

def find_and_fix_ui():
    print(f"--- Przeszukiwanie katalogu {SEARCH_DIR} ---")
    
    if not os.path.exists(SEARCH_DIR):
        print(f"Błąd: Katalog {SEARCH_DIR} nie istnieje!")
        return

    target_file = None
    
    # 1. Przeszukaj pliki w poszukiwaniu definicji dymku
    for root, dirs, files in os.walk(SEARCH_DIR):
        for file in files:
            if file.endswith(".py") or file.endswith(".kv"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Szukamy charakterystycznych cech dymku czatu:
                # Klasa dziedzicząca po MDCard/BoxLayout i zawierająca MDLabel z root.text
                if "MDLabel" in content and "root.text" in content and ("MDCard" in content or "ChatBubble" in content):
                    print(f"[ZNALEZIONO] Potencjalny plik UI: {filepath}")
                    target_file = filepath
                    break
        if target_file:
            break

    if not target_file:
        print("[BŁĄD] Nie udało się automatycznie znaleźć pliku z definicją dymku czatu.")
        print("Spróbuj ręcznie znaleźć plik w folderze 'ui', który zawiera 'MDLabel' i 'root.text'.")
        return

    # 2. Wykonaj kopię zapasową
    shutil.copy(target_file, target_file + ".bak")
    print(f"[BACKUP] Utworzono {target_file}.bak")

    # 3. Dokonaj zamiany w znalezionym pliku
    with open(target_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    inside_label = False
    indentation = ""
    
    # Dodajemy import TextInput na początku, jeśli to plik .py
    if target_file.endswith(".py"):
        new_lines.append("from kivy.uix.textinput import TextInput\n")

    for line in lines:
        # Wykrywanie początku MDLabel wewnątrz definicji dymku
        if "MDLabel:" in line:
            inside_label = True
            # Pobierz wcięcie (ilość spacji przed MDLabel)
            indentation = line.split("MDLabel")[0]
            
            # Wstawiamy nasz TextInput z odpowiednim wcięciem
            replacement = NEW_WIDGET_KV.strip().split('\n')
            for rep_line in replacement:
                new_lines.append(indentation + rep_line.strip() + "\n")
            continue

        # Jeśli jesteśmy wewnątrz definicji MDLabel, pomijamy stare właściwości
        if inside_label:
            # Sprawdzamy czy wcięcie jest większe niż wcięcie MDLabel (czyli to właściwości Labela)
            current_indent = len(line) - len(line.lstrip())
            base_indent = len(indentation)
            
            if current_indent > base_indent:
                continue # Pomiń linię (np. text: root.text, theme_text_color...)
            else:
                inside_label = False # Koniec bloku MDLabel
        
        new_lines.append(line)

    # Zapisz zmiany
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"[SUKCES] Zaktualizowano plik: {target_file}")
    print("Teraz dymki czatu powinny pozwalać na zaznaczanie i kopiowanie tekstu.")

if __name__ == "__main__":
    find_and_fix_ui()