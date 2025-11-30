@echo off
TITLE Agent 007 - Matrix Console
COLOR 0A

echo --- START SYSTEMU ---

:: Proba 1: Launcher 'py' (Zalecany na Windows)
py --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [INFO] Wykryto 'py'. Uruchamianie...
    py setup.py
    echo.
    py main.py
    pause
    exit
)

:: Proba 2: Komenda 'python' (Jesli dodana do PATH)
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [INFO] Wykryto 'python'. Uruchamianie...
    python setup.py
    echo.
    python main.py
    pause
    exit
)

:: Proba 3: Twarda sciezka (Ostatecznosc)
IF EXIST "C:\Program Files\Python313\python.exe" (
    echo [INFO] Wykryto sciezke bezposrednia.
    "C:\Program Files\Python313\python.exe" setup.py
    echo.
    "C:\Program Files\Python313\python.exe" main.py
    pause
    exit
)

echo.
echo [KRYTYCZNY BLAD] Nie znaleziono zadnego interpretera Python.
echo Zainstaluj Python ze strony python.org i zaznacz "Add to PATH".
pause