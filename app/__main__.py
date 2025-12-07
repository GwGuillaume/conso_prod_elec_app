# -*- coding: utf-8 -*-
"""
app/__main__.py

Permet de lancer l'application Streamlit via :
    python -m app
"""

from pathlib import Path
import subprocess
import sys


def main():
    app_path = Path(__file__).parent.joinpath("main.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
