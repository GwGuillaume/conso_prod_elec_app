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

import sys
from pathlib import Path

# Ajout du dossier racine au sys.path pour permettre les imports de 'common'
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from datetime import datetime, timedelta

from conso_api_tools.config import FOLDER_30MIN, FOLDER_1H
from conso_api_tools.api_client import fetch_and_archive
from common.utils import cleanup_folders, format_date_to_str, print_section, yesterday
from common.config import START_DATE

def fetch_all_missing_data(start_date: datetime = START_DATE):
    """
    Télécharge toutes les données de consommation manquantes depuis la date donnée.

    Paramètre :
        start_date (datetime) : date de début (incluse)
    
    Retour :
        None 
    """
    print_section(f"📡 Téléchargement de l’historique Conso API depuis le {format_date_to_str(start_date)}")
    date_incr = start_date

    while date_incr <= yesterday():
        date_str = format_date_to_str(date_obj = date_incr)
        print(f"\n📅 Traitement du {date_str}...")
        # 1h
        new_1h = fetch_and_archive(
            date_obj = date_incr, 
            interval = "1h")
        # 30min
        new_30min = fetch_and_archive(
            date_obj = date_incr, 
            interval = "30min")
        # Incrémentation d'une journée
        date_incr = date_incr + timedelta(days=1)
    
    # Suppression des dossiers temporaires
    tmp_folders = [Path(FOLDER_1H), Path(FOLDER_30MIN)]
    cleanup_folders(tmp_folders)

    print("📦 Historique de consommation mis à jour.")


if __name__ == "__main__":
    # Téléchargement des données depuis START_DATE jusqu'à hier
    fetch_all_missing_data(start_date = START_DATE)
