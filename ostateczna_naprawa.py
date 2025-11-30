import os

def patch_file(filepath, replacements):
    """Funkcja pomocnicza do zamiany tekstu w pliku."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = content
        modified = False
        
        for old, new in replacements.items():
            if old in new_content:
                new_content = new_content.replace(old, new)
                print(f"   🔧 W pliku {filepath}:")
                print(f"      Zamieniono: '{old}' -> '{new}'")
                modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"   💾 Zapisano zmiany w {filepath}")
            return True
    except Exception as e:
        print(f"   ⚠️ Błąd przetwarzania {filepath}: {e}")
    return False

def run_fix():
    print("🚀 Rozpoczynam ostateczną naprawę...")
    
    # 1. Definicje zamian
    # Zamieniamy stary model na nowy
    # Wyłączamy search (search=True -> search=False)
    replacements = {
        "gemini-pro-latest": "gemini-3-pro-preview",
        "search=True": "search=False",
        "search = True": "search = False",
        "search=self.search": "search=False" # Wymuszenie wyłączenia w klasie Agent
    }

    count = 0
    
    # 2. Przeszukujemy folder CORE (logika)
    if os.path.exists("core"):
        for filename in os.listdir("core"):
            if filename.endswith(".py"):
                if patch_file(os.path.join("core", filename), replacements):
                    count += 1

    # 3. Przeszukujemy folder UI (interfejs - tam często jest konfiguracja startowa)
    # Sprawdzamy podfoldery w UI
    if os.path.exists("ui"):
        for root, dirs, files in os.walk("ui"):
            for filename in files:
                if filename.endswith(".py"):
                    if patch_file(os.path.join(root, filename), replacements):
                        count += 1

    # 4. Sprawdzamy plik główny main.py
    if os.path.exists("main.py"):
        if patch_file("main.py", replacements):
            count += 1

    if count > 0:
        print(f"\n✅ Sukces! Zmodyfikowano {count} plików.")
        print("Spróbuj uruchomić: python launcher.py")
    else:
        print("\n❌ Nie znaleziono miejsc do naprawy automatycznej.")
        print("Będziemy musieli edytować plik core/agent.py ręcznie.")
        print("Otwórz core/agent.py i wklej jego zawartość tutaj, a powiem Ci co zmienić.")

if __name__ == "__main__":
    run_fix()