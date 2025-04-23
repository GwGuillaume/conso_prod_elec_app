import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp


# ---------------------------- GRAPHIQUE INTERACTIF ----------------------------- #
def plot_production_vs_consumption(df: pd.DataFrame, mode_affichage: str):
    """
    Crée un graphique interactif comparant la consommation, la production et la somme des deux (total)
    en fonction du temps, pour différents modes d'affichage : Classique, Journée spécifique, Hebdomadaire, Mensuel.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame contenant au minimum les colonnes suivantes :
        - 'datetime' : horodatage (type datetime)
        - 'consommation' : consommation en watts
        - 'production' : production en watts
        - 'total' : somme consommation + production

    mode_affichage : str
        Mode d'affichage sélectionné parmi "Classique", "Journée spécifique", "Hebdomadaire" ou "Mensuel"

    Retour :
    --------
    fig : plotly.graph_objects.Figure
        Graphique interactif (simple ou multi-subplots selon le mode) avec les courbes de consommation, production et total.
    """

    if mode_affichage in ["Classique", "Journée spécifique"]:
        return _plot_single_figure(df)

    # Sinon, mode multi-subplots : Hebdomadaire ou Mensuel
    if mode_affichage == "Hebdomadaire":
        df["periode"] = df["datetime"].dt.to_period("W").apply(lambda r: r.start_time)
    elif mode_affichage == "Mensuel":
        df["periode"] = df["datetime"].dt.to_period("M").apply(lambda r: r.start_time)

    # Dataframe par péridoes
    periodes = df["periode"].drop_duplicates().sort_values()
    nb_subplots = len(periodes)

    # Titres des subplots
    if mode_affichage == "Hebdomadaire":
        subplot_titles = [
            f"Semaine du {p.strftime('%d %B')} au {(p + pd.offsets.Day(6)).strftime('%d %B %Y')}"
            for p in periodes]
    elif mode_affichage == "Mensuel":
        subplot_titles = [
            f"Mois de {p.strftime("%B %Y")}"
            for p in periodes]

    fig = sp.make_subplots(
        rows=nb_subplots,
        cols=1,
        shared_yaxes=True,
        vertical_spacing=0.1,  # Espacement vertical entre 2 subplots successifs
        subplot_titles=subplot_titles
    )

    for i, periode in enumerate(periodes):
        data_periode = df[df["periode"] == periode]
        _plot_subplot(data_periode,
                      fig=fig,
                      row=i+1,
                      col=1,
                      show_legend=(i==0))  # Légende seulement sur le 1er subplot

    # Mise en forme de la figure
    fig.update_layout(
        height=400 * nb_subplots,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", x=0.5, y=1.1, xanchor="center", yanchor="top"),
        showlegend=True
    )

    return fig

def _plot_single_figure(df: pd.DataFrame):
    """
    Crée une figure Plotly simple avec les courbes consommation, production et total.

    Paramètres :
    -----------
    df : pd.DataFrame
        Données à afficher

    Retour :
    --------
    fig : plotly.graph_objects.Figure
    """
    fig = go.Figure()
    _plot_subplot(df, fig=fig)

    # Mise en forme de la figure
    fig.update_layout(
        height=400,
        xaxis_title="Date et heure",
        yaxis_title="Puissance (W)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", x=0.5, y=1.3, xanchor="center", yanchor="top")
    )

    return fig

def _plot_subplot(df: pd.DataFrame, fig=None, row=None, col=None, show_legend=True):
    """
    Ajoute les courbes consommation, production et total à une figure Plotly (simple ou subplot).

    Paramètres :
    -----------
    df : pd.DataFrame
        Données à tracer
    fig : plotly.graph_objects.Figure
        Figure à modifier
    row : int
        Ligne du subplot (si subplot)
    col : int
        Colonne du subplot (si subplot)
    show_legend : bool
        Si True, affiche la légende pour ce subplot

    Retour :
    --------
    fig : plotly.graph_objects.Figure
    """
    add_trace_args = {"row": row, "col": col} if row and col else {}

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["consommation"],
        mode="lines",
        name="Consommation",
        line=dict(color="rgba(255, 0, 0, 0.4)"),
        fill='tozeroy',
        hovertemplate='Consommation : %{y} W<extra></extra>',
        showlegend=show_legend
    ), **add_trace_args)

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["production"],
        mode="lines",
        name="Production",
        line=dict(color="rgba(0, 255, 0, 0.4)"),
        fill='tozeroy',
        hovertemplate='Production : %{y} W<extra></extra>',
        showlegend=show_legend
    ), **add_trace_args)

    fig.add_trace(go.Scatter(
        x=df["datetime"],
        y=df["total"],
        mode="lines",
        name="Consommation + Production",
        line=dict(color="rgba(129, 180, 227, 0.3)"),
        fill='tozeroy',
        hovertemplate='Consommation + Production : %{y} W<extra></extra>',
        showlegend=show_legend
    ), **add_trace_args)

    return fig