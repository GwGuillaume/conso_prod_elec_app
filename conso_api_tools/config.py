"""
config.py

Chargement de la configuration depuis le fichier .env
(enedis token, linky PRM, chemins de fichiers, etc.)
"""

from os import getenv
from dotenv import load_dotenv

from common.config import ROOT_PATH

# Charger .env uniquement s'il existe localement
ENV_FILE = ROOT_PATH / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# -------------------------------
# ⚙️ CONFIGURATION PRINCIPALE
# -------------------------------

ENEDIS_TOKEN = getenv("ENEDIS_TOKEN")
LINKY_PRM = getenv("LINKY_PRM")

if not ENEDIS_TOKEN or not LINKY_PRM:
    raise RuntimeError("⚡ ENEDIS_TOKEN ou LINKY_PRM non définis dans .env")

# Répertoire de stockage des fichiers JSON et CSV
BASE_DATA_DIR = ROOT_PATH.joinpath("data/conso")
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Chemins des dossiers, fichiers CSV et ZIP
FOLDER_30MIN = BASE_DATA_DIR.joinpath("conso_30min")
FOLDER_1H = BASE_DATA_DIR.joinpath("conso_1h")
CSV_1H = BASE_DATA_DIR.joinpath("consumption_data_1h.csv")
CSV_30MIN = BASE_DATA_DIR.joinpath("consumption_data_30min.csv")
ZIP_FILE = BASE_DATA_DIR.joinpath("raw_conso_files.zip")

# URL de base de l’API Conso
API_BASE_URL = "https://conso.boris.sh/api/consumption_load_curve"
