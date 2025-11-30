import os

def show_ui():
    paths = ["ui/layout.kv", "ui/screens/chat.py"]
    
    for path in paths:
        print(f"\n{'='*20} PLIK: {path} {'='*20}\n")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print("Brak pliku.")

if __name__ == "__main__":
    show_ui()