import os

# Konfiguracja
TARGET_MODEL = "gemini-3-pro-preview"
OLD_MODEL = "gemini-3-pro-preview"

def patch_project():
    print(f"🔍 Szukam plików, aby zmienić domyślny model na: {TARGET_MODEL}...")
    
    patched = False
    
    # Przeszukujemy katalog core i główny
    dirs_to_search = ['.', 'core', 'ui']
    
    for directory in dirs_to_search:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith(".py"):
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Sprawdzamy czy plik zawiera stary model
                    if OLD_MODEL in content:
                        print(f"📝 Znaleziono konfigurację w pliku: {filepath}")
                        
                        # Zamiana - wstawiamy nowy model przed starym lub zamiast niego
                        # Tutaj robimy prostą zamianę tekstu, co wymusi nowy model jako priorytet
                        new_content = content.replace(OLD_MODEL, TARGET_MODEL)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                            
                        print(f"✅ Zaktualizowano model w: {filepath}")
                        patched = True
                        
                except Exception as e:
                    print(f"⚠️ Błąd podczas odczytu {filepath}: {e}")

    if patched:
        print("\n🎉 Gotowe! Model został zmieniony.")
        print("Możesz teraz uruchomić program: python launcher.py")
    else:
        print("\n❌ Nie znaleziono pliku z definicją modelu.")
        print("Upewnij się, że jesteś w głównym folderze Agent007.")

if __name__ == "__main__":
    patch_project()