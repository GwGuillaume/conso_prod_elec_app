import pandas as pd
from babel.dates import format_date

def extract_periods(df: pd.DataFrame, freq: str):
    """
    Extrait les périodes hebdomadaires ou mensuelles et génère des labels
    formatés en français pour l'affichage.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame contenant une colonne 'datetime'.
    freq : str
        Fréquence : "W" pour hebdo, "M" pour mensuel.

    Retour
    ------
    tuple (period_list, labels)
        - period_list : dates représentant le début de chaque période
        - labels : libellés textuels en français
    """

    if freq == "W":
        # Extraction du début de la semaine
        df["period"] = df["datetime"].dt.to_period(
            freq = "W").apply(lambda r: r.start_time)
        period_list = df["period"].drop_duplicates().sort_values()

        # Labels : "Semaine du 12 mars au 18 mars 2025"
        labels = [
            f"Semaine du {format_date(
                date = p, 
                format = 'd MMMM', 
                locale = 'fr_FR')} au "
            f"{format_date(
                date = p + pd.offsets.Day(n = 6), 
                format = 'd MMMM y', 
                locale='fr_FR')}"
            for p in period_list
        ]

    elif freq == "M":
        # Extraction du premier jour du mois
        df["period"] = df["datetime"].dt.to_period(
            freq = "M").apply(lambda r: r.start_time)
        period_list = df["period"].drop_duplicates().sort_values()
        labels = [f"Mois de {format_date(
            date = p, 
            format = 'LLLL y', 
            locale = 'fr_FR')}" for p in period_list]

    else:
        raise ValueError("Fréquence non supportée (W ou M uniquement).")

    return period_list, labels
