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
import time
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

_ENEDIS_TOKEN: Optional[str] = None


def _current_token() -> Optional[str]:
    """Retourne le token ENEDIS_TOKEN depuis .env ou l'environnement."""
    global _ENEDIS_TOKEN
    if _ENEDIS_TOKEN is None:
        # Charge le .env s'il existe (local), sinon utilise les variables d'env (GHA)
        load_dotenv()
        _ENEDIS_TOKEN = getenv("ENEDIS_TOKEN")

    return _ENEDIS_TOKEN


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


def _extract_day_from_value(value: object) -> Optional[str]:
    """Extrait la date au format YYYY-MM-DD depuis une valeur de type date."""
    if isinstance(value, datetime):
        return format_date_to_str(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).date().strftime("%Y-%m-%d")
        except ValueError:
            return cleaned.split("T", 1)[0]
    return None


def group_interval_readings_by_day(data: dict) -> dict[str, list[dict]]:
    """Regroupe les lectures d'un payload par jour afin de les archiver par date."""
    grouped: dict[str, list[dict]] = {}
    for item in data.get("interval_reading", []):
        day = _extract_day_from_value(item.get("date"))
        if day is None:
            continue
        grouped.setdefault(day, []).append(item)
    return grouped


def download_interval_data(
    date_str: str,
    interval: str = "30min",
    *,
    end_date_str: Optional[str] = None,
    max_retries: int = 3,
    retry_delay_seconds: int = 10,
) -> dict | None:
    """
    Télécharge les données de consommation pour une date donnée ou une plage de dates.

    Paramètres :
        date_str (str) : date de début au format 'YYYY-MM-DD'
        interval (str) : '30min' ou '1h'
        end_date_str (str | None) : date de fin au format 'YYYY-MM-DD' pour une requête de plage

    Retour :
        dict : données JSON renvoyées par l'API
    """
    if end_date_str is None:
        end_date_str = format_date_to_str(next_day(format_str_to_date(date_str)))

    url = f"{config.API_BASE_URL}?prm={config.LINKY_PRM}&start={date_str}&end={end_date_str}"
    response = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=_get_headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            if "interval_reading" not in data:
                raise ValueError(f"Aucune donnée disponible pour {date_str} → {end_date_str} ({interval})")
            return data
        except requests.exceptions.HTTPError as err:
            status_code = getattr(response, "status_code", None)
            if status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                wait = min(60, retry_delay_seconds * (attempt + 1))
                print(f"⚠️ Erreur {status_code} (Serveur Boris/Enedis). Tentative {attempt + 2}/{max_retries} dans {wait}s...")
                time.sleep(wait)
                continue

            if end_date_str == format_date_to_str(datetime.today()):
                print(f"❌ Données du {date_str} non disponibles (date cible {end_date_str} est aujourd'hui).")
                return None

            print(f"💥 Erreur API définitive pour {date_str} → {end_date_str}: {err}")
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                wait = 5
                print(f"⚠️ Erreur de connexion/timeout pour {date_str}. Tentative {attempt + 2}/{max_retries} dans {wait}s...")
                time.sleep(wait)
                continue
            print(f"📡 Échec de connexion définitif pour {date_str}: {e}")
            return None
    return None


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
    for item in data.get("interval_reading", []):
        rows.append({
            "datetime": item["date"],
            "consommation": item["value"]
        })
    if not rows:
        return

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


def _archive_interval_payloads(data: dict, interval: str, csv_file: Path, folder: Path) -> int:
    """Archive les lectures d'un payload par jour dans le ZIP et dans le CSV."""
    grouped = group_interval_readings_by_day(data)
    saved_count = 0
    interval_folder_name = "conso_30min" if interval == "30min" else "conso_1h"

    for date_str, items in sorted(grouped.items()):
        if check_json_in_archive(zip_path=config.ZIP_FILE, date_str=date_str, interval_folder=interval_folder_name):
            continue

        day_payload = {
            key: value for key, value in data.items() if key != "interval_reading"
        }
        day_payload["interval_reading"] = items

        json_path = save_json(day_payload, date_str, folder)
        append_to_csv(day_payload, csv_file)
        print(f"🧾 Données ajoutées à {csv_file} pour le {date_str}")

        add_file_to_zip(
            tmp_file=json_path,
            zip_path=config.ZIP_FILE,
            arcname=f"{interval_folder_name}/conso_{date_str}.json"
        )
        json_path.unlink()
        print(f"✅ {json_path.name} archivé et supprimé localement")
        saved_count += 1

    return saved_count


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

    data = download_interval_data(date_str, interval)
    if data is None:
        return False

    saved_count = _archive_interval_payloads(data, interval, csv_file, folder)
    return saved_count > 0


def fetch_range_and_archive(
    start_date_obj: datetime,
    end_date_obj: datetime,
    interval: str,
    *,
    chunk_days: int = 7,
    request_delay_seconds: float = 1.0,
):
    """Télécharge l'historique d'une plage de dates en requêtes groupées par lots de plusieurs jours."""
    current_start = start_date_obj
    downloaded_any = False

    while current_start <= end_date_obj:
        current_end = min(current_start + timedelta(days=chunk_days - 1), end_date_obj)
        start_str = format_date_to_str(current_start)
        end_str = format_date_to_str(current_end)
        print(f"📦 Requête API {interval} du {start_str} au {end_str} ({chunk_days} jours)")

        data = download_interval_data(start_str, interval, end_date_str=end_str)
        if data is not None:
            folder = config.FOLDER_30MIN if interval == "30min" else config.FOLDER_1H
            csv_file = config.CSV_30MIN if interval == "30min" else config.CSV_1H
            downloaded_any = _archive_interval_payloads(data, interval, csv_file, folder) > 0 or downloaded_any

        if request_delay_seconds > 0:
            time.sleep(request_delay_seconds)

        current_start = current_end + timedelta(days=1)

    return downloaded_any
