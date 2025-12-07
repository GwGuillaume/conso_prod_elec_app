# -*- coding: utf-8 -*-
"""
app/core/preprocessing.py

Fonctions utilitaires pour valider et préparer les DataFrame
avant les visualisations ou calculs.
"""

import pandas as pd


def normalize_datetime_column(df: pd.DataFrame, col: str = "datetime") -> pd.DataFrame:
    """
    Convertit la colonne datetime en type datetime64 et renvoie un DataFrame propre.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame source
    col : str
        Nom de la colonne datetime

    Retour
    ------
    pd.DataFrame
        DataFrame avec colonne datetime normalisée.
    """
    df = df.copy()
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vérifie la présence des colonnes nécessaires ('production', 'consommation', 'total').
    Génère 'total' si absent.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame source

    Retour
    ------
    pd.DataFrame
        DataFrame garanti avec:
        - 'production'
        - 'consommation'
        - 'total'
    """
    df = df.copy()

    # Si les colonnes n'existent pas, les créer à zéro
    if "production" not in df.columns:
        df["production"] = 0

    if "consommation" not in df.columns:
        df["consommation"] = 0

    # Génération du total si absent
    if "total" not in df.columns:
        df["total"] = df["production"] + df["consommation"]

    return df
