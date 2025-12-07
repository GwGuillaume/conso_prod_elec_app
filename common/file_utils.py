# file_utils.py
# -*- coding: utf-8 -*-
"""
Fonctions utilitaires pour la gestion des fichiers JSON, CSV et ZIP.

Ces fonctions sont utilisées par les modules conso_api_tools et prod_api_tools
pour :
- sauvegarder des fichiers JSON,
- concaténer des données dans des CSV,
- gérer les archives ZIP.
"""

import zipfile
import pandas as pd
from pathlib import Path
from typing import List

# ------------------------------------------------------
# 📁 Gestion de dossiers et fichiers
# ------------------------------------------------------


# ------------------------------------------------------
# 🧾 Gestion des fichiers CSV
# ------------------------------------------------------

def append_dicts_to_csv(rows: list[dict], csv_path: Path):
    """
    Ajoute une liste de dictionnaires dans un fichier CSV.
    Crée le fichier et son en-tête s’il n’existe pas.

    Paramètres :
        rows (list[dict]) : données à ajouter
        csv_path (Path) : chemin du fichier CSV
    """
    if not rows:
        return

    df = pd.DataFrame(rows)
    if csv_path.exists():
        df.to_csv(csv_path, mode="a", index=False, header=False)
    else:
        df.to_csv(csv_path, index=False)
    print(f"🧾 Données ajoutées à {csv_path}")



def load_clean_data(csv_filepath: Path) -> pd.DataFrame:
    """
    Charge les données complètes de production ou de consommation
    (production_data.csv ou consumption_data.csv).

    Paramètre :
        csv_filepath : chemin vers le fichier CSV
                       (production_data.csv ou consumption_data.csv)

    Retour :
        DataFrame avec les colonnes 'datetime' (datetime)
        et 'production' ou 'consommation' (numérique)
    """
    if not csv_filepath.exists():
        raise FileNotFoundError(f"🚫 Le fichier {csv_filepath} est introuvable.")
    df = pd.read_csv(csv_filepath, sep=";")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    # conversion automatique des autres colonnes en numérique
    for col in df.columns:
        if col != "datetime":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("datetime").reset_index(drop=True)
    return df

# ------------------------------------------------------
# 🧹 Suppression de fichiers
# ------------------------------------------------------

def safe_delete(file_path: Path):
    """
    Supprime un fichier local s’il existe.

    Paramètre :
        file_path (Path) : chemin du fichier à supprimer
    """
    try:
        file_path.unlink(missing_ok=True)
        print(f"🧹 Fichier supprimé : {file_path}")
    except Exception as e:
        print(f"⚠️ Impossible de supprimer {file_path} : {e}")
