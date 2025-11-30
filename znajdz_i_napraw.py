import os

def nuclear_fix():
    print("🕵️ Przeszukuję CAŁY projekt (wszystkie podfoldery)...")
    
    files_modified = 0
    
    # Przechodzimy przez wszystkie katalogi i pliki
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"): # Sprawdzamy tylko pliki Python
                path = os.path.join(root, file)
                
                # Pomijamy sam skrypt naprawczy
                if "znajdz_i_napraw.py" in path:
                    continue

                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    modified = False
                    
                    # 1. ZMIANA MODELU
                    # Szukamy starego modelu i zamieniamy na nowy
                    if "gemini-pro-latest" in content:
                        print(f"🎯 Znaleziono definicję modelu w: {path}")
                        content = content.replace("gemini-pro-latest", "gemini-3-pro-preview")
                        modified = True
                    
                    # 2. WYŁĄCZENIE SEARCH (Naprawa błędu 400)
                    # Szukamy włączenia wyszukiwania i wyłączamy je
                    if "search=True" in content:
                        print(f"🔧 Wyłączam 'search=True' w: {path}")
                        content = content.replace("search=True", "search=False")
                        modified = True
                    elif "search = True" in content: # Wersja ze spacjami
                        print(f"🔧 Wyłączam 'search = True' w: {path}")
                        content = content.replace("search = True", "search = False")
                        modified = True

                    # Zapisujemy zmiany, jeśli coś znaleziono
                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"💾 ZAPISANO ZMIANY w pliku: {path}")
                        files_modified += 1
                        
                except Exception as e:
                    # Ignorujemy błędy odczytu (np. pliki binarne)
                    pass

    if files_modified > 0:
        print(f"\n✅ Sukces! Zmodyfikowano {files_modified} plików.")
        print("Teraz uruchom: python launcher.py")
    else:
        print("\n❌ Nie znaleziono fraz 'gemini-pro-latest' ani 'search=True' w żadnym pliku.")
        print("To bardzo dziwne. Czy na pewno pobrałeś pliki projektu?")

if __name__ == "__main__":
    nuclear_fix()