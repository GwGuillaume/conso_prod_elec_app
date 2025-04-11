# ------------------------------- IMPORTS ------------------------------------ #

import os
import pandas as pd
import streamlit as st
import locale

# Configuration de la locale pour l'affichage des dates en français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

# Import des fonctions utilitaires
from files_tools import process_raw_consumption_file, process_raw_production_repo
from data_tools import complete_dataframe_datetimes, subsampling_in_15min
from plot_tools import plot_production_vs_consumption

# --------------------------- PRÉPARATION DES DONNÉES --------------------------- #

# Définition des chemins relatifs vers les dossier des fichiers de consommation et
# de production électrique
conso_path = os.path.join('data', 'conso')
prod_path = os.path.join('data', 'prod')

# Lecture et nettoyage des données de consommation électrique
conso_df = process_raw_consumption_file(consumption_data_path = conso_path,
                                        consumption_data_folder="mes-donnees-elec-2025-04-08",
                                        raw_csv_filename="mes-puissances-atteintes-30min-004033466112-56140.csv",
                                        clean_csv_filename="consumption_data.csv")

# Lecture et nettoyage des données de production photovoltaïque
prod_df = process_raw_production_repo(production_data_path=prod_path,
                                      production_data_folder="raw_csv_files",
                                      raw_csv_root_filename="station_power_data_*.csv",
                                      clean_csv_filename="production_data.csv")

# Tri des données de consommation et ajout des créneaux manquants (échantillonnage
# complet)
conso_df_30min_raw = conso_df.sort_values("datetime").reset_index(drop=True)
conso_df_30min = complete_dataframe_datetimes(df=conso_df_30min_raw,
                                              min_freq='30min')

# Conversion des données de consommation en pas de 15 minutes
conso_df_15min = subsampling_in_15min(conso_df_30min)

# Tri des données de production et ajout des créneaux manquants (échantillonnage
# complet)
prod_df_30min_raw = prod_df.sort_values("datetime").reset_index(drop=True)
prod_df_30min = complete_dataframe_datetimes(df=prod_df_30min_raw,
                                             min_freq='15min')

# Fusion des deux DataFrames sur la colonne datetime
merged_df = pd.merge(conso_df_15min, prod_df,
                     on="datetime", how="inner")

# Calcul de la somme consommation + production quand la consommation est nulle,
# 0 sinon
merged_df["total"] = merged_df["consommation"] + merged_df["production"]
merged_df.loc[(merged_df["consommation"] == 0), 'total'] = 0
merged_df.loc[(merged_df["total"] == 0), 'total'] = 0
merged_df.fillna(value=0, inplace=True)

# ----------------------- INTERFACE GRAPHIQUE STREAMLIT ------------------------- #

# Titre de l'application
st.title("Analyse de la consommation et de la production électrique")

# Choix de la période d'analyse
st.markdown("### Sélection de la période")

# Bornes min et max de dates disponibles dans les données
min_date = merged_df['datetime'].min().date()
max_date = merged_df['datetime'].max().date()

# Deux colonnes côte à côte pour la date et l'heure de début/fin
col_debut, col_fin = st.columns(2)
with col_debut:
    date_debut = st.date_input(label="Date de début",
                               value=min_date,
                               min_value=min_date,
                               max_value=max_date)
    heure_debut = st.time_input(label="Heure de début",
                                value=pd.to_datetime("00:00").time(),
                                key="heure_debut")
with col_fin:
    date_fin = st.date_input(label="Date de fin",
                             value=max_date,
                             min_value=min_date,
                             max_value=max_date)
    heure_fin = st.time_input(label="Heure de fin",
                              value=pd.to_datetime("23:59").time(),
                              key="heure_fin")

# Combinaison date + heure en datetime complet
start_datetime = pd.to_datetime(f"{date_debut} {heure_debut}")
end_datetime = pd.to_datetime(f"{date_fin} {heure_fin}")

# Filtrage du DataFrame selon l'intervalle choisi
df_filtered = merged_df[(merged_df['datetime'] >= start_datetime) &
                        (merged_df['datetime'] <= end_datetime)]

# Affichage graphique interactif
fig = plot_production_vs_consumption(df_filtered)
st.markdown("### Consommation, Production et Total")
st.plotly_chart(fig)