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

    st.title(body="📊 Analyse consommation & production électrique")

    # --- Sidebar : paramètres généraux ---
    st.sidebar.header(body="⚙️ Paramètres d'affichage")

    mode = select_mode()
    chart_type = select_chart_type()

    # --- Sélection de la période principale (toujours deux bornes) ---
    if df.empty:
        st.warning(body="Aucune donnée disponible à afficher.")
        return

    start_datetime, end_datetime, selected_periods, period_type = select_period(mode, df)

    # Filtrage de la période principale
    mask = ((df["datetime"] >= start_datetime) & (df["datetime"] <= end_datetime))
    df_filtered = df.loc[mask].copy()

    # --- Options avancées (affichées seulement pour Hebdomadaire / Mensuel) ---
    show_detail = False
    selected_periods: List[pd.Timestamp] = []
    period_labels: List[str] = []
    period_list: pd.Series = pd.Series([], dtype="datetime64[ns]")  # valeur par défaut sûre
    freq = None

    if mode in ["Hebdomadaire", "Mensuel"]:
        freq = "W" if mode == "Hebdomadaire" else "M"

        # extract_periods renvoie (period_list, labels) avec labels en français (via Babel)
        try:
            period_list, period_labels = extract_periods(df_filtered, freq)
        except Exception:
            # En cas d'erreur (p.ex. pas de colonne datetime valide), on garde les listes vides
            period_list = pd.Series([], dtype="datetime64[ns]")
            period_labels = []

        st.sidebar.markdown(body="---")
        st.sidebar.subheader("Options avancées")

        # choix d'affichage des détails horaires
        choice = st.sidebar.selectbox(
            label="Afficher le détail horaire pour :",
            options=["Aucun", "Toutes les périodes", "Sélectionner des périodes"],
            index=0
        )

        if choice != "Aucun":
            show_detail = True

        # multiselect : on afffiche les labels en français tout en conservant les valeurs réelles
        if choice == "Sélectionner des périodes":
            # si aucune période disponible, afficher un message
            if len(period_list) == 0:
                st.sidebar.info("Aucune période disponible pour la plage sélectionnée.")
                selected_periods = []
            else:
                # multiselect avec format_func pour afficher des labels lisibles
                selected_periods = st.sidebar.multiselect(
                    label="Choisissez une ou plusieurs périodes",
                    options=list(period_list),
                    format_func=lambda x: period_labels[list(period_list).index(x)],
                )

    st.sidebar.markdown(body="---")
    show_stats = st.sidebar.checkbox(label="Afficher les statistiques", value=True)

    # --- Informations et aide ---
    st.markdown(body=get_summary_info(df_filtered, mode))
    st.markdown(body="⚙️ Cliquez sur la légende pour activer/désactiver les courbes.")

    # --- Figure principale selon le mode ---
    if mode == "Classique" or mode == "Journée spécifique":
        fig = plot_production_vs_consumption(df=df_filtered, mode=mode, chart_type=chart_type)
    elif mode == "Hebdomadaire" or mode == "Mensuel":
        fig = build_multi_period_figure(df=df_filtered, freq=freq, chart_type=chart_type)
    else:
        st.error(body="Mode inconnu.")
        return

    # ID unique basé sur le mode + borne de dates (utile pour éviter le rerun inutile)
    chart_key = f"plot_{mode}_{start_datetime.strftime('%Y%m%d%H%M')}_{end_datetime.strftime('%Y%m%d%H%M')}"
    st.plotly_chart(figure_or_data=fig, width='content', key=chart_key)

    # --- Affichage des détails horaires si demandé ---
    if show_detail:
        st.markdown("## 🔎 Détails horaires")

        # Déterminer les cibles : toutes les périodes ou seulement les sélectionnées
        if choice == "Toutes les périodes":
            targets = period_list
        else:
            targets = selected_periods

        if len(targets) == 0:
            st.info("Aucune période sélectionnée ou disponible pour afficher les détails.")
        else:
            # Pour chaque période cible, on affiche un sous-graphique horaire
            for p in targets:
                st.markdown("---")
                if freq == "W":
                    start_label = format_date_fr(p, pattern="d MMMM")
                    end_label = format_date_fr(p + pd.offsets.Day(6), pattern="d MMMM y")
                    title = f"Semaine du {start_label} au {end_label}"
                else:
                    title = f"Mois de {format_date_fr(p, pattern='LLLL y')}"

                st.markdown(f"### {title}")

                # filtrer les données pour la période courante
                df_period = df_filtered.copy()
                df_period["period"] = df_period["datetime"].dt.to_period(freq).apply(lambda r: r.start_time)
                df_period = df_period[df_period["period"] == p]

                # si pas de données pour la période, on informe l'utilisateur
                if df_period.empty:
                    st.warning("Aucune donnée horaire pour cette période.")
                    continue

                # affichage du détail horaire (graphe "Classique")
                fig_detail = plot_production_vs_consumption(df_period, mode="Detail")
                # clé unique par période pour assurer l'état
                detail_key = f"detail_{mode}_{p.strftime('%Y%m%d')}"
                st.plotly_chart(fig_detail, width='content', key=detail_key)

    # --- Statistiques basiques ---
    if show_stats:
        st.markdown(body="### 📈 Statistiques sur la période sélectionnée")
        stats = compute_basic_stats(df=df_filtered)
        st.dataframe(data=stats, width='content')
