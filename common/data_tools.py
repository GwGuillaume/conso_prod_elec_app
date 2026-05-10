# -*- coding: utf-8 -*-
"""
common/data_tools_OLD.py

Outils communs de manipulation des données de production et de consommation :
- Compléter un DataFrame pour avoir toutes les dates/horaires réguliers
- Fusionner les jeux de données conso/production
- Générer les informations générales de synthèse
"""

import os
import pandas as pd


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
def merge_conso_prod_data(conso_df_30min: pd.DataFrame, prod_df_30min: pd.DataFrame) -> pd.DataFrame:
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

    # Fusion des deux DataFrames sur la colonne 'datetime' en utilisant une jointure interne
    merged_df = pd.merge(
        left = conso_df_30min, 
        right = prod_df_30min, 
        on = "datetime", 
        how = "inner")
    merged_df["total"] = merged_df["consommation"] + merged_df["production"]
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
def print_general_info(display_mode: str, df: pd.DataFrame, mois_choisi: str | None = None) -> str:
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

    return f"""
**Informations générales sur la période :**

- 🔌 Consommation totale : **{format_power(
                                value = total_conso)}**
- 🌿 Production totale : **{format_power(
                                value = total_prod)}**
"""
