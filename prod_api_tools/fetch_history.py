# -*- coding: utf-8 -*-
"""
fetch_history.py

Télécharge l'historique complet des données de production depuis une date donnée
jusqu'à la veille du jour courant.

Fonctionnalités :
- Vérifie pour chaque date si les fichiers existent déjà dans l'archive
- Télécharge uniquement les jours manquants
- Ajoute les nouvelles données au fichier production_data.csv
- Archive les CSV dans raw_prod_files.zip
- Supprime les dossiers temporaires

🧩 Exemple d'utilisation :
    python prod_api_tools/fetch_history.py
"""

from os import getenv
from datetime import datetime, timedelta
from common.utils import  format_date_to_str, print_section, cleanup_folders
from prod_api_tools.config import SITE_ID, ARCHIVE_FILE, CSV_30MIN, CSV_1H, RAW_FOLDER
from prod_api_tools.api_client import fetch_and_archive, _current_token, refresh_token
from common.config import START_DATE
from common.utils import yesterday


if _current_token() is None:
    print("⚠️ Problème de token détecté — tentative de rafraîchissement...")
    new_token = refresh_token(mode="gha" if getenv("GITHUB_ACTIONS") else "local")
    if not new_token:
        raise RuntimeError("❌ Impossible de rafraîchir le token Hoymiles.")


def fetch_all_missing_data(start_date: datetime = START_DATE):
    """
    Télécharge toutes les données de production manquantes depuis la date donnée.

    Paramètre :
        start_date (datetime) : date de début (incluse)
    """
    print_section(f"📡 Téléchargement de l'historique Hoymiles depuis le {format_date_to_str(start_date)}")
    date_incr = start_date

    while date_incr <= yesterday() :
        try:
            print(f"\n📅 Traitement du {format_date_to_str(date_incr)}...")
            fetch_and_archive(date_incr, SITE_ID, ARCHIVE_FILE, CSV_30MIN, CSV_1H)
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {format_date_to_str(date_incr)}: {e}")
        # Incrémentation d'une journée
        date_incr = date_incr + timedelta(days=1)
    cleanup_folders([RAW_FOLDER])
    print("📦 Historique de production mis à jour.")


if __name__ == "__main__":
    fetch_all_missing_data(START_DATE)
