@echo off
:: Ta komenda ustawia folder roboczy na ten, w którym jest plik .bat
cd /d "%~dp0"

:: Wyświetl informację o starcie
echo Uruchamianie Agent007 (DebugDruid)...

:: Próba uruchomienia launchera
python launcher.py

:: Jeśli program zamknie się z błędem, zatrzymaj okno, żebyś mógł przeczytać komunikat
if %errorlevel% neq 0 (
    echo.
    echo WYSTAPIL BLAD!
    echo Sprawdz, czy zainstalowales biblioteki komenda: pip install -r requirements.txt
    pause
)