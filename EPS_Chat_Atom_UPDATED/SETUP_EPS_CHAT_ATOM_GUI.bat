@echo off
echo Tworzenie wirtualnego srodowiska .venv ...
python -m venv .venv
if errorlevel 1 (
  echo BLAD: nie udalo sie utworzyc .venv
  pause
  goto :eof
)
echo.
echo Aktywacja .venv ...
call .venv\Scripts\activate.bat
echo.
echo Instalacja wymaganych pakietow (customtkinter, pillow, requests)...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Gotowe.
echo Aby uruchomic aplikacje w tym srodowisku, uzyj:
echo   call .venv\Scripts\activate.bat
echo   python run_eps_chat_atom_gui.py
pause
