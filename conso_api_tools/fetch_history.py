# -*- coding: utf-8 -*-
"""
fetch_history.py

Télécharge l’historique complet des données de consommation depuis une date donnée
jusqu’à la veille du jour courant.

⚙️ Fonctionnalités :
- Vérifie pour chaque date si les fichiers JSON sont déjà présents dans l’archive
- Télécharge uniquement les jours manquants (1h et 30min)
- Concatène les nouvelles données dans consumption_data_1h.csv et consumption_data_30min.csv
- Archive les JSON dans raw_conso_files.zip et supprime les fichiers locaux
- Affiche un compteur de journées réellement téléchargées

🧩 Exemple d’utilisation :
    python conso_api_tools/fetch_history.py
"""

import argparse
import sys
from pathlib import Path

# Ajout du dossier racine au sys.path pour permettre les imports de 'common'
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from datetime import datetime

from conso_api_tools.config import FOLDER_30MIN, FOLDER_1H
from conso_api_tools.api_client import fetch_range_and_archive
from common.utils import cleanup_folders, format_date_to_str, format_str_to_date, print_section, yesterday
from common.config import START_DATE


def parse_args():
    parser = argparse.ArgumentParser(description="Télécharger un historique de consommation Enedis")
    parser.add_argument("--start-date", default=None, help="Date de début au format YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="Date de fin au format YYYY-MM-DD (par défaut hier)")
    parser.add_argument("--chunk-days", type=int, default=7, help="Nombre de jours par requête API")
    parser.add_argument("--interval", choices=["1h", "30min"], default=None, help="Intervalle à télécharger (sinon 1h et 30min)")
    return parser.parse_args()


def fetch_all_missing_data(
    start_date: datetime = START_DATE,
    end_date: datetime | None = None,
    chunk_days: int = 7,
    interval: str | None = None,
):
    """
    Télécharge toutes les données de consommation manquantes depuis la date donnée.

    Paramètre :
        start_date (datetime) : date de début (incluse)

    Retour :
        None
    """
    if end_date is None:
        end_date = yesterday()

    print_section(f"📡 Téléchargement de l’historique Conso API depuis le {format_date_to_str(start_date)}")
    intervals = [interval] if interval else ["1h", "30min"]

    for current_interval in intervals:
        print(f"\n⚡ Traitement de l’intervalle {current_interval}...")
        fetch_range_and_archive(
            start_date_obj=start_date,
            end_date_obj=end_date,
            interval=current_interval,
            chunk_days=chunk_days,
        )

    tmp_folders = [Path(FOLDER_1H), Path(FOLDER_30MIN)]
    cleanup_folders(tmp_folders)

    print("📦 Historique de consommation mis à jour.")


if __name__ == "__main__":
    args = parse_args()
    start_date = format_str_to_date(args.start_date) if args.start_date else START_DATE
    end_date = format_str_to_date(args.end_date) if args.end_date else None
    fetch_all_missing_data(
        start_date=start_date,
        end_date=end_date,
        chunk_days=args.chunk_days,
        interval=args.interval,
    )
