# -*- coding: utf-8 -*-
"""
daily_update.py

Script quotidien pour la mise à jour des données Hoymiles.
Peut être exécuté localement ou via un workflow GitHub Actions.

Fonctionnalités :
- Télécharge les données de la veille
- Intègre dans le CSV cumulatif
- Met à jour l’archive ZIP
- Supprime les dossiers temporaires
"""

from datetime import datetime, timedelta
from prod_api_tools.config import SITE_ID, ARCHIVE_FILE, CSV_FILE, RAW_FOLDER
from prod_api_tools.api_client import fetch_and_archive
from common.file_utils import cleanup_folders
from common.utils import print_section, format_date


def main():
    yesterday = datetime.now() - timedelta(days=1)
    print_section(f"☀️ Mise à jour quotidienne de la production ({format_date(yesterday)})")

    downloaded = fetch_and_archive(yesterday, SITE_ID, ARCHIVE_FILE, CSV_FILE)
    cleanup_folders([RAW_FOLDER])

    print_section("✅ Récapitulatif")
    if downloaded:
        print(f"📊 Données de production mises à jour pour {format_date(yesterday)}")
    else:
        print(f"📦 Aucune nouvelle donnée à télécharger pour {format_date(yesterday)}")
    print("🧹 Dossiers temporaires nettoyés.")
    print("🏁 Script daily_update.py terminé.")


if __name__ == "__main__":
    main()
