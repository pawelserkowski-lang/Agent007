import os

# Nowa logika: Tylko PRO, najnowsza wersja
NEW_MANAGER_CODE = """
import google.generativeai as genai
import os
import re

def get_best_model(api_key=None):
    \"\"\"
    Pobiera listę modeli i wymusza wybór wersji PRO.
    Wybiera najnowszą dostępną wersję PRO (np. 1.5-pro-002 > 1.5-pro-001).
    \"\"\"
    # 1. Pobierz klucz
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("[ModelManager] Brak klucza API. Fallback.")
        return "models/gemini-1.5-pro"

    try:
        print(f"[ModelManager] Szukam najlepszego modelu PRO...")
        genai.configure(api_key=api_key)
        
        # 2. Pobierz listę modeli
        all_models = list(genai.list_models())
        # Tylko te, które generują tekst (chat)
        chat_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # 3. Filtrowanie: Szukamy tylko modeli z 'pro' w nazwie
        pro_models = [m for m in chat_models if 'pro' in m.name.lower()]
        
        # Jeśli z jakiegoś powodu nie ma wersji PRO, bierzemy wszystkie (żeby program nie padł)
        candidate_pool = pro_models if pro_models else chat_models
        
        if not candidate_pool:
            print("[ModelManager] Nie znaleziono żadnych modeli. Używam domyślnego.")
            return "models/gemini-1.5-pro"

        # 4. Logika sortowania (Najnowszy wygrywa)
        def model_sorter(model_obj):
            name = model_obj.name
            score = 0.0
            
            # Wersja główna (np. 1.5 > 1.0)
            ver_match = re.search(r'(\d+)\.(\d+)', name)
            if ver_match:
                score += float(f"{ver_match.group(1)}.{ver_match.group(2)}") * 1000
            
            # Numer wydania (np. -002 > -001)
            # 'latest' dostaje wysoki priorytet, ale konkretny numer builda (np. 002) 
            # często jest lepszy niż ogólny alias.
            if 'latest' in name:
                score += 900
            else:
                build_match = re.search(r'-(\d{3})', name)
                if build_match:
                    score += int(build_match.group(1))
            
            # Preferujemy stabilne wersje (bez 'exp' / 'experimental')
            if 'exp' not in name and 'experimental' not in name:
                score += 50

            return score

        # Sortujemy od najlepszego
        candidate_pool.sort(key=model_sorter, reverse=True)
        
        best_model = candidate_pool[0].name
        
        # Logi dla Ciebie
        print(f"[ModelManager] Znalezione modele PRO: {[m.name for m in pro_models]}")
        print(f"[ModelManager] WYBRANO: {best_model}")
        
        return best_model

    except Exception as e:
        print(f"[ModelManager] Błąd API: {e}")
        # W razie błędu zwracamy bezpieczny standard PRO
        return "models/gemini-1.5-pro"
"""

def update_file():
    path = os.path.join("core", "model_manager.py")
    
    if not os.path.exists("core"):
        os.makedirs("core")
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(NEW_MANAGER_CODE)
    
    print(f"[SUKCES] Zaktualizowano {path}")
    print("Teraz program będzie wybierał wyłącznie najnowszą wersję PRO.")

if __name__ == "__main__":
    update_file()