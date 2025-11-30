
import google.generativeai as genai
import os
import re

def get_best_model(api_key=None):
    """
    Wybiera model bazując na NUMERZE WERSJI.
    Cel: Znaleźć najwyższy numer (np. 2.5 > 2.0 > 1.5).
    """
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        return "models/gemini-1.5-pro"

    try:
        genai.configure(api_key=api_key)
        all_models = list(genai.list_models())
        chat_models = [m for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Filtrujemy tylko modele Gemini
        candidates = [m for m in chat_models if 'gemini' in m.name]

        def version_sorter(model_obj):
            name = model_obj.name
            score = 0.0
            
            # 1. Wyciągnij wersję (np. 2.5, 2.0, 1.5)
            # Szukamy wzorca: gemini-LICZBA.LICZBA
            ver_match = re.search(r'gemini-(\d+\.\d+)', name)
            if ver_match:
                version = float(ver_match.group(1))
                score += version * 10000  # Wersja jest najważniejsza (2.5 > 1.5)
            
            # 2. Preferuj PRO nad Flash
            if 'pro' in name.lower():
                score += 500
            
            # 3. Preferuj stabilne (bez 'exp'/'preview'), chyba że wersja jest wyższa
            # Ale w Twoim przypadku 2.5-preview jest lepsze niż 1.5-stable.
            # Więc punktujemy 'preview' mniej karnie niż różnicę wersji.
            
            # 4. 'latest' dostaje mały bonus, żeby wygrać w remisie
            if 'latest' in name:
                score += 10

            return score

        # Sortujemy od najwyższego wyniku
        candidates.sort(key=version_sorter, reverse=True)
        
        if candidates:
            best = candidates[0].name
            print(f"[ModelManager] Top 3 modele: {[m.name for m in candidates[:3]]}")
            print(f"[ModelManager] WYBRANO NAJPOTĘŻNIEJSZY: {best}")
            return best
            
    except Exception:
        pass
        
    return "models/gemini-1.5-pro"
