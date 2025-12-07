"""
config.py

Définition des paramètres communs
"""

from pathlib import Path
from datetime import datetime


# Dossier racine du projet
ROOT_PATH = Path(__file__).resolve().parents[1]

# Date de départ
START_DATE = datetime(2025, 3, 25)