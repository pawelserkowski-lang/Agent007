@echo off
TITLE Agent 007 - Launcher
COLOR 0A

echo --- URUCHAMIANIE Z BEZWZGLEDNEJ SCIEZKI ---
echo Wykryto: C:\Program Files\Python313\python.exe

:: 1. Najpierw upewniamy sie, ze biblioteki sa na miejscu
"C:\Program Files\Python313\python.exe" setup.py

:: 2. Jesli setup przeszedl, odpalamy aplikacje
IF %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUKCES] Uruchamianie GUI...
    "C:\Program Files\Python313\python.exe" main.py
) ELSE (
    echo [BLAD] Setup zakonczyl sie niepowodzeniem.
    pause
)