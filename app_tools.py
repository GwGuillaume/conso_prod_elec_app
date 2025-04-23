import streamlit as st
import pandas as pd


# ------------------------ CHOIX DE LA PÉRIODE D'ANALYSE ------------------------ #
def period_choice(display_mode: str, df: pd.DataFrame):
    """
    Affiche les sélecteurs de période dans l'application Streamlit en fonction du
    mode d'affichage choisi par l'utilisateur.

    Paramètres :
    ------------
    display_mode : str
        Mode d'affichage choisi par l'utilisateur parmi :
        - "Classique"
        - "Hebdomadaire"
        - "Mensuel"
        - "Journée spécifique"

    df : pd.DataFrame
        DataFrame contenant une colonne 'datetime' pour extraire les bornes de dates disponibles.

    Retour :
    --------
    Tuple (datetime_debut, datetime_fin) correspondant à la période sélectionnée.
    """

    min_date = df['datetime'].min().date()
    max_date = df['datetime'].max().date()

    if display_mode == "Classique":
        # Sélection de deux dates + heures
        col_debut, col_fin = st.columns(2)
        with col_debut:
            date_debut = st.date_input("Date de début", value=min_date, min_value=min_date, max_value=max_date)
            heure_debut = pd.to_datetime("00:00").time()    # st.time_input("Heure de début", value=pd.to_datetime("00:00").time(), key="heure_debut")
        with col_fin:
            date_fin = st.date_input("Date de fin", value=max_date, min_value=min_date, max_value=max_date)
            heure_fin = pd.to_datetime("23:59").time()  # st.time_input("Heure de fin", value=pd.to_datetime("23:59").time(), key="heure_fin")

        datetime_debut = pd.to_datetime(f"{date_debut} {heure_debut}")
        datetime_fin = pd.to_datetime(f"{date_fin} {heure_fin}")

    elif display_mode == "Hebdomadaire":
        # Récupération des semaines disponibles dans les données
        semaines_disponibles = df['datetime'].dt.to_period("W").drop_duplicates().sort_values()

        # Création de la liste d'options avec "Toutes" en premier
        options_semaines = ["Toutes"] + [str(s) for s in semaines_disponibles]

        # Sélecteur de semaine avec "Toutes" sélectionnée par défaut
        semaine_choisie = st.selectbox("Choisissez une semaine :", options=options_semaines, index=0)

        # Détermination des dates selon le choix
        if semaine_choisie == "Toutes":
            datetime_debut = df['datetime'].min()
            datetime_fin = df['datetime'].max()
        else:
            semaine = pd.Period(semaine_choisie, freq="W")
            datetime_debut = semaine.start_time
            datetime_fin = semaine.end_time - pd.Timedelta(seconds=1)

    elif display_mode == "Mensuel":
        # Récupération des mois disponibles
        mois_disponibles = df['datetime'].dt.to_period("M").drop_duplicates().sort_values()

        # Création de la liste d'options avec "Tous" en premier
        options_mois = ["Tous"] + [str(m) for m in mois_disponibles]

        # Sélecteur de mois avec "Tous" sélectionné par défaut
        mois_choisi = st.selectbox("Choisissez un mois :", options=options_mois, index=0)

        # Détermination des dates selon le choix
        if mois_choisi == "Tous":
            datetime_debut = df['datetime'].min()
            datetime_fin = df['datetime'].max()
        else:
            mois = pd.Period(mois_choisi, freq="M")
            datetime_debut = mois.start_time
            datetime_fin = mois.end_time - pd.Timedelta(seconds=1)

    elif display_mode == "Journée spécifique":
        # Widgets de date et heures sur la même ligne
        col_date, col_hdeb, col_hfin = st.columns(3)

        # Sélection d'une date + heures (même date pour début et fin)
        with col_date:
            date = st.date_input("Date à analyser", value=min_date, min_value=min_date, max_value=max_date)
        with col_hdeb:
            heure_debut = st.time_input("Heure de début", value=pd.to_datetime("00:00").time(), key="heure_debut_spec")
        with col_hfin:
            heure_fin = st.time_input("Heure de fin", value=pd.to_datetime("23:59").time(), key="heure_fin_spec")

        # Détermination des dates selon le choix
        datetime_debut = pd.to_datetime(f"{date} {heure_debut}")
        datetime_fin = pd.to_datetime(f"{date} {heure_fin}")

    else:
        st.error("Mode d'affichage non reconnu.")
        return None, None

    return datetime_debut, datetime_fin