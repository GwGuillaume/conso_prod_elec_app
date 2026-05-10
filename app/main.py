# -*- coding: utf-8 -*-
"""
Point d’entrée principal de l’application Streamlit.
Gère le chargement des données, l’affichage et la logique de navigation.
"""

import sys
from pathlib import Path

# Ajout du dossier racine au sys.path pour permettre les imports de 'common', 'conso_api_tools' et 'prod_api_tools'
root_path = Path(__file__).resolve().parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import streamlit as st
from babel.dates import format_date
from app.ui import apply_theme, render_app
from app.core.data_manager import load_merged_data


# ---------------------------------------------------------------------
# ⚙️ Configuration initiale Streamlit (doit être appelée avant tout)
# ---------------------------------------------------------------------
st.set_page_config(

    page_title = "Suivi de la consommation et de la production électrique ⚡️",
    layout = "wide",
    page_icon = "🔋",
    initial_sidebar_state = "expanded",
)

# ------------------------------------------------------------------
# 🎬 Fonction principale
# ------------------------------------------------------------------

def main():
    """
    Initialise l'application Streamlit :
    - Charge les fichiers de données de consommation et de production
    - Fusionne les deux jeux de données sur la colonne 'datetime'
    - Transmet le DataFrame fusionné à l'interface graphique
    """

    # Thème
    apply_theme()

    # --- Chargement et fusion des données avec message remplaçable ---
    status_box = st.empty()  # crée une zone qui pourra être remplacée
    status_box.info("📥 Chargement et fusion des données...")

    with st.spinner(text = "🔄 Traitement en cours..."):
        try:
            # Fusion des données de consommation et de production
            merged_df = load_merged_data()

            # Récupération automatique des dates min/max
            min_date = format_date(
                date = merged_df["datetime"].min(),
                format = "EEEE d MMMM y",
                locale = "fr")
            max_date = format_date(
                date = merged_df["datetime"].max(),
                format = "EEEE d MMMM y",
                locale = "fr")
            
            # Remplacement du message bleu par un message vert
            status_msg = f"✅ Données du {min_date} au {max_date} chargées et fusionnées avec succès !"

            # Affichage du message vert
            status_box.success(
                body = status_msg)
        except Exception as e:
            status_box.error(
                body = f"❌ Erreur lors du chargement ou de la fusion des données : {e}")
            return

    # --- Rendu principal de l'application ---
    render_app(
        df = merged_df)


if __name__ == "__main__":
    main()
