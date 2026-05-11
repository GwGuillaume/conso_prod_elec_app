# -*- coding: utf-8 -*-
"""
app/core/visualization.py

Fonctions de visualisation (Plotly) pour l'application Streamlit.

Contenu :
- plot_production_vs_consumption : figure principale (conso / prod / total)
- make_timeseries_trace : utilitaire pour construire une trace temporelle
- build_multi_period_figure : helper pour vues agrégées (hebdo / mensuel)

Les DataFrame en entrée sont supposées contenir au minimum :
- une colonne 'datetime' de type datetime
- une colonne 'production' (W ou Wh suivant convention)
- une colonne 'consommation' (W ou Wh suivant convention)
- éventuellement une colonne 'total' = production + consommation

Toutes les fonctions renvoient un objet plotly.graph_objects.Figure.
"""

from typing import Iterable, Optional
import pandas as pd
import plotly.graph_objects as go
from .config import PLOT_THEME
from app.core.preprocessing import normalize_datetime_column
from common.plot_utils import create_time_series_plot, create_time_series_bar_plot


# --------------------------------------------------
# Utilitaires pour créer des traces
# --------------------------------------------------
def make_timeseries_trace(
        x: Iterable,
        y: Iterable,
        name: str,
        mode: str = "lines",
        yaxis: Optional[str] = None,
        visible: bool = True,
        hovertemplate: Optional[str] = None,
        customdata: Optional[Iterable] = None,
        line_dash: Optional[str] = None,
        line_width: int = 2,
        chart_type: str = "Courbe"
        ) -> go.Scatter | go.Bar:
    """
    Crée une trace Plotly standardisée pour séries temporelles.

    Selon le paramètre chart_type :
    - "Courbe"      → go.Scatter (ligne)
    - "Histogramme" → go.Bar (barres)

    Retour
    ------
    Trace Plotly prête à être ajoutée à une figure.
    """

    if chart_type == "Histogramme":
        # Largeur par défaut des barres temporelles (en ms)
        bar_width = 30 * 60 * 1000  # 30 minutes
        trace = go.Bar(
            x = x,
            y = y,
            name = name,
            visible = visible,
            hovertemplate = hovertemplate,
            customdata = customdata,
            width = bar_width
        )
    else:
        # Courbe par défaut
        trace = go.Scatter(
            x = x,
            y = y,
            name = name,
            mode = mode,
            visible = visible,
            hovertemplate = hovertemplate,
            customdata = customdata,
            line = dict(
                dash = line_dash or "solid", 
                width = line_width),
        )

    if yaxis:
        trace.update(
            yaxis = yaxis)

    return trace


# --------------------------------------------------
# Figure principale : production vs consommation
# --------------------------------------------------
def plot_production_vs_consumption(
        df: pd.DataFrame,
        mode: str = "Classique",
        chart_type: str = "Courbe"
    ) -> go.Figure:
    """
    Construit la figure principale affichant la consommation, la production
    et leur somme (total) selon le DataFrame fourni.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame contenant :
        - 'datetime' (datetime)
        - 'production' (numérique)
        - 'consommation' (numérique)
        - optionnellement 'total'
    mode : str
        Mode d'affichage ("Classique", "Hebdomadaire", "Mensuel" ou "Journée spécifique").
        Influence le titre et l'agrégation éventuelle.
    chart_type : str
        Type d'affichage (courbe ou histogramme)

    Retour
    ------
    go.Figure
        Figure Plotly interactive.
    """
    if df.empty:
        return go.Figure()
    df_local = normalize_datetime_column(
        df = df,
        col = "datetime")

    title = f"Consommation vs Production — {mode}"

    if chart_type == "Histogramme":
        fig = create_time_series_bar_plot(
            df = df_local, 
            title = title, 
            show_total = True
        )
    else:
        # Courbe temporelle classique
        fig = create_time_series_plot(
            df = df_local, 
            title = title, 
            show_total = True
        )

    # Application du thème et des options de navigation (slider, etc.)
    fig.update_layout(
        template = PLOT_THEME if hasattr(PLOT_THEME, "__str__") else "plotly_white",
    )

    # On n'ajoute le rangeselector et le slider que pour les séries temporelles
    if chart_type != "Histogramme":
        fig.update_layout(
            xaxis = dict(
            showgrid = True,
            rangeselector = dict(
                buttons = list([
                    dict(
                        count = 1, 
                        label = "1d", 
                        step = "day", 
                        stepmode = "backward"),
                    dict(
                        count = 7, 
                        label = "7d", 
                        step = "day", 
                        stepmode = "backward"),
                    dict(
                        count = 30, 
                        label = "30d", 
                        step = "day", 
                        stepmode = "backward"),
                    dict(
                        step = "all"
                    )
                ])
                   ),
                   rangeslider = dict(
                       visible = True))
        )

    return fig


# --------------------------------------------------
# Vue agrégée (hebdo / mensuelle) — optionnel
# --------------------------------------------------
def build_multi_period_figure(
        df: pd.DataFrame,
        freq: str = "W",
        chart_type: str = "Courbe"
    ) -> go.Figure:
    if df.empty:
        return go.Figure()

    df_local = normalize_datetime_column(
        df = df, 
        col = "datetime")
    
    df_local = df_local.set_index("datetime")
    agg = df_local[["production", "consommation"]].resample(
        rule = freq).sum(min_count = 1).fillna(0)
    agg["total"] = agg["production"] + agg["consommation"]
    agg = agg.reset_index()

    freq_label = "Hebdomadaire" if freq == "W" else "Mensuelle"
    title = f"Agrégation périodique ({freq_label})"

    if chart_type == "Histogramme":
        fig = create_time_series_bar_plot(
            df = agg,
            title = title,
            show_total = True
        )
    else:
        fig = create_time_series_plot(
            df = agg,
            title = title,
            show_total = True
        )

    fig.update_layout(
        template = PLOT_THEME if hasattr(PLOT_THEME, "__str__") else "plotly_white")

    return fig