# ------------------------------- IMPORTS ------------------------------------ #

import os
import streamlit as st
import locale

# Essaie de définir la locale française
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # Unix/Linux/Mac
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')    # Windows
    except locale.Error:
        print("⚠️ Impossible de définir la locale française. Vérifiez qu'elle est installée.")


# Import des fonctions utilitaires
from files_tools import process_raw_consumption_file, process_raw_production_repo
from data_tools import complete_dataframe_datetimes, merge_conso_prod_data, print_general_info
from plot_tools import plot_production_vs_consumption
from app_tools import period_choice

# --------------------------- PRÉPARATION DES DONNÉES --------------------------- #

# Définition des chemins relatifs vers les dossiers des fichiers de consommation et
# de production électrique
conso_path = os.path.join('data', 'conso')
prod_path = os.path.join('data', 'prod')

# Lecture et nettoyage des données de consommation électrique
conso_df = process_raw_consumption_file(consumption_data_path = conso_path,
                                        consumption_data_folder="mes-donnees-elec-2025-05-25",
                                        raw_csv_filename="mes-puissances-atteintes-30min-004033466112-56140.csv",
                                        clean_csv_filename="consumption_data.csv")

# Lecture et nettoyage des données de production photovoltaïque
prod_df = process_raw_production_repo(production_data_path=prod_path,
                                      production_data_folder="raw_csv_files",
                                      raw_csv_root_filename="station_power_data_*.csv",
                                      clean_csv_filename="production_data.csv")

# Tri des données de consommation et ajout des créneaux manquants (échantillonnage
# complet)
conso_df_30min = complete_dataframe_datetimes(df=conso_df,
                                              min_freq='30min')

# Tri des données de production et ajout des créneaux manquants (échantillonnage
# complet)
prod_df_15min = complete_dataframe_datetimes(df=prod_df,
                                             min_freq='15min')

# Moyenne de la production sur des intervalles de 30 minutes
prod_df_30min = prod_df_15min.set_index('datetime').resample("30T").mean().reset_index()

# Fusion des deux DataFrames sur la colonne datetime
merged_df = merge_conso_prod_data(conso_df_30min, prod_df_30min)

# ----------------------- INTERFACE GRAPHIQUE STREAMLIT ------------------------- #

# Titre de l'application
st.title("🔋 Suivi de la consommation et de la production électrique ⚡️")

# Choix du mode d'affichage ("Classique", "Hebdomadaire", "Mensuel" ou "Journée spécifique")
st.markdown("### 📅 Choix du mode d'affichage")
mode_affichage = st.radio(
    "Mode d'affichage du graphique",
    options=["Classique", "Hebdomadaire", "Mensuel", "Journée spécifique"],
    horizontal=True,
    index=0
)

# Choix dynamique de la période d'analyse selon le mode sélectionné
start_datetime, end_datetime = period_choice(mode_affichage, merged_df)

# Filtrage du DataFrame selon l'intervalle choisi
df_filtered = merged_df[(merged_df['datetime'] >= start_datetime) &
                        (merged_df['datetime'] <= end_datetime)]

# Affichage des informations générales de consommation et de production
st.markdown("### ⚡️ Consommation, Production et Total")

# Affichage des informations générales sur la période sélectionnée
info = print_general_info(mode_affichage, df_filtered)
st.markdown(info)

# Affichage du graphique
st.markdown("⚙️ Cliquer sur la légende pour activer/désactiver la "
            "visualisation de la consommation, production et/ou de "
            "leur combinaison")
fig = plot_production_vs_consumption(df_filtered, mode_affichage)
st.plotly_chart(fig, use_container_width=True)
