# -*- coding: utf-8 -*-
"""
daily_update.py

Script quotidien pour GitHub Actions ou exécution locale.

Fonctionnalités :
- Vérifie pour la veille si les fichiers JSON sont déjà présents dans l’archive
- Télécharge les données 1h et 30min si manquantes
- Concatène les nouvelles données dans consumption_data_1h.csv et consumption_data_30min.csv
- Archive les JSON dans raw_conso_files.zip et supprime les fichiers locaux
- Affiche la progression et un récapitulatif clair
"""

import sys
from pathlib import Path

# Ajout du dossier racine au sys.path pour permettre les imports de 'common'
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from datetime import datetime, timedelta
from conso_api_tools.api_client import fetch_and_archive
from conso_api_tools import config
from common.utils import print_section, format_date_to_str, cleanup_folders

def main():
    # -------------------------------
    # 🕒 Préparation
    # -------------------------------
    yesterday = datetime.now() - timedelta(days=1)
    date_str = format_date_to_str(date_obj = yesterday)

    print_section(f"📆 Mise à jour quotidienne des données Conso API ({date_str})")

    downloaded = False

    # -------------------------------
    # ⚙️ Téléchargement 1h
    # -------------------------------
    print(f"⚡ Vérification des données 1h pour le {date_str}...")
    new_1h = fetch_and_archive(
        date_obj = yesterday, 
        interval = "1h")
    if new_1h:
        downloaded = True

    # -------------------------------
    # ⚙️ Téléchargement 30min
    # -------------------------------
    print(f"⚡ Vérification des données 30min pour le {date_str}...")
    new_30 = fetch_and_archive(
        date_obj = yesterday, 
        interval = "30min")
    if new_30:
        downloaded = True

    # -------------------------------
    # 🧹 Nettoyage des dossiers temporaires
    # -------------------------------
    tmp_folders = [Path(config.FOLDER_1H), 
                   Path(config.FOLDER_30MIN)]
    cleanup_folders(tmp_folders)

    # -------------------------------
    # ✅ Récapitulatif
    # -------------------------------
    print_section("✅ Résumé du téléchargement quotidien des données de consommation")
    if downloaded:
        print(f"📊 Données mises à jour pour le {date_str}")
    else:
        print(f"📦 Aucune nouvelle donnée à télécharger pour le {date_str}")
    print("🧹 Dossiers temporaires nettoyés avec succès.")
    print("🏁 Script daily_update.py terminé.")


if __name__ == "__main__":
    main()
