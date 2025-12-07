# -*- coding: utf-8 -*-
"""
Configuration centrale de l'application :
chemins d'accès aux fichiers de données et constantes globales.
"""

from pathlib import Path

# ---------------------------------------------------------------
# 📁 Dossiers de base
# ---------------------------------------------------------------

# Dossier racine du projet
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

# Chemins par défaut — si les modules prod_api_tools / conso_api_tools
# existent, utiliser leurs constantes
try:
    from prod_api_tools.config import (
        DATA_FOLDER as PROD_DIR, CSV_FILE as PROD_CSV, ARCHIVE_FILE as PROD_ZIP)
except Exception:
    PROD_DIR = DATA_DIR.joinpath("prod")
    PROD_CSV = PROD_DIR.joinpath("production_data.csv")
    PROD_ZIP = PROD_DIR.joinpath("raw_prod_files.zip")

try:
    from conso_api_tools.config import (
        FOLDER_1H as CONSO_DIR, CSV_1H as CONSO_CSV, ZIP_FILE as CONSO_ZIP)
except Exception:
    CONSO_DIR = DATA_DIR.joinpath("conso")
    CONSO_CSV = CONSO_DIR.joinpath("consumption_data_1h.csv")
    CONSO_ZIP = CONSO_DIR.joinpath("raw_conso_files.zip")

GLOBAL_DIR = DATA_DIR.joinpath("merged")
GLOBAL_CSV = GLOBAL_DIR.joinpath("global.csv")

# ---------------------------------------------------------------
# ⚙️ Paramètres d'application
# ---------------------------------------------------------------

APP_TITLE = "Suivi consommation / production électrique"
DATE_FORMAT = "%Y-%m-%d %H:%M"
PLOT_THEME = "plotly_white"

# ---------------------------------------------------------------
# 🔑 Variables de sécurité (API, tokens, etc.)
# ---------------------------------------------------------------
# (Chargées via .env ou gestionnaire de secrets)

ENV_FILE = BASE_DIR.joinpath(".env")

APP_CONFIG = {
    "PROD_CSV": PROD_CSV,
    "CONSO_CSV": CONSO_CSV,
    "ARCHIVE_PROD": PROD_ZIP,
    "ARCHIVE_CONSO": CONSO_ZIP,
    "GLOBAL_DIR": GLOBAL_DIR,
    "GLOBAL_CSV": GLOBAL_CSV,
    "APP_TITLE" : APP_TITLE,
    "DATE_FORMAT": DATE_FORMAT,
    "PLOT_THEME": PLOT_THEME,
    "ENV_FILE": ENV_FILE
}