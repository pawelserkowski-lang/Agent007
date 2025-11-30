import os
import re
import shutil

KV_FILE = os.path.join("ui", "layout.kv")
BACKUP_FILE = KV_FILE + ".bak"

# Parametry dla TextInput (bez pola text, bo to pobierzemy z oryginału)
TEXT_INPUT_PROPS = """
    readonly: True
    background_color: 0, 0, 0, 0
    foreground_color: 1, 1, 1, 1
    cursor_color: 0, 0, 0, 0
    multiline: True
    size_hint_y: None
    height: self.minimum_height
    font_size: "16sp"
    padding: [10, 10]
    background_normal: ''
    background_active: ''
"""

def restore_backup():
    """Przywraca plik z kopii zapasowej, jeśli istnieje."""
    if os.path.exists(BACKUP_FILE):
        shutil.copy(BACKUP_FILE, KV_FILE)
        print(f"[INFO] Przywrócono oryginał z {BACKUP_FILE}")
        return True
    else:
        print(f"[BŁĄD] Brak pliku kopii zapasowej {BACKUP_FILE}. Nie można naprawić.")
        return False

def smart_fix():
    if not restore_backup():
        return

    with open(KV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Szukamy definicji MDLabel, która wygląda na dymek czatu
        # (zazwyczaj ma adaptive_height lub jest wewnątrz struktury czatu)
        if "MDLabel:" in line:
            # Sprawdzamy kontekst - czy to ten właściwy label?
            # Szukamy w następnych liniach właściwości 'text:'
            is_target = False
            original_text_prop = ""
            indent = line.split("MDLabel")[0]
            
            # Skanujemy kilka linii w przód, żeby znaleźć 'text:' i upewnić się, że to dymek
            j = 1
            temp_props = []
            while i + j < len(lines):
                next_line = lines[i+j]
                # Jeśli wcięcie jest mniejsze lub równe, to koniec bloku MDLabel
                if not next_line.strip():
                    j += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= len(indent):
                    break
                
                # Zbieramy właściwości
                temp_props.append(next_line)
                
                # Szukamy właściwości text
                if "text:" in next_line:
                    original_text_prop = next_line.strip() # np. "text: root.message"
                
                # Jeśli znajdziemy adaptive_height (częste w dymkach) lub root. (wiązanie)
                if "root." in next_line:
                    is_target = True
                
                j += 1

            # Jeśli to nasz cel (ma wiązanie do root lub wygląda na dymek)
            if is_target and original_text_prop:
                print(f"[ZNALEZIONO] MDLabel do zamiany w linii {i+1}")
                print(f"             Oryginalny tekst: {original_text_prop}")
                
                # 1. Wstawiamy TextInput
                new_lines.append(f"{indent}TextInput:\n")
                
                # 2. Wstawiamy ORYGINALNĄ linię z text: (z zachowaniem wcięcia)
                # Musimy obliczyć wcięcie dla właściwości (zazwyczaj +4 spacje od widgetu)
                prop_indent = indent + "    "
                # Wyciągamy samą wartość po dwukropku
                text_value = original_text_prop.split(":", 1)[1].strip()
                new_lines.append(f"{prop_indent}text: {text_value}\n")
                
                # 3. Dodajemy właściwości TextInput
                for prop in TEXT_INPUT_PROPS.strip().split('\n'):
                    new_lines.append(f"{prop_indent}{prop.strip()}\n")
                
                # 4. Przepisujemy inne ważne właściwości z oryginału (np. id, pos_hint)
                # Ale pomijamy te, które psują TextInput (color, halign, theme_text_color)
                for prop_line in temp_props:
                    if any(x in prop_line for x in ["theme_text_color", "halign", "color:", "text_color"]):
                        continue
                    if "text:" in prop_line: 
                        continue # Już dodaliśmy
                    
                    # Dodajemy resztę (np. id, size_hint)
                    # Upewniamy się, że wcięcie jest poprawne
                    stripped = prop_line.strip()
                    new_lines.append(f"{prop_indent}{stripped}\n")

                # Przesuwamy główny licznik o tyle linii, ile przetworzyliśmy w bloku MDLabel
                i += j
                continue
            
        # Jeśli to nie MDLabel lub nie ten właściwy, przepisujemy linię
        new_lines.append(line)
        i += 1

    with open(KV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("[SUKCES] Plik naprawiony. Zachowano oryginalne wiązania tekstu.")

if __name__ == "__main__":
    smart_fix()