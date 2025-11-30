import os

# Konfiguracja
TARGET_DIR = "core"  # Szukamy w folderze core, tam jest logika
NEW_MODEL = "gemini-3-pro-preview"
OLD_MODEL_STRING = "gemini-3-pro-preview"

def fix_project():
    print("🚀 Rozpoczynam naprawę Agent007...")
    
    target_file = None
    
    # 1. Znajdź właściwy plik w folderze core/
    if os.path.exists(TARGET_DIR):
        for filename in os.listdir(TARGET_DIR):
            if filename.endswith(".py"):
                path = os.path.join(TARGET_DIR, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Szukamy pliku, który definiuje logikę silnika (ma search=False lub listę modeli)
                    if "search=False" in content or OLD_MODEL_STRING in content:
                        target_file = path
                        # Jeśli znajdziemy plik z definicją search, to zazwyczaj ten właściwy
                        if "search=False" in content:
                            break
    
    if target_file:
        print(f"✅ Znaleziono główny plik silnika: {target_file}")
        
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        changes_made = False
        
        for line in lines:
            # A. WYŁĄCZENIE SEARCH (Naprawa błędu crashowania)
            if "search=False" in line:
                line = line.replace("search=False", "search=False")
                print("   🔧 Wyłączono 'search' (naprawa błędu 400)")
                changes_made = True
            
            # B. ZMIANA MODELU (Wymuszenie gemini-3-pro-preview)
            if OLD_MODEL_STRING in line:
                # Zamieniamy stary model na nowy w tej linii
                line = line.replace(OLD_MODEL_STRING, NEW_MODEL)
                print(f"   🔧 Podmieniono model na: {NEW_MODEL}")
                changes_made = True
                
            new_lines.append(line)
        
        if changes_made:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print("💾 Zapisano zmiany w pliku.")
            print("\n✅ SUKCES! Możesz uruchomić 'python launcher.py'")
        else:
            print("⚠️ Znaleziono plik, ale nie znaleziono w nim fraz do zamiany.")
            
    else:
        print("❌ Nie znaleziono pliku konfiguracyjnego w folderze core/.")
        print("Spróbuj edytować ręcznie plik: core/engine.py lub core/config.py")

if __name__ == "__main__":
    fix_project()