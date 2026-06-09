# -*- coding: utf-8 -*-
"""
common/data_tools_OLD.py

Outils communs de manipulation des données de production et de consommation :
- Compléter un DataFrame pour avoir toutes les dates/horaires réguliers
- Fusionner les jeux de données conso/production
- Générer les informations générales de synthèse
"""

import os
from pathlib import Path
import pandas as pd


DEFAULT_PRICE_DATA_PATH = Path("data/conso/consumption_prices.csv")


def load_price_data(price_path: str | Path | None = None) -> pd.DataFrame | None:
    """Charge un fichier de prix de consommation si disponible."""
    resolved_path = Path(price_path) if price_path is not None else DEFAULT_PRICE_DATA_PATH
    if not resolved_path.exists():
        return None

    price_df = pd.read_csv(resolved_path, sep=";")
    if price_df.empty:
        return None

    datetime_col = None
    for candidate in ["datetime", "date", "timestamp", "time"]:
        if candidate in price_df.columns:
            datetime_col = candidate
            break

    if datetime_col is None:
        return None

    price_col = None
    for candidate in ["price_eur_per_kwh", "price_per_kwh", "price", "value", "cost"]:
        if candidate in price_df.columns:
            price_col = candidate
            break

    if price_col is None:
        return None

    normalized = price_df[[datetime_col, price_col]].copy()
    normalized.columns = ["datetime", "price_eur_per_kwh"]
    normalized["datetime"] = pd.to_datetime(normalized["datetime"], utc=False, errors="coerce")
    normalized = normalized.dropna(subset=["datetime", "price_eur_per_kwh"]).sort_values("datetime")
    return normalized.reset_index(drop=True)


# ---------------------- COMPLÉTION DES DATES MANQUANTES ---------------------- #
def complete_dataframe_datetimes(df: pd.DataFrame, min_freq: str) -> pd.DataFrame:
    """
    Complète un DataFrame pour qu'il contienne une ligne pour chaque horodatage régulier
    entre la première et la dernière date, à la fréquence spécifiée.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame d'entrée contenant une colonne 'datetime'.
    min_freq : str
        Fréquence temporelle à respecter entre chaque ligne. Exemple : '30min', '1H', etc.

    Retour :
    --------
    pd.DataFrame
        Nouveau DataFrame avec un datetime toutes les `min_freq` et des valeurs NaN remplies à 0.
    """

    # Assure que la colonne 'datetime' est au format datetime
    df["datetime"] = pd.to_datetime(
        arg = df["datetime"])
    
    # Assure que la colonne 'datetime' est indexée pour faciliter la réindexation
    df = df.set_index("datetime")

    # Génère un index complet de datetimes à la fréquence spécifiée
    full_index = pd.date_range(
        start = df.index.min(), 
        end = df.index.max(), 
        freq = min_freq)
    
    # Réindexation du DataFrame pour inclure toutes les dates/horaires et remplir les valeurs manquantes avec 0
    df_full = df.reindex(
        labels = full_index).fillna(value = 0).reset_index().rename(columns = {"index": "datetime"})

    return df_full.sort_values(by = "datetime")


# -------------------------- FUSION DES DONNÉES ------------------------------- #
def merge_conso_prod_data(
    conso_df_30min: pd.DataFrame,
    prod_df_30min: pd.DataFrame,
    price_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Fusionne les DataFrames de consommation et de production (agrégés sur 30 minutes)
    et calcule la colonne 'total'.

    Paramètres :
    ------------
    conso_df_30min : pd.DataFrame
        Données de consommation avec colonnes ['datetime', 'consommation'].
    prod_df_30min : pd.DataFrame
        Données de production avec colonnes ['datetime', 'production'].

    Retour :
    --------
    pd.DataFrame
        DataFrame fusionné contenant les colonnes ['datetime', 'consommation', 'production', 'total'].
    """

    conso_df_30min = conso_df_30min.copy()
    prod_df_30min = prod_df_30min.copy()
    conso_df_30min["datetime"] = pd.to_datetime(conso_df_30min["datetime"], errors="coerce")
    prod_df_30min["datetime"] = pd.to_datetime(prod_df_30min["datetime"], errors="coerce")

    # Fusion des deux DataFrames sur la colonne 'datetime' en utilisant une jointure interne
    merged_df = pd.merge(
        left = conso_df_30min, 
        right = prod_df_30min, 
        on = "datetime", 
        how = "inner")

    if price_df is not None:
        price_df = price_df.copy()
        price_df["datetime"] = pd.to_datetime(price_df["datetime"], errors="coerce")
        price_df = price_df.dropna(subset=["datetime"]).sort_values("datetime")
        price_df = price_df.set_index("datetime").resample("30min").ffill().reset_index()
        merged_df = pd.merge(
            left = merged_df,
            right = price_df[["datetime", "price_eur_per_kwh"]],
            on = "datetime",
            how = "left")
    else:
        merged_df["price_eur_per_kwh"] = pd.NA

    if "consommation" not in merged_df.columns and "consumption" in merged_df.columns:
        merged_df.rename(columns={"consumption": "consommation"}, inplace=True)
    if "production" not in merged_df.columns and "prod" in merged_df.columns:
        merged_df.rename(columns={"prod": "production"}, inplace=True)

    merged_df["total"] = merged_df["consommation"] + merged_df["production"]
    merged_df["consumption_cost_eur"] = (merged_df["consommation"] / 1000) * merged_df["price_eur_per_kwh"].fillna(0)
    merged_df["production_savings_eur"] = (merged_df["production"] / 1000) * merged_df["price_eur_per_kwh"].fillna(0)
    merged_df.fillna(
        value = 0, 
        inplace=True)

    output_path = os.path.join("data", "global.csv")
    merged_df.to_csv(
        path_or_buf = output_path, 
        sep = ";", 
        index = False)
    return merged_df


# ---------------------- INFOS GÉNÉRALES SUR LA PÉRIODE ---------------------- #
def print_general_info(
    display_mode: str,
    df: pd.DataFrame,
    mois_choisi: str | None = None,
    price_per_kwh: float | None = None,
) -> str:
    """
    Génère un texte descriptif des totaux et moyennes de consommation et de production.

    Paramètres :
    ------------
    display_mode : str
        Mode d’affichage sélectionné : "Classique", "Mensuel", "Hebdomadaire", etc.
    df : pd.DataFrame
        Données filtrées sur la période affichée.
    mois_choisi : str | None
        Mois ou période choisie (facultatif).

    Retour :
    --------
    str : Texte formaté prêt à afficher dans Streamlit.
    """

    def format_power(value: float) -> str:
        """Formate une puissance en W ou kW."""
        return f"{value/1000:,.2f} kW" if value >= 1000 else f"{value:,.0f} W"

    total_conso = df["consommation"].sum()
    total_prod = df["production"].sum()
    estimated_cost_eur = round(df["consumption_cost_eur"].sum() if "consumption_cost_eur" in df.columns else 0.0, 2)
    estimated_savings_eur = round(df["production_savings_eur"].sum() if "production_savings_eur" in df.columns else 0.0, 2)

    return f"""
**Informations générales sur la période :**

- 🔌 Consommation totale : **{format_power(
                                value = total_conso)}**
- 💶 Coût estimé de la consommation : **{estimated_cost_eur:,.2f} €**
- 🌿 Économies estimées grâce à la production : **{estimated_savings_eur:,.2f} €**
- 🌿 Production totale : **{format_power(
                                value = total_prod)}**
"""
