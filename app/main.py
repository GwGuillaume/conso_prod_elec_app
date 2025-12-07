# -*- coding: utf-8 -*-
"""
Point d’entrée principal de l’application Streamlit.
Gère le chargement des données, l’affichage et la logique de navigation.
"""

import streamlit as st
from babel.dates import format_date
from app.ui import apply_theme, render_app
from app.core.data_manager import load_merged_data


# ---------------------------------------------------------------------
# ⚙️ Configuration initiale Streamlit (doit être appelée avant tout)
# ---------------------------------------------------------------------
st.set_page_config(

    page_title="Suivi de la consommation et de la production électrique ⚡️",
    layout="wide",
    page_icon="🔋",
    initial_sidebar_state="expanded",
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

    with st.spinner("🔄 Traitement en cours..."):
        try:
            # Fusion des données de consommation et de production
            merged_df = load_merged_data()
            # Récupération automatique des dates min/max
            min_date = format_date(date=merged_df["datetime"].min(),
                                   format="EEEE d MMMM y",
                                   locale="fr")
            max_date = format_date(date=merged_df["datetime"].max(),
                                   format="EEEE d MMMM y",
                                   locale="fr")
            # Remplacement du message bleu par un message vert
            status_msg = f"✅ Données du {min_date} au {max_date} chargées et fusionnées avec succès !"
            status_box.success(status_msg)
        except Exception as e:
            status_box.error(f"❌ Erreur lors du chargement ou de la fusion des données : {e}")
            return

    # --- Rendu principal de l'application ---
    render_app(merged_df)

    # # Choix utilisateur
    # st.markdown("### 📅 Choix du mode d'affichage")
    # mode = select_mode()
    # start_datetime, end_datetime = select_period(mode, merged_df)
    #
    # # Filtrage
    # df_filtered = merged_df[
    #     (merged_df["datetime"] >= start_datetime) &
    #     (merged_df["datetime"] <= end_datetime)
    # ]
    #
    # # Informations générales
    # st.markdown("### ⚡️ Consommation, Production et Total")
    # st.markdown(get_summary_info(df_filtered, mode))
    #
    # # Graphique
    # st.markdown("⚙️ Cliquez sur la légende pour activer/désactiver les courbes.")
    # fig = plot_production_vs_consumption(df_filtered, mode)
    # # ID unique basé sur le mode + borne de dates
    # chart_key = f"plot_{mode}_{start_datetime.strftime('%Y%m%d%H%M')}_{end_datetime.strftime('%Y%m%d%H%M')}"
    #
    # st.plotly_chart(fig, use_container_width=True, key=chart_key)

if __name__ == "__main__":
    main()
