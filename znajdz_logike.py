import os

def locate_logic():
    print("🕵️ Szukam pliku sterującego wyborem modelu...")
    found_file = None
    
    # Szukamy pliku zawierającego unikalne komunikaty z Twoich logów
    search_phrases = ["Auto-Discovery", "Wybrano priorytetowy model", "PRIORITY_MODELS"]
    
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for phrase in search_phrases:
                        if phrase in content:
                            print(f"\n✅ ZNALEZIONO KLUCZOWY PLIK: {path}")
                            print(f"   (Zawiera frazę: '{phrase}')")
                            found_file = path
                            
                            # Wypisz fragmenty, które mogą zawierać listę modeli
                            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = f.readlines()
                                print("   --- Fragmenty kodu ---")
                                for i, line in enumerate(lines):
                                    if "gemini" in line or "search" in line or "PRIORITY" in line:
                                        # Wypisujemy tylko pierwsze 100 znaków linii dla czytelności
                                        print(f"   Linia {i+1}: {line.strip()[:100]}")
                            return # Przerywamy po znalezieniu pierwszego pasującego pliku
                            
                except Exception:
                    pass

    if not found_file:
        print("❌ Nie znaleziono pliku z logiką Auto-Discovery.")

if __name__ == "__main__":
    locate_logic()