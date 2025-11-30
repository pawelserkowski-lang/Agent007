import os

def patch_ui_threading():
    """Naprawia błąd wątków w ui/app.py"""
    target_file = os.path.join("ui", "app.py")
    if not os.path.exists(target_file):
        print(f"[SKIP] Nie znaleziono {target_file}")
        return

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Szukamy problematycznej linii
    broken_line = "self.api_key = key_source"
    
    # Nowa wersja bezpieczna dla wątków
    fixed_block = """
            # --- PATCH: Thread Safe Update ---
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self, 'api_key', key_source))
            # ---------------------------------
    """

    if broken_line in content and "Clock.schedule_once" not in content:
        print(f"[FIX] Naprawiam błąd wątków w {target_file}...")
        # Musimy zachować wcięcia, więc robimy to na liście linii
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if broken_line in line:
                indent = line[:line.find(broken_line)]
                new_lines.append(f"{indent}from kivy.clock import Clock\n")
                new_lines.append(f"{indent}Clock.schedule_once(lambda dt: setattr(self, 'api_key', key_source))\n")
            else:
                new_lines.append(line)
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("[SUKCES] UI Threading naprawiony.")
    else:
        print("[INFO] ui/app.py wygląda na już naprawiony lub inny niż oczekiwano.")

def patch_model_name():
    """Zmienia domyślny model z gemini-1.5-pro na gemini-1.5-flash"""
    print("[SEARCH] Szukam definicji modelu w plikach...")
    
    # Szukamy we wszystkich plikach .py
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Zamieniamy stary model na nowy, bardziej dostępny
                    if "gemini-1.5-pro" in content:
                        print(f"[FIX] Aktualizuję model w {path}...")
                        new_content = content.replace("gemini-1.5-pro", "gemini-1.5-flash")
                        
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"[SUKCES] Zmieniono model na 'gemini-1.5-flash' w {file}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    print("--- ROZPOCZYNAM NAPRAWĘ AGENTA ---")
    patch_ui_threading()
    patch_model_name()
    print("--- ZAKOŃCZONO ---")