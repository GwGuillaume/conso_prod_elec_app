# api_client.py
# -*- coding: utf-8 -*-
"""
Client pour l'API Conso (consommation électrique).

Fonctions principales :
- Vérifie si un JSON pour une date est déjà dans l'archive
- Télécharge les données 1h ou 30min si manquantes
- Concatène les CSV
- Archive les JSON et supprime les fichiers locaux

Utilise :
- config.py pour token, PRM et chemins de fichiers
- common/utils.py pour la gestion des fichiers et archives
"""

import pandas as pd
from datetime import datetime, timedelta
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from os import getenv

from conso_api_tools import config
from common.utils import ensure_folder, add_file_to_zip, save_json, check_json_in_archive, format_date_to_str, next_day, format_str_to_date

# -------------------------------
# ⚙️ CONFIGURATION DES DOSSIERS
# -------------------------------

ensure_folder(config.FOLDER_1H)
ensure_folder(config.FOLDER_30MIN)

# -------------------------------
# 🔧 FONCTIONS PRINCIPALES
# -------------------------------

def _current_token() -> Optional[str]:
    """Retourne le token ENEDIS_TOKEN depuis .env ou l'environnement."""
    load_dotenv(override=True)  # recharge le .env à chaque appel
    return getenv("ENEDIS_TOKEN")

def _get_headers(token: Optional[str] = None) -> dict:
    """
    Construit les en-têtes pour les requêtes Enedis.
    """
    tok = token or _current_token()
    if not tok:
        raise RuntimeError("⚠️ Aucun token disponible (ENEDIS_TOKEN non défini).")
    return {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/json",
        "User-Agent": "github.com/gguillaume/conso-prod-elec",
        "From": "contact@example.com",
    }

def download_interval_data(date_str: str, interval: str = "30min") -> dict | None:
    """
    Télécharge les données de consommation pour une date donnée et un intervalle.

    Paramètres :
        date_str (str) : date au format 'YYYY-MM-DD'
        interval (str) : '30min' ou '1h'

    Retour :
        dict : données JSON renvoyées par l'API
    """
    day_after = format_date_to_str(next_day(format_str_to_date(date_str)))
    url = f"{config.API_BASE_URL}?prm={config.LINKY_PRM}&start={date_str}&end={day_after}"

    try:
        response = requests.get(url, headers=_get_headers(), timeout=20)
        response.raise_for_status()
        data = response.json()
        if "interval_reading" not in data:
            raise ValueError(f"Aucune donnée disponible pour {date_str} ({interval})")
        return data
    except requests.exceptions.HTTPError as err:
        # Si la date de fin demandée est aujourd'hui, l'erreur est normale car les données ne sont pas prêtes
        if day_after == format_date_to_str(datetime.today()):
            print(f"❌ Données du {date_str} non disponibles (date cible {day_after} est aujourd'hui).")
            pass
        else:
            raise SystemExit(err)

def append_to_csv(data: dict, csv_file: Path):
    """
    Concatène les valeurs JSON dans le CSV correspondant.

    Paramètres :
    ------------
        data (dict) : Données JSON de la courbe de charge.
        csv_file (Path) : Chemin du fichier CSV à mettre à jour.

    Détails :
    ---------
        - Utilise le séparateur ';' pour rester cohérent avec les fichiers de production.
        - Ajoute les données sans réécrire l'en-tête si le fichier existe déjà.
        - Force l'encodage UTF-8 avec BOM pour compatibilité Windows.
    """
    rows = []
    # unit = data.get("reading_type", {}).get("unit", "")
    for item in data.get("interval_reading", []):
        rows.append({
            "datetime": item["date"],
            f"consommation": item["value"]
        })
    df = pd.DataFrame(rows)
    if csv_file.exists():
        df.to_csv(
            csv_file,
            mode="a",
            header=False,
            index=False,
            sep=";",
            encoding="utf-8-sig")
    else:
        df.to_csv(
            csv_file,
            index=False,
            sep=";",
            encoding="utf-8-sig")

def fetch_and_archive(date_obj: datetime, interval: str):
    """
    Télécharge les données si elles ne sont pas déjà archivées,
    les ajoute au CSV et au ZIP, puis supprime le JSON local.

    Paramètres :
        date_obj (datetime) : date ciblée
        interval (str) : '30min' ou '1h'

    Retour :
        bool : True si une requête API a été effectuée, False sinon
    """
    date_str = format_date_to_str(date_obj)
    folder = config.FOLDER_30MIN if interval == "30min" else config.FOLDER_1H
    csv_file = config.CSV_30MIN if interval == "30min" else config.CSV_1H
    interval_folder_name = "conso_30min" if interval == "30min" else "conso_1h"
    arcname = f"{interval_folder_name}/conso_{date_str}.json"

    if check_json_in_archive(zip_path=config.ZIP_FILE,
                             date_str=date_str,
                             interval_folder=interval_folder_name):
        print(f"📂 {arcname} déjà présent dans l’archive, pas de téléchargement.")
        return False

    # Téléchargement
    data = download_interval_data(date_str, interval)
    if data is None:
        return False
    else:
        json_path = save_json(data, date_str, folder)
        # Concaténation du CSV
        append_to_csv(data, csv_file)
        print(f"🧾 Données ajoutées à {csv_file}")

        # Archivage et suppression
        add_file_to_zip(
            tmp_file=json_path,
            zip_path=config.ZIP_FILE,
            arcname=arcname
        )
        json_path.unlink()
        print(f"✅ {json_path.name} archivé et supprimé localement")

        return True
