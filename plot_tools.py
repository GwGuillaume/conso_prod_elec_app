import pandas as pd
import plotly.graph_objects as go


# ---------------------------- GRAPHIQUE INTERACTIF ----------------------------- #
def plot_production_vs_consumption(merged_df:pd.DataFrame):
    """
    Crée un graphique interactif comparant la consommation, la production et la
    somme des deux (total) en fonction du temps, à partir d'un DataFrame.

    Paramètres :
    -----------
    merged_df : pd.DataFrame
        DataFrame contenant au minimum les colonnes suivantes :
        - 'datetime' : horodatage (type datetime)
        - 'consommation' : consommation en watts
        - 'production' : production en watts
        - 'total' : somme consommation + production

    Retour :
    --------
    fig : plotly.graph_objects.Figure
        Graphique interactif avec les courbes de consommation, de production et
        totale.
    """

    # Création de la figure
    fig = go.Figure()

    # Ajout de la courbe de consommation
    fig.add_trace(go.Scatter(
        x=merged_df["datetime"],
        y=merged_df["consommation"],
        mode="lines",
        name="Consommation",
        line=dict(color="rgba(255, 0, 0, 0.4)"), # Rouge semi-transparent
        fill='tozeroy',
        hovertemplate='Consommation : %{y} W<extra></extra>'
    ))

    # Ajout de la courbe de production
    fig.add_trace(go.Scatter(
        x=merged_df["datetime"],
        y=merged_df["production"],
        mode="lines",
        name="Production",
        line=dict(color="rgba(0, 255, 0, 0.4)"), # Vert semi-transparent
        fill='tozeroy',
        hovertemplate='Production : %{y} W<extra></extra>'
    ))

    # Ajout de la courbe totale (consommation + production sur les mêmes
    # créneaux horaires)
    fig.add_trace(go.Scatter(
        x=merged_df["datetime"],
        y=merged_df["total"],
        mode="lines",
        name="Consommation + Production",
        line=dict(color="rgba(129, 180, 227, 0.3)"), # Bleu clair transparent
        fill='tozeroy',
        hovertemplate='Consommation + Production : %{y} W<extra></extra>'
    ))

    # Mise en forme du graphique
    fig.update_layout(
        # title="Consommation, Production et Total",
        xaxis_title="Date et heure",
        yaxis_title="Puissance (W)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h",
                    xanchor="center",
                    x=0.5,
                    yanchor="bottom",
                    y=-0.5
        )
    )

    return fig