# -*- coding: utf-8 -*-
"""
app/ui/layout.py

Disposition principale Streamlit :
- Sidebar (sélecteurs de mode, dates, options avancées)
- Contenu principal (graphique principal + détails horaires optionnels)
"""
from typing import List, Tuple

import streamlit as st
import pandas as pd

from app.ui.widgets import select_mode, select_period, select_chart_type
from app.core.visualization import plot_production_vs_consumption, build_multi_period_figure
from app.core.statistics import compute_basic_stats, get_summary_info
from app.core.periods import extract_periods
from app.core.localization import format_date_fr


def render_app(df: pd.DataFrame) -> None:
    """
    Rend l'application Streamlit avec la barre latérale et les graphiques principaux.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame fusionné contenant au minimum une colonne 'datetime'.
    """

    # --- Titre principal de l'application ---
    st.title(
        body = "📊 Analyse consommation & production électrique")

    # --- Sidebar : paramètres généraux ---
    st.sidebar.header(
        body = "⚙️ Paramètres d'affichage")

    # --- Sélection du mode d'affichage ---
    mode = select_mode()

    # --- Sélection du type de graphique (courbes, barres, etc.) ---
    chart_type = select_chart_type()

    # --- Sélection de la période principale (toujours deux bornes) ---
    if df.empty:
        st.warning(
            body = "Aucune donnée disponible à afficher.")
        return

    # --- Sélection de la période principale (toujours deux bornes) ---
    start_datetime, end_datetime, selected_periods = select_period(
        display_mode = mode, 
        df = df)

    # --- Filtrage de la période principale dans le DataFrame ---
    mask = ((df["datetime"] >= start_datetime) & 
            (df["datetime"] <= end_datetime))
    df_filtered = df.loc[mask].copy()

    # --- Options avancées (affichées seulement pour Hebdomadaire / Mensuel) ---
    show_detail = False
    selected_periods: List[pd.Timestamp] = []
    period_labels: List[str] = []
    period_list: pd.Series = pd.Series([], dtype = "datetime64[ns]")
    freq = None

    if mode in ["Hebdomadaire", "Mensuel"]:

        # Détermination du type de période pour les fonctions d'extraction et d'affichage
        freq = "W" if mode == "Hebdomadaire" else "M"

        # Extraction des périodes disponibles dans la plage sélectionnée pour alimenter les options avancées
        try:
            period_list, period_labels = extract_periods(
                df = df_filtered, 
                freq = freq)
        except Exception:
            # En cas d'erreur (p.ex. pas de colonne datetime valide), on garde les listes vides
            period_list = pd.Series(
                data = [], 
                dtype = "datetime64[ns]")
            period_labels = []

        # --- Affichage des options avancées dans la sidebar pour les modes Hebdo/Mensuel ---
        st.sidebar.markdown(
            body = "---")
        st.sidebar.subheader(
            body = "Options avancées")

        # Affichage conditionnel du multiselect pour les périodes si l'utilisateur choisit de voir les détails horaires
        choice = st.sidebar.selectbox(
            label = "Afficher le détail horaire pour :",
            options = ["Aucun", "Toutes les périodes", 
                     "Sélectionner des périodes"],
            index = 0)

        # Activation de l'affichage des détails horaires si l'utilisateur choisit une option autre que "Aucun"
        if choice != "Aucun":
            show_detail = True

        # Affichage du multiselect pour choisir les périodes spécifiques si l'utilisateur choisit cette option
        if choice == "Sélectionner des périodes":
            # Si aucune période disponible, afficher un message
            if len(period_list) == 0:
                st.sidebar.info(
                    body = "Aucune période disponible pour la plage sélectionnée.")
                selected_periods = []
            else:
                # multiselect avec format_func pour afficher des labels lisibles
                selected_periods = st.sidebar.multiselect(
                    label = "Choisissez une ou plusieurs périodes",
                    options = list(period_list),
                    format_func = lambda x: period_labels[list(period_list).index(x)])

    st.sidebar.markdown(body = "---")
    show_stats = st.sidebar.checkbox(
        label = "Afficher les statistiques", 
        value = True)

    # --- Informations et aide ---
    st.markdown(
        body = get_summary_info(df_filtered, mode))
    st.markdown(
        body = "⚙️ Cliquez sur la légende pour activer/désactiver les courbes.")

    # --- Figure principale selon le mode ---
    if mode == "Classique" or mode == "Journée spécifique":
        fig = plot_production_vs_consumption(
            df = df_filtered, 
            mode = mode, 
            chart_type = chart_type)
    elif mode == "Hebdomadaire" or mode == "Mensuel":
        fig = build_multi_period_figure(
            df = df_filtered, 
            freq = freq, 
            chart_type = chart_type)
    else:
        st.error(body = "Mode inconnu.")
        return

    # ID unique basé sur le mode + borne de dates (utile pour éviter le rerun inutile)
    chart_key = f"plot_{mode}_{start_datetime.strftime('%Y%m%d%H%M')}_{end_datetime.strftime(format = '%Y%m%d%H%M')}"
    st.plotly_chart(
        figure_or_data = fig, 
        width = 'content', 
        key = chart_key)

    # --- Affichage des détails horaires si demandé ---
    if show_detail:
        st.markdown(
            body = "## 🔎 Détails horaires")

        # Déterminer les cibles : toutes les périodes ou seulement les sélectionnées
        if choice == "Toutes les périodes":
            targets = period_list
        else:
            targets = selected_periods

        if len(targets) == 0:
            st.info(
                body = "Aucune période sélectionnée ou disponible pour afficher les détails.")
        else:
            # Pour chaque période cible, on affiche un sous-graphique horaire
            for p in targets:
                st.markdown(
                    body = "---")
                if freq == "W":
                    start_label = format_date_fr(
                        d = p, 
                        pattern = "d MMMM")
                    end_label = format_date_fr(
                        d = p + pd.offsets.Day(6), 
                        pattern = "d MMMM y")
                    title = f"Semaine du {start_label} au {end_label}"
                else:
                    title = f"Mois de {format_date_fr(
                        d = p, 
                        pattern = 'LLLL y')}"

                # Affichage du titre de la période
                st.markdown(
                    body = f"### {title}")

                # Filtrage des données pour la période courante
                df_period = df_filtered.copy()
                df_period["period"] = df_period["datetime"].dt.to_period(freq).apply(lambda r: r.start_time)
                df_period = df_period[df_period["period"] == p]

                # Si pas de données pour la période, afficher un message et passer à la suivante
                if df_period.empty:
                    st.warning(
                        body = "Aucune donnée horaire pour cette période.")
                    continue

                # affichage du détail horaire (graphe "Classique")
                fig_detail = plot_production_vs_consumption(
                    df = df_period, 
                    mode = "Detail")
                # Clé unique par période pour assurer l'état
                detail_key = f"detail_{mode}_{p.strftime('%Y%m%d')}"
                
                # Affichage du graphique pour la période courante
                st.plotly_chart(
                    figure_or_data = fig_detail, 
                    width = 'content', 
                    key = detail_key)

    # --- Statistiques basiques ---
    if show_stats:
        st.markdown(
            body = "### 📈 Statistiques sur la période sélectionnée")
        stats = compute_basic_stats(
            df = df_filtered)
        st.dataframe(
            data = stats, 
            width = 'content')
