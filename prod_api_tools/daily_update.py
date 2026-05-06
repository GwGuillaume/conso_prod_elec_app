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

import sys
from pathlib import Path

# Ajout du dossier racine au sys.path pour permettre les imports de 'common'
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from datetime import datetime, timedelta
from prod_api_tools.config import SITE_ID, ARCHIVE_FILE, CSV_30MIN, CSV_1H, RAW_FOLDER
from prod_api_tools.api_client import fetch_and_archive
from common.utils import print_section, format_date_to_str, cleanup_folders


def main():
    # -------------------------------
    # 🕒 Préparation
    # -------------------------------
    yesterday = datetime.now() - timedelta(days=1)
    date_str = format_date_to_str(yesterday)

    print_section(f"📆 Mise à jour quotidienne de la production ({date_str})")

    # -------------------------------
    # ⚙️ Telechargement
    # -------------------------------
    print(f"⚡ Vérification des données de production pour le {date_str}...")

    downloaded = fetch_and_archive(yesterday, SITE_ID, ARCHIVE_FILE, CSV_30MIN, CSV_1H)

    # -------------------------------
    # 🧹 Nettoyage des dossiers temporaires
    # -------------------------------
    cleanup_folders([RAW_FOLDER])


    # -------------------------------
    # ✅ Récapitulatif
    # -------------------------------
    print_section("✅ Résumé du téléchargement quotidien des données de production")
    if downloaded:
        print(f"📊 Données de production mises à jour pour le {date_str}")
    else:
        print(f"📦 Aucune nouvelle donnée à télécharger pour le {date_str}")
    print("🧹 Dossiers temporaires nettoyés.")
    print("🏁 Script daily_update.py terminé.")


if __name__ == "__main__":
    main()
