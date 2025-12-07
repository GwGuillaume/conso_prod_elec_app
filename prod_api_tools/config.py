# -*- coding: utf-8 -*-
"""
config.py

Configuration centrale pour la gestion des données de production Hoymiles.
"""

from os import getenv
from pathlib import Path
from dotenv import load_dotenv

from common.config import ROOT_PATH

# Chargement des variables depuis .env
load_dotenv()

# -------------------------------
# ⚙️ CONFIGURATION PRINCIPALE
# -------------------------------

load_dotenv()
USERNAME = getenv("HOYMILES_USER")
PASSWORD = getenv("HOYMILES_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("HOYMILES_USER ou HOYMILES_PASSWORD non définis dans .env")

LOGIN_PAGE = "https://global.hoymiles.com/website/login"
TIMEOUT = 20

# Répertoire de stockage des fichiers CSV
BASE_DATA_DIR = ROOT_PATH.joinpath("data")
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Chemins des fichiers CSV et ZIP
DATA_FOLDER = BASE_DATA_DIR.joinpath("prod")
RAW_FOLDER = DATA_FOLDER.joinpath("tmp_raw")
ARCHIVE_FILE = DATA_FOLDER.joinpath("raw_prod_files.zip")
CSV_RAW = DATA_FOLDER.joinpath("raw_production_data.csv")
CSV_1H = DATA_FOLDER.joinpath("production_data_1h.csv")
CSV_30MIN = DATA_FOLDER.joinpath("production_data_30min.csv")

# Paramètres par défaut
SITE_ID = 156600

# URL de base de l’API Hoymiles
API_BASE_URL = "https://neapi.hoymiles.com/pvm-report/api/0/station/report/"