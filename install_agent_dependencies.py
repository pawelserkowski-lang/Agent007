#!/usr/bin/env python3
"""
install_agent_dependencies.py
---------------------------------

This script automates the installation of the Python packages required to
run the local KivyMD AI agent. It performs the following actions:

1. Upgrades pip and a few core packaging tools (setuptools and virtualenv).
2. Installs Kivy with pre-built wheels (using the ``kivy[base]`` extra),
   KivyMD, Ollama, and python-dotenv via pip.
3. Attempts to download the ``llama3`` model for Ollama. If Ollama is not
   installed, the script will notify the user and skip the model download.

Usage:
    python install_agent_dependencies.py

Notes:
    - This script assumes you have Python 3.10+ installed and available
      via the ``python`` command. If your Python executable has a different
      name (e.g. ``python3``), adjust the commands accordingly.
    - On Windows, it is recommended to run this script from a PowerShell
      terminal with administrator privileges for full package installation.

"""

import subprocess
import sys


def run_command(command: str) -> int:
    """Run a shell command and return its exit code.

    The command is echoed to stdout before execution. If the command
    returns a non-zero exit code, that code is returned to the caller.

    Args:
        command: The command line to execute as a string.

    Returns:
        The return code from the executed command.
    """
    print(f"\n➡️  Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"⚠️  Command exited with return code {result.returncode}")
    return result.returncode


def update_pip_and_tools() -> None:
    """Upgrade pip and essential build tools."""
    print("Updating pip and core Python packaging tools…")
    run_command("python -m pip install --upgrade pip setuptools virtualenv")


def install_dependencies() -> None:
    """Install Kivy, KivyMD, Ollama, and python-dotenv via pip."""
    print("Installing Kivy, KivyMD, Ollama, and python-dotenv via pip…")
    # Kivy uses an extra called "base" to install pre-built wheels. See:
    # https://kivy.org/doc/stable/installation/installation-windows.html
    run_command(
        'python -m pip install "kivy[base]" kivymd ollama python-dotenv'
    )


def pull_llama_model(model_name: str = "llama3") -> None:
    """Attempt to download a model via Ollama.

    Args:
        model_name: The name of the model to pull, default "llama3".

    If the ``ollama`` CLI is not installed, the function will catch the
    resulting error and prompt the user to install Ollama manually.
    """
    print(f"Attempting to pull the '{model_name}' model via Ollama…")
    try:
        # Note: On Windows, you might need to add .exe to the command if using
        # a compiled binary. The generic command works across platforms.
        return_code = run_command(f"ollama pull {model_name}")
        if return_code != 0:
            raise RuntimeError
    except Exception:
        print(
            "\n⚠️  It appears that the 'ollama' command failed. "
            "Make sure Ollama is installed on your system and try "
            "running 'ollama pull {model_name}' manually."
        )


def main() -> None:
    """Execute installation steps in sequence."""
    update_pip_and_tools()
    install_dependencies()
    pull_llama_model()
    print("\n✅ All steps completed. You can now run your local AI agent.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user.")
        sys.exit(1)
