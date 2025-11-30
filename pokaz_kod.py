import os

def read_file(path):
    print(f"\n{'='*20} PLIK: {path} {'='*20}\n")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"Błąd odczytu: {e}")
    else:
        print("Plik nie istnieje.")
    print(f"\n{'='*50}\n")

# Sprawdzamy dwa najważniejsze pliki
read_file("core/model_manager.py")
read_file("core/agent.py")