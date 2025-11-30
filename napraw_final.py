import os

def fix_model_manager():
    path = "core/model_manager.py"
    print(f"🔧 Naprawiam {path}...")
    
    # Nadpisujemy plik prostą funkcją, która ZAWSZE zwraca Twój model
    new_content = """
import google.generativeai as genai
import os

def get_best_model(api_key=None):
    # WYMUSZENIE MODELU
    print("[ModelManager] WYMUSZONO MODEL: gemini-3-pro-preview")
    return "models/gemini-3-pro-preview"
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content.strip())
    print("✅ Wymuszono model gemini-3-pro-preview w managerze.")

def fix_agent():
    path = "core/agent.py"
    print(f"🔧 Naprawiam {path}...")
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # 1. NAPRAWA BŁĘDU 400 (Wyłączenie Search)
        # Szukamy linii definiującej tools i zamieniamy ją na pustą listę
        if 'tools = [{"google_search_retrieval": {}}]' in line:
            new_lines.append('            tools = [] # Search wylaczony przez patch\n')
            print("✅ Usunięto błędne narzędzie Google Search (naprawa crasha).")
        
        # 2. WYMUSZENIE MODELU W AGENCIE
        # Szukamy linii ustalającej target_model i wpisujemy nasz na sztywno
        elif 'target_model = self.cached_model if self.cached_model' in line:
            new_lines.append('            target_model = "gemini-3-pro-preview"\n')
            print("✅ Wymuszono model gemini-3-pro-preview w logice agenta.")
            
        else:
            new_lines.append(line)
            
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    print("🚀 Rozpoczynam ostateczną naprawę...")
    fix_model_manager()
    fix_agent()
    print("\n🎉 GOTOWE! Wszystkie poprawki wgrane.")
    print("Uruchom teraz: python launcher.py")