@echo off
TITLE Agent 007 - Naprawa Srodowiska
COLOR 0A

echo --- DIAGNOSTYKA ---
echo Sprawdzanie dostepnosci Pythona...
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo [BLAD] Nie wykryto komendy 'python'.
    echo Sprobuj wpisac: py --version
    pause
    exit /b
)
echo Python wykryty poprawnie.

echo.
echo --- AKTUALIZACJA ZALEZNOSCI ---

echo [1/6] Aktualizacja pip...
python -m pip install --upgrade pip

echo.
echo [2/6] Instalacja Kivy (Core)...
python -m pip install "kivy>=2.3.0"

echo.
echo [3/6] Instalacja KivyMD (Material Design)...
:: Wymuszamy wersje kompatybilna, czasami 1.2.0 jest jako pre-release
python -m pip install "kivymd>=1.2.0" --pre

echo.
echo [4/6] Instalacja Silnika AI...
python -m pip install "google-generativeai>=0.4.0"

echo.
echo [5/6] Instalacja Narzedzi Pomocniczych...
python -m pip install python-dotenv Pillow docutils

echo.
echo --- WERYFIKACJA ---
python -c "import kivy; import kivymd; print(f'Sukces! Kivy: {kivy.__version__}, KivyMD: {kivymd.__version__}')"

echo.
echo ===================================================
echo  SRODOWISKO GOTOWE.
echo ===================================================
echo.
echo Uruchamiam Agenta...
python main.py

pause