# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour la génération de graphiques Plotly.

Ce module centralise la logique de visualisation pour assurer la cohérence
et optimiser les performances, notamment sur les histogrammes volumineux.
"""

import plotly.graph_objects as go
import pandas as pd

def create_time_series_plot(
    df: pd.DataFrame, 
    title: str = "Analyse Temporelle",
    show_total: bool = True) -> go.Figure:
    """
    Génère un graphique de type courbes (Scatter) pour visualiser l'évolution
    temporelle de la consommation et de la production.

    Paramètres :
    ------------
    df : pd.DataFrame
        Données contenant au moins 'datetime' et l'une des colonnes ['consommation', 'production'].
    show_total : bool
        Si True, affiche également la courbe 'total' (somme prod + conso).
    title : str
        Titre du graphique.

    Retour :
    --------
    go.Figure
        Objet figure Plotly prêt à être affiché.
    """
    fig = go.Figure()

    # Tracé de la consommation
    if "consommation" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df["consommation"],
            name="Consommation (W)",
            line=dict(color="#EF553B", width=2),
            hovertemplate="Consommation: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))

    # Tracé de la production
    if "production" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df["production"],
            name="Production (W)",
            line=dict(color="#00CC96", width=2),
            hovertemplate="Production: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))
    
    # Tracé du total
    if show_total and "total" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df["total"],
            name="Total (W)",
            line=dict(color="#636EFA", width=2, dash="dot"),
            hovertemplate="Total: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Puissance / Énergie",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

def create_time_series_bar_plot(
    df: pd.DataFrame,
    title: str = "Analyse Temporelle (Barres)",
    show_total: bool = True) -> go.Figure:
    """
    Génère un graphique de type barres (Histogramme temporel) pour visualiser 
    l'évolution de la consommation et de la production dans le temps.

    Paramètres :
    ------------
    df : pd.DataFrame
        Données contenant 'datetime' et les colonnes de puissance.
    show_total : bool
        Si True, affiche également les barres pour le 'total'.
    title : str
        Titre du graphique.

    Retour :
    --------
    go.Figure
        Objet figure Plotly (barres temporelles).
    """
    fig = go.Figure()

    # Tracé de la consommation
    if "consommation" in df.columns:
        fig.add_trace(go.Bar(
            x=df["datetime"],
            y=df["consommation"],
            name="Consommation (W)",
            marker_color="#EF553B",
            hovertemplate="Consommation: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))

    # Tracé de la production
    if "production" in df.columns:
        fig.add_trace(go.Bar(
            x=df["datetime"],
            y=df["production"],
            name="Production (W)",
            marker_color="#00CC96",
            hovertemplate="Production: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))

    # Tracé du total
    if show_total and "total" in df.columns:
        fig.add_trace(go.Bar(
            x=df["datetime"],
            y=df["total"],
            name="Total (W)",
            marker_color="#636EFA",
            hovertemplate="Total: %{y:.0f} W<br>Date: %{x}<extra></extra>"
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Puissance / Énergie",
        barmode='group',
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig
