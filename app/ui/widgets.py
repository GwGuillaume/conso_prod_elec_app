# -*- coding: utf-8 -*-
"""
Composants interactifs Streamlit : sélection du mode, de la période,
et affichage des messages contextuels.
"""

import streamlit as st
import pandas as pd


# ----------------------------------------------------------------------
# 🎛️ Choix du mode d'affichage
# ----------------------------------------------------------------------

def select_mode() -> str:
    """
    Permet à l'utilisateur de choisir le mode d'affichage :
    Classique, Hebdomadaire, Mensuel ou Journée spécifique.

    Retour :
        mode : str
            mode d'affichage choisi parmi "Classique", "Hebdomadaire", "Mensuel", "Journée spécifique"
    """
    mode = st.sidebar.selectbox(
        label = "Mode d'affichage",
        options = ["Classique",
                   "Hebdomadaire",
                   "Mensuel",
                   "Journée spécifique"],
        index = 0, 
        help = "Choisir le mode d'affichage pour visualiser la consommation et la production électrique :\n\n"
               "- **Classique** : sélectionnez une plage de dates et heures personnalisée.\n"
               "- **Hebdomadaire** : affichez les données agrégées par semaine, avec possibilité de sélectionner une ou plusieurs semaines spécifiques.\n"
               "- **Mensuel** : affichez les données agrégées par mois, avec possibilité de sélectionner un ou plusieurs mois spécifiques.\n"
               "- **Journée spécifique** : sélectionnez une date précise et une plage horaire pour analyser une journée particulière.")
    return mode


# ----------------------------------------------------------------------
# 📅 Sélection de période
# ----------------------------------------------------------------------

def select_period(display_mode: str, df: pd.DataFrame):
    """
    Gère dynamiquement la sélection de la période dans l'application
    Streamlit en fonction du mode d'affichage choisi par l'utilisateur.

    Paramètres :
        display_mode (str): Mode d'affichage choisi par l'utilisateur parmi :
                            - "Classique"
                            - "Hebdomadaire"
                            - "Mensuel"
                            - "Journée spécifique"
        df (pd.DataFrame): données fusionnées avec une colonne 'datetime'
                           pour extraire les bornes de dates disponibles

    Retour :
        tuple(datetime, datetime, list, str) :
            bornes de la période sélectionnée, liste des périodes sélectionnées (pour Hebdo/Mensuel), type de période (W/M)
    """

    min_date = df['datetime'].min().date()
    max_date = df['datetime'].max().date()

    # Valeurs par défaut
    selected_periods = None
    
    if display_mode == "Classique":
        # Sélection de deux dates + heures
        col_debut, col_fin = st.columns(2)
        with col_debut:
            # Date de début
            date_debut = st.date_input(
                label = "Date de début",
                value = min_date,
                min_value = min_date,
                max_value = max_date)
            heure_debut = pd.to_datetime(
                arg = "00:00").time()
        with col_fin:
            # Date de fin
            date_fin = st.date_input(
                label = "Date de fin",
                value = max_date,
                min_value = min_date,
                max_value = max_date)
            heure_fin = pd.to_datetime(
                arg = "23:59").time()
        datetime_debut = pd.to_datetime(
            arg = f"{date_debut} {heure_debut}")
        datetime_fin = pd.to_datetime(
            arg = f"{date_fin} {heure_fin}")
        return datetime_debut, datetime_fin, selected_periods

    elif display_mode == "Hebdomadaire":
        semaines = df['datetime'].dt.to_period(
            freq = "W").drop_duplicates().sort_values()
        options = ["Toutes"] + [str(s) for s in semaines]

        choix = st.selectbox(label = "Choisissez une semaine :", 
                             options = options, 
                             index = 0)

        if choix == "Toutes":
            datetime_debut = df['datetime'].min()
            datetime_fin = df['datetime'].max()
            selected_periods = semaines      # ← important !
        else:
            semaine = pd.Period(
                value = choix, 
                freq = "W")
            datetime_debut = semaine.start_time
            datetime_fin = semaine.end_time - pd.Timedelta(seconds=1)
            selected_periods = [semaine]

        return datetime_debut, datetime_fin, selected_periods

    elif display_mode == "Mensuel":
        mois = df['datetime'].dt.to_period(
            freq = "M").drop_duplicates().sort_values()
        options = ["Tous"] + [str(m) for m in mois]

        choix = st.selectbox(
            label = "Choisissez un mois :", 
            options = options, 
            index = 0)

        if choix == "Tous":
            datetime_debut = df['datetime'].min()
            datetime_fin = df['datetime'].max()
            selected_periods = [m.start_time for m in mois]
        else:
            per = pd.Period(
                value = choix, 
                freq = "M")
            datetime_debut = per.start_time
            datetime_fin = per.end_time - pd.Timedelta(seconds=1)
            selected_periods = [per.start_time]
        return datetime_debut, datetime_fin, selected_periods
    
    elif display_mode == "Journée spécifique":
        # Widgets de date et heures sur la même ligne
        col_date, col_hdeb, col_hfin = st.columns(
            spec = 3)

        # Sélection d'une date + heures (même date pour début et fin)
        with col_date:
            date = st.date_input(
                label = "Date à analyser",
                value = min_date,
                min_value = min_date,
                max_value = max_date)
        with col_hdeb:
            heure_debut = st.time_input(
                label = "Heure de début",
                value = pd.to_datetime(
                    arg = "00:00").time(),
                key = "heure_debut_spec")
        with col_hfin:
            heure_fin = st.time_input(
                label = "Heure de fin",
                value = pd.to_datetime(
                    arg = "23:59").time(),
                key = "heure_fin_spec")

        # Détermination des dates selon le choix
        datetime_debut = pd.to_datetime(
            arg = f"{date} {heure_debut}")
        datetime_fin = pd.to_datetime(
            arg = f"{date} {heure_fin}")
        return datetime_debut, datetime_fin, selected_periods

    else:
        st.error(body = "Mode d'affichage non reconnu.")
        return None, None, None, None

# ----------------------------------------------------------------------
# 📊 Choix du type de graphique
# ----------------------------------------------------------------------

def select_chart_type() -> str:
    """
    Permet à l'utilisateur de choisir le type de représentation graphique :
    - Courbe (time series)
    - Histogramme (barres)
    """
    chart_type = st.sidebar.selectbox(
        label = "Type de graphique",
        options = ["Courbe", "Histogramme"],
        index = 0, 
        help = "Choisir entre une courbe temporelle classique ou un histogramme à barres pour visualiser la consommation et la production électrique.")
    return chart_type
