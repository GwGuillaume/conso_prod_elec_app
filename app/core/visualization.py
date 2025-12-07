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
from app.core.localization import format_date_fr


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
        ) -> go.Scatter:
    """
    Crée une trace time-series (plotly.graph_objects.Scatter) standardisée.

    Paramètres
    ----------
    x : Iterable
        Valeurs d'axe X (horodatages).
    y : Iterable
        Valeurs d'axe Y.
    name : str
        Nom de la trace (légende).
    mode : str
        Mode d'affichage ('lines', 'markers', 'lines+markers').
    yaxis : Optional[str]
        Si 'y2', associe la trace à l'axe droit.
    visible : bool
        Visible par défaut dans la légende.
    hovertemplate : Optional[str]
        Template d'affichage au survol (Plotly).
    customdata : Iterable
        Custom fields
    line_dash : Optional[str]
        Style de ligne ('dash', 'dot', etc.).
    line_width : int
        Epaisseur de la ligne.

    Retour
    ------
    go.Scatter
        Trace prête à être ajoutée à une figure.
    """
    trace = go.Scatter(
        x=x,
        y=y,
        name=name,
        mode=mode,
        visible=visible,
        hovertemplate=hovertemplate,
        customdata=customdata,
        line=dict(dash=line_dash or "solid", width=line_width),
    )
    if yaxis:
        trace.update(yaxis=yaxis)
    return trace


# --------------------------------------------------
# Figure principale : production vs consommation
# --------------------------------------------------
def plot_production_vs_consumption(df: pd.DataFrame, mode: str = "Classique") -> go.Figure:
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
        Mode d'affichage (ex. "Classique", "Hebdomadaire", "Mensuel", "Journée spécifique").
        Influence le titre et l'agrégation éventuelle.

    Retour
    ------
    go.Figure
        Figure Plotly interactive.
    """
    if df.empty:
        return go.Figure()
    df_local = normalize_datetime_column(df, "datetime")
    df_local["datetime_fr"] = df_local["datetime"].apply(lambda d: format_date_fr(d, pattern="d MMMM y HH:mm"))

    fig = go.Figure()

    if "consommation" in df_local.columns:
        fig.add_trace(
            make_timeseries_trace(
                x=df_local["datetime"],
                y=df_local["consommation"],
                name="Consommation",
                hovertemplate="%{customdata}<br>Consommation : %{y:.0f}<extra></extra>",
                customdata=df_local["datetime_fr"],
                line_dash="solid",
                line_width=2))

    if "production" in df_local.columns:
        fig.add_trace(
            make_timeseries_trace(
                x=df_local["datetime"],
                y=df_local["production"],
                name="Production",
                hovertemplate="%{customdata}<br>Production : %{y:.0f}<extra></extra>",
                customdata=df_local["datetime_fr"],
                line_dash="dot",
                line_width=2))

    if "total" in df_local.columns and df_local["total"].notna().any():
        fig.add_trace(
            make_timeseries_trace(
                x=df_local["datetime"],
                y=df_local["total"],
                name="Total (prod + conso)",
                hovertemplate="%{customdata}<br>Total : %{y:.0f}<extra></extra>",
                customdata=df_local["datetime_fr"],
                line_dash="dash",
                line_width=3))

    title = f"Consommation vs Production — {mode}"
    fig.update_layout(
        template=PLOT_THEME if hasattr(PLOT_THEME, "__str__") else "plotly_white",
        title=dict(text=title, x=0.01, xanchor="left"),
        xaxis=dict(title="Date", showgrid=True,
                   rangeselector=dict(
                       buttons=list([
                           dict(count=1, label="1d", step="day", stepmode="backward"),
                           dict(count=7, label="7d", step="day", stepmode="backward"),
                           dict(count=30, label="30d", step="day", stepmode="backward"),
                           dict(step="all")
                       ])
                   ),
                   rangeslider=dict(visible=True)),
        yaxis=dict(title="Puissance / Energie", autorange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=60),
        hovermode="x unified"
        )

    return fig


# --------------------------------------------------
# Vue agrégée (hebdo / mensuelle) — optionnel
# --------------------------------------------------
def build_multi_period_figure(df: pd.DataFrame, freq: str = "W") -> go.Figure:
    """
    Construit une figure agrégée en sommant les données par période.
    - freq : 'W' pour hebdomadaire, 'ME' pour mensuel, 'D' pour jour

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame contenant 'datetime', 'production', 'consommation'
    freq : str
        Fréquence de rééchantillonnage ('D', 'W', 'ME')

    Retour
    ------
    go.Figure
    """
    if df.empty:
        return go.Figure()

    df_local = normalize_datetime_column(df, "datetime")
    # Indexation sur datetime
    df_local = df_local.set_index(df_local["datetime"])
    df_local["datetime_fr"] = df_local["datetime"].apply(lambda d: format_date_fr(d, pattern="d MMMM y HH:mm"))
    agg = df_local[["production", "consommation"]].resample(freq).sum(min_count=1).fillna(0)
    agg["total"] = agg["production"] + agg["consommation"]
    agg = agg.reset_index()

    if freq == "W":
        agg["period_fr"] = agg["datetime"].apply(
            lambda d: f"Semaine du {format_date_fr(d, 'd MMMM')} "
                      f"au {format_date_fr(d + pd.Timedelta(days=6), 'd MMMM y')}")
    else:
        agg["period_fr"] = agg["datetime"].apply(
            lambda d: f"Mois de {format_date_fr(d, 'LLLL y')}")

    fig = go.Figure()
    fig.add_trace(
        make_timeseries_trace(
            x=agg["datetime"],
            y=agg["consommation"],
            name="Consommation",
            hovertemplate="%{customdata}<br>Consommation: %{y:.0f}<extra></extra>",
            customdata=agg["period_fr"]))
    fig.add_trace(
        make_timeseries_trace(
            x=agg["datetime"],
            y=agg["production"],
            name="Production",
            hovertemplate="%{customdata}<br>Production: %{y:.0f}<extra></extra>",
            customdata=agg["period_fr"]))
    fig.add_trace(
        make_timeseries_trace(
            x=agg["datetime"],
            y=agg["total"],
            name="Total",
            hovertemplate="%{customdata}<br>Production: %{y:.0f}<extra></extra>",
            customdata=agg["period_fr"],
            line_width=3))

    freq_label = "W" if freq == "W" else "ME"
    fig.update_layout(
        template=PLOT_THEME if hasattr(PLOT_THEME, "__str__") else "plotly_white",
        title=f"Agrégation périodique ({freq_label})",
        xaxis_title="Période",
        yaxis_title="Énergie",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=0.01))
    return fig