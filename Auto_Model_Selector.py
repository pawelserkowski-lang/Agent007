"""
AUTO MODEL SELECTOR & CONFIG PATCHER
Ten skrypt łączy się z Google, pobiera listę dostępnych modeli dla Twojego klucza
i automatycznie wpisuje najlepszy działający do src/config.py.
"""
import os
import google.generativeai as genai
from pathlib import Path

# Szukanie klucza w systemie (tak jak w aplikacji)
candidates = ["GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]
API_KEY = ""
for c in candidates:
    val = os.environ.get(c)
    if val and "WPISZ" not in val:
        API_KEY = val
        break

print("-" * 50)
print(f"DEBUG: Używam klucza: {API_KEY[:5]}...*******")
print("Łączenie z Google Cloud w celu pobrania listy modeli...")
print("-" * 50)

if not API_KEY:
    print("BŁĄD KRYTYCZNY: Nie znaleziono klucza w zmiennych środowiskowych!")
    exit()

genai.configure(api_key=API_KEY)

try:
    available_models = []
    # Pobieramy listę modeli
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - Znaleziono: {m.name}")
            available_models.append(m.name)
            
    # Algorytm wyboru najlepszego
    SELECTED_MODEL = ""
    
    # Lista priorytetów (od najnowszego do najstarszego pewniaka)
    priorities = [
        "models/gemini-3-pro-preview",
    ]
    
    for p in priorities:
        if p in available_models:
            SELECTED_MODEL = p.replace("models/", "") # config woli nazwę bez prefixu
            break
            
    if not SELECTED_MODEL and available_models:
        # Fallback: weź pierwszy z listy jeśli żaden z priorytetów nie pasuje
        SELECTED_MODEL = available_models[0].replace("models/", "")

    if SELECTED_MODEL:
        print(f"\n>> ZWYCIĘZCA: {SELECTED_MODEL}")
        
        # NADPISYWANIE CONFIGU
        cfg_path = Path("src/config.py")
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Brutalna podmiana stringa z modelem
        # Szukamy linii z MODEL_ALIAS
        import re
        new_content = re.sub(
            r'MODEL_ALIAS: str = ".*?"', 
            f'MODEL_ALIAS: str = "{SELECTED_MODEL}"', 
            content
        )
        
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f">> [SUKCES] Zaktualizowano src/config.py na model: {SELECTED_MODEL}")
        print(">> Teraz uruchom: python start_system_v2.py")
        
    else:
        print(">> [BŁĄD] Twoje konto Google nie widzi żadnych modeli generatywnych.")
        print("   Sprawdź czy masz włączone 'Generative Language API' w konsoli Google Cloud.")

except Exception as e:
    print(f"\n[FATAL ERROR]: {e}")
    print("Sugestia: Twój klucz API może być błędny lub biblioteka za stara.")
    print("Wykonaj: pip install --upgrade google-generativeai")