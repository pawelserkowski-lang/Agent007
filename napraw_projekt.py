import os
import re
import shutil

# --- KONFIGURACJA ---
TARGET_MODEL = "gemini-3-pro-preview-11-2025"
AGENT_FILE = os.path.join("core", "agent.py")
BUBBLE_FILE = os.path.join("ui", "chat_bubble.py")

def backup_file(filepath):
    """Tworzy kopię zapasową pliku przed zmianą."""
    if os.path.exists(filepath):
        shutil.copy(filepath, filepath + ".bak")
        print(f"[BACKUP] Utworzono kopię: {filepath}.bak")

def fix_agent_model():
    """Wymusza model w core/agent.py"""
    if not os.path.exists(AGENT_FILE):
        print(f"[BŁĄD] Nie znaleziono pliku: {AGENT_FILE}")
        return

    backup_file(AGENT_FILE)
    
    with open(AGENT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Znajdź i podmień inicjalizację modelu (genai.GenerativeModel(...))
    # Regex szuka genai.GenerativeModel( i wszystkiego do zamknięcia nawiasu
    pattern = r'genai\.GenerativeModel\s*\((?:[^)(]|\((?:[^)(]+|\([^)(]*\))*\))*\)'
    
    # Nowa linia kodu
    replacement = f'genai.GenerativeModel("{TARGET_MODEL}")'
    
    new_content = re.sub(pattern, replacement, content)

    # Sprawdzenie czy zmiana zaszła
    if new_content != content:
        with open(AGENT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[SUKCES] Model ustawiony na sztywno: {TARGET_MODEL} w {AGENT_FILE}")
    else:
        print(f"[INFO] Nie znaleziono pasującego wzorca w {AGENT_FILE} lub model już ustawiony.")

def fix_chat_bubble():
    """Zamienia MDLabel na TextInput w ui/chat_bubble.py"""
    if not os.path.exists(BUBBLE_FILE):
        print(f"[BŁĄD] Nie znaleziono pliku: {BUBBLE_FILE}")
        return

    backup_file(BUBBLE_FILE)

    with open(BUBBLE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    import_added = False
    
    for line in lines:
        # 1. Dodaj import TextInput na początku pliku
        if "import" in line and not import_added:
            new_lines.append("from kivy.uix.textinput import TextInput\n")
            import_added = True
        
        # 2. Zamień dziedziczenie lub użycie MDLabel na TextInput
        # Uwaga: To prosta zamiana, zakłada standardowe formatowanie
        if "MDLabel" in line:
            # Zamień klasę
            line = line.replace("MDLabel", "TextInput")
            
            # Jeśli to definicja w KV string lub Pythonie, dodaj właściwości readonly
            # (To uproszczenie - dodajemy parametry w nowej linii jeśli to kod Pythona)
            if "(" in line: # Wywołanie w Pythonie
                line = line.replace(")", ', readonly=True, background_color=(0,0,0,0), foreground_color=(1,1,1,1), cursor_color=(0,0,0,0))')
        
        # 3. Usuń parametry specyficzne dla MDLabel, które psują TextInput
        if "theme_text_color" in line or "text_color" in line:
            continue # Pomiń te linie, TextInput ich nie obsługuje
            
        new_lines.append(line)

    with open(BUBBLE_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"[SUKCES] Podmieniono MDLabel na TextInput w {BUBBLE_FILE}")

if __name__ == "__main__":
    print("--- ROZPOCZYNAM NAPRAWĘ AGENTA 007 ---")
    fix_agent_model()
    fix_chat_bubble()
    print("--- ZAKOŃCZONO ---")
    print("Uruchom teraz 'main.py' i sprawdź działanie.")