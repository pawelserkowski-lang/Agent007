import os
import shutil
from pathlib import Path

def clean_slate():
    root = Path(__file__).parent.parent
    
    # Lista plików do bezwzględnego usunięcia
    to_delete = [
        # ZAGROŻENIA BEZPIECZEŃSTWA (Hardcoded Keys)
        "core/agent.py",
        "config.json", 
        
        # MARTWY KOD / TYMCZASOWE FIXY
        "fix_thread_crash.py",
        "start_system_v2.py",
        "launcher.py",
        "launcher_pro.py",
        "launcher_ultimate.py",
        "debug_druid.bat", # Zakładam, że stworzymy nowy start script
        "fix_all.py",
        "fix.py",
        "update_to_v2.py",
        "wymus_gemini3.py",
        "ustaw_model.py",
        "znajdz_i_napraw.py",
        "znajdz_logike.py",
        "pokaz_kod.py",
        "pokaz_ui.py",
        "force_key.py",
        "force_pro_model.py",
        "Engine_Surgeon_Fix.py",
        "Final_Config_Correction.py",
        "Fixed_GUI_Injector_Final.py",
        "MASTER_REPLASTER.py",
        "ostateczna_naprawa.py",
        "patch_agent.py",
        "patch_druid.py",
        "patch_v2.py",
        "Sprawdz_Zmienne.py"
    ]

    print("--- ROZPOCZYNAM CZYSZCZENIE PROJEKTU (OPTION C) ---")
    
    deleted_count = 0
    for file_rel in to_delete:
        target = root / file_rel
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                print(f"[USUNIĘTO]: {file_rel}")
                deleted_count += 1
            except Exception as e:
                print(f"[BŁĄD]: Nie można usunąć {file_rel}: {e}")
        else:
            pass # Plik już nie istnieje, to dobrze.

    # Usunięcie folderu _ARCHIVE_BEFORE_V2 jeśli istnieje
    archive = root / "_ARCHIVE_BEFORE_V2"
    if archive.exists():
        shutil.rmtree(archive)
        print("[USUNIĘTO]: _ARCHIVE_BEFORE_V2")
        deleted_count += 1

    print(f"--- ZAKOŃCZONO. Usunięto {deleted_count} obiektów. ---")
    print("Twój projekt korzysta teraz wyłącznie z 'main.py' i 'src/config.py'.")

if __name__ == "__main__":
    clean_slate()