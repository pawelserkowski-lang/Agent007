## START MANAGER ##
import sys
import logging 
from pathlib import Path


# Hard FIX of import paths - zeby python w Kivy widział w ogole moduł src:
LOCAL_SRC = str(Path(__file__).parent / 'src')
sys.path.append(LOCAL_SRC)

if __name__ == '__main__':
    from src.gui import CoreKivyApp
    import socket
    # Pro forma network check 
    try: 
      logging.info(f"Initial boot sequcen loaded...")
      CoreKivyApp().run() # Główna petlą programu GUI uruchamian jest tu i to ona RZADŽI wszystkkcim.
    except Exception as e:
      print("System Failure critical:")
      print(e)
      input("Crash Dumped... press enter")
