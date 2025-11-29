@echo off
REM ======================================================================
REM  start_agent.bat
REM  ----------------------------------------------------------------------
REM  This batch script launches the Local AI Agent built with KivyMD.
REM
REM  It sets a few environment variables used by the agent (model name,
REM  SQLite database path, history limit and system prompt) and then runs
REM  main.py using the configured Python interpreter. You can modify the
REM  values below to suit your needs. On Windows, setting the code page to
REM  UTF-8 ensures that Polish characters display correctly.
REM
REM  Usage:
REM      Double‑click this file, or run it from the command prompt.
REM ======================================================================

@echo on

REM Change to the directory of this script so paths are relative
cd /d "%~dp0"

REM Use UTF-8 code page for proper display of Polish characters
chcp 65001 >NUL

REM Specify the Python executable. Adjust if your Python is installed
REM under a different name or path (e.g. python3).
set "PYTHON_EXEC=python"

REM Optional: set up a virtual environment if you have one.
REM Uncomment the following lines if you created a venv in this directory.
REM if exist venv\Scripts\activate.bat (
REM     call venv\Scripts\activate.bat
REM )

REM ----------------------------------------------------------------------
REM Configure agent parameters. Modify as needed.
set "MODEL_NAME=llama3"
set "DB_PATH=history.db"
set "HISTORY_LIMIT=50"
set "SYSTEM_PROMPT=You are a helpful local AI assistant that replies in Polish."

REM Export these variables so that Python can read them via os.getenv
set "MODEL_NAME=%MODEL_NAME%"
set "DB_PATH=%DB_PATH%"
set "HISTORY_LIMIT=%HISTORY_LIMIT%"
set "SYSTEM_PROMPT=%SYSTEM_PROMPT%"

REM ----------------------------------------------------------------------
REM Start the agent. Any additional command‑line parameters can be added
REM after main.py below. For example, to specify a different .env file or
REM log level, append arguments here.
%PYTHON_EXEC% main.py

REM Pause to keep the window open after the script finishes (optional)
pause