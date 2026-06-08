# utils.py
# -*- coding: utf-8 -*-
"""
Fonctions utilitaires générales (dates, formats, logs, etc.).
"""

from datetime import datetime, timedelta, time
from pathlib import Path
import pandas as pd
import zipfile
import shutil
import json

# ------------------------------------------------------
# ⏰ Gestion des dates
# ------------------------------------------------------

def format_date_to_str(date_obj: datetime) -> str:
    """
    Formate un datetime en chaîne 'YYYY-MM-DD'.

    Paramètre :
        date_obj (datetime) : objet datetime

    Retour :
        str : date formatée
    """
    return date_obj.date().strftime("%Y-%m-%d")

def format_str_to_date(date_str: str) -> datetime:
    """
    Formate un string de date au format 'YYYY-MM-DD' en datetime.

    Paramètre :
        date_str (str) : date au format 'YYYY-MM-DD'

    Retour :
        datetime : date formatée
    """
    return datetime.strptime(date_str, "%Y-%m-%d")

def yesterday() -> datetime:
    """
    Retourne la date d'hier.

    Retour :
        date_obj (datetime) : date d'hier
    """
    today = datetime.now().date()
    yesterday_date = today - timedelta(days = 1)
    yesterday_time = time(
        hour = 0, 
        minute = 0)
    return datetime.combine(
        date = yesterday_date, 
        time = yesterday_time)

def next_day(current_day: datetime) -> datetime:
    """
    Retourne la date du jour suivant.

    Paramètre :
        current_day (datetime) : date courante 'YYYY-MM-DD'

    Retour :
        date_obj (datetime) : date du jour suivant
    """
    return current_day + timedelta(days=1)

# ------------------------------------------------------
# 🧾 Gestion générique de logs et chemins
# ------------------------------------------------------

def print_section(title: str):
    """
    Affiche une section lisible dans la console.
    """
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def resolve_path(base: Path, sub: str | Path) -> Path:
    """
    Résout un chemin relatif à un répertoire de base.

    Paramètres :
        base (Path) : dossier racine
        sub (str | Path) : sous-chemin

    Retour :
        Path : chemin absolu combiné
    """
    return base / sub

# ------------------------------------------------------
# 📁 Gestion de dossiers et fichiers
# ------------------------------------------------------

def ensure_folder(folder_path: str | Path):
    """
    Crée le dossier spécifié s’il n’existe pas.

    Paramètre :
        folder_path (str | Path) : chemin du dossier à créer
    """
    path = Path(folder_path)
    path.mkdir(
        parents = True, 
        exist_ok = True)
    return path

def cleanup_folders(folder_paths: list):
    """
    Supprime le dossier spécifié.

    Paramètre :
        folder_paths (list) : liste des chemins des dossiers à supprimer
    """
    for folder in folder_paths:
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
            print(f"\n🧹 Dossier temporaire supprimé : {folder}")

def save_json(data: dict, date_str: str, interval_folder: str) -> Path:
    """
    Sauvegarde un dictionnaire JSON dans le dossier approprié.

    Paramètres :
        data (dict) : données JSON à sauvegarder
        date_str (str) : date au format 'YYYY-MM-DD'
        interval_folder (str) : chemin vers le dossier de stockage
                                (FOLDER_1H ou FOLDER_30MIN)

    Retour :
        Path : chemin complet du fichier sauvegardé
    """
    ensure_folder(
        folder_path = interval_folder)
    file_path = Path(interval_folder) / f"conso_{date_str}.json"
    with open(
        file = file_path, 
        mode = "w", 
        encoding = "utf-8") as f:
        json.dump(
            obj = data, 
            fp = f, 
            ensure_ascii = False, 
            indent = 2)
    return file_path

def clean_csv_columns(source_csv: Path, columns_map: dict) -> Path:
    """
    Nettoie et renomme des colonnes d'un fichier CSV en fonction d'un mapping fourni,
    puis remplace directement le fichier CSV original par la version nettoyée.

    Cette fonction :
    - charge un fichier CSV,
    - vérifie la présence des colonnes spécifiées dans le dictionnaire de mapping,
    - extrait uniquement ces colonnes,
    - renomme les colonnes selon le mapping,
    - écrase le fichier d'entrée avec le CSV nettoyé (séparateur ;),
    - retourne le chemin du fichier CSV modifié.

    Paramètres
    ----------
    source_csv : Path
        Chemin du fichier CSV source (sera écrasé).

    columns_map : dict
        Dictionnaire {ancien_nom: nouveau_nom}
        Exemple : {"Time": "datetime", "Production (W)": "production"}

    Retour
    ------
    Path
        Chemin du fichier CSV nettoyé (identique à l'entrée).
    """

    # Lecture du CSV original
    df = pd.read_csv(
        filepath_or_buffer = source_csv)

    # Validation des colonnes
    missing = [col for col in columns_map.keys() if col not in df.columns]
    if missing:
        raise RuntimeError(
            f"Colonnes manquantes dans le fichier CSV : {missing}"
        )

    # Sélection et renommage
    df_clean = df[list(columns_map.keys())].rename(columns = columns_map)

    # Écrasement du fichier source
    df_clean.to_csv(
        filepath_or_buf = source_csv, 
        sep = ";", 
        index = False)

    return source_csv


def append_csvs_with_resampling(csv_paths: list[Path],
                                csv_30min: Path,
                                csv_1h: Path):
    """
    Ajoute plusieurs CSV bruts et met à jour uniquement
    les fichiers resamplés 30 min et 1h par concaténation.

    Paramètres
    ----------
    csv_paths : list[Path]
        Liste des chemins des fichiers CSV à ajouter.
        Chaque CSV doit contenir au minimum :
        - datetime : horodatage
        - production : valeur numérique
    csv_30min : Path
        Chemin du fichier contenant les données moyennées toutes les 30 minutes.
    csv_1h : Path
        Chemin du fichier contenant les données moyennées toutes les 60 minutes.

    Retour
    ------
    None
    """

    # -----------------------------------------------------------
    # 1) Charger les nouveaux CSV bruts
    # -----------------------------------------------------------
    dfs = []
    for p in csv_paths:
        df = pd.read_csv(
            filepath_or_buffer = p, 
            sep = ";")
        df["datetime"] = pd.to_datetime(
                                arg = df["datetime"])
        dfs.append(
            object = df)

    df_new = pd.concat(
        objs = dfs, 
        ignore_index = True)
    df_new = df_new.set_index("datetime").sort_index()

    # -----------------------------------------------------------
    # 2) Resampling des nouvelles données
    # -----------------------------------------------------------
    df_new_30min = (
        df_new.resample("30min")
        .mean(numeric_only = True)
        .dropna()
    )

    df_new_1h = (
        df_new.resample("1h")
        .mean(numeric_only = True)
        .dropna()
    )
    df_new_1h = df_new_1h[df_new_1h.index.minute == 0]

    # -----------------------------------------------------------
    # 3) Charger l'existant et concaténer
    # -----------------------------------------------------------

    # ---- 30 min ----
    if csv_30min.exists():
        df_old_30 = pd.read_csv(
            filepath_or_buffer = csv_30min, 
            sep = ";", 
            parse_dates = ["datetime"])
        df_old_30 = df_old_30.set_index("datetime")
        df_30 = pd.concat(
            objs = [df_old_30, df_new_30min], 
            ignore_index = True)
        df_30 = df_30[~df_30.index.duplicated(keep = 'last')]  # supprime doublons
        df_30 = df_30.sort_index()
    else:
        df_30 = df_new_30min

    # ---- 1 heure ----
    if csv_1h.exists():
        df_old_1h = pd.read_csv(
            filepath_or_buffer = csv_1h, 
            sep = ";", 
            parse_dates = ["datetime"])
        df_old_1h = df_old_1h.set_index("datetime")
        df_1h_final = pd.concat(
            objs = [df_old_1h, df_new_1h], 
            ignore_index = True)
        df_1h_final = df_1h_final[~df_1h_final.index.duplicated(keep = 'last')]
        df_1h_final = df_1h_final.sort_index()
    else:
        df_1h_final = df_new_1h

    # -----------------------------------------------------------
    # 4) Sauvegarde finale
    # -----------------------------------------------------------
    df_30.to_csv(
        path_or_buf = csv_30min, 
        sep = ";", 
        index_label = "datetime")
    df_1h_final.to_csv(
        path_or_buf = csv_1h, 
        sep = ";", 
        index_label = "datetime")

    print(f"⏱️ Mise à jour du fichier 30 minutes : {csv_30min}")
    print(f"⏱️ Mise à jour du fichier 1 heure : {csv_1h}")


def append_csvs_to_clean_csv(csv_paths: list[Path], clean_csv: Path):
    """
    Concatène plusieurs CSV en un fichier CSV unique (clean_csv).
    Crée clean_csv si inexistant.

    Paramètres :
        csv_paths : liste de chemins vers les CSV à ajouter
        clean_csv : chemin du CSV de sortie

    Retour :
        None
    """
    dfs = []
    for p in csv_paths:
        dfs.append(pd.read_csv(
            filepath_or_buffer = p, 
            sep = ";"))
    df_all = pd.concat(
        objs = dfs, 
        ignore_index = True)

    if clean_csv.exists():
        df_existing = pd.read_csv(
            filepath_or_buffer = clean_csv, 
            sep = ";")
        df_all = pd.concat(
            objs = [df_existing, df_all], 
            ignore_index = True)

    df_all.to_csv(
        path_or_buf = clean_csv, 
        index = False)
    print(f"🧾 Données ajoutées à {clean_csv}")


def resampled_data_exists_for_date(target_date: datetime,
                                   csv_30min: Path,
                                   csv_1h: Path) -> bool:
    """
    Vérifie si les données resamplées (30 min et 1h) existent déjà
    pour la journée target_date dans les fichiers csv_30min et csv_1h.

    Règles :
    - 30 min : il doit exister au moins les 24 timestamps horaires (HH:00)
    - 1h : les 24 timestamps horaires doivent exister (HH:00)

    Paramètres
    ----------
    target_date : datetime
        La date à vérifier
    csv_30min : Path
        Chemin du fichier CSV contenant les données resamplées 30 min
    csv_1h : Path
        Chemin du fichier CSV contenant les données resamplées 1h

    Retour
    ------
    bool
        True si les données existent déjà, False sinon
    """

    day_start = datetime.combine(
        date = target_date.date(), 
        time = datetime.min.time())
    expected_hours = [day_start + timedelta(
                                    hours = h) for h in range(24)]

    # -----------------------------------------------------------
    # Vérification fichier 1h
    # -----------------------------------------------------------
    if not csv_1h.exists():
        return False

    df_1h = pd.read_csv(
        filepath_or_buffer = csv_1h, 
        sep = ";", 
        parse_dates = ["datetime"])
    df_day_1h = df_1h[(df_1h["datetime"].dt.date == target_date.date())]

    if df_day_1h.empty:
        return False

    # Timestamps attendus : toutes les heures
    found_hours = set(df_day_1h["datetime"])
    if not all(h in found_hours for h in expected_hours):
        return False

    # -----------------------------------------------------------
    # Vérification fichier 30 min
    # -----------------------------------------------------------
    if not csv_30min.exists():
        return False

    df_30 = pd.read_csv(
        filepath_or_buffer = csv_30min, 
        sep = ";", 
        parse_dates = ["datetime"])
    df_day_30 = df_30[(df_30["datetime"].dt.date == target_date.date())]

    if df_day_30.empty:
        return False

    # Vérifier qu'il existe au moins une donnée par heure
    hours_with_data = set(df_day_30["datetime"].dt.hour)

    expected_hours_set = set(range(
                                stop = 24))
    if not expected_hours_set.issubset(
                                s = hours_with_data):
        return False

    return True


# ------------------------------------------------------
# 📦 Gestion des archives ZIP
# ------------------------------------------------------

def add_file_to_zip(tmp_file: Path, zip_path: Path, arcname: str):
    """
    Ajoute un fichier dans une archive ZIP en le renommant selon la date cible.

    Paramètres :
        tmp_file (Path) : chemin du fichier temporaire local
        zip_path (Path) : chemin de l’archive ZIP
        arcname (str) : chemin/nom du fichier DANS le ZIP
                        ex:
                            - prod_2025-03-25.csv
                            - conso_1h/courbe_2025-03-25.json
    """
    with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(
            filename = tmp_file, 
            arcname = arcname)

    print(f"📦 Fichier ajouté dans l’archive sous : {arcname}")

def extract_zip_file_list(zip_path: Path) -> list[str]:
    """
    Liste les fichiers contenus dans une archive ZIP.

    Paramètre :
        zip_path (Path) : chemin de l’archive ZIP

    Retour :
        list[str] : liste des chemins internes des fichiers contenus dans le ZIP
    """
    if not zip_path.exists():
        return []
    with zipfile.ZipFile(
        file = zip_path, 
        mode = "r") as zipf:
        return zipf.namelist()

def read_csv_from_zip(zip_path: Path, zip_filename: str) -> pd.DataFrame:
    """
    Extrait et lit un fichier CSV contenu dans une archive ZIP.

    Parameters
    ----------
    zip_path : Path
        Chemin vers l'archive ZIP contenant un fichier CSV.
    zip_filename : str
        Nom du fichier CSV.

    Returns
    -------
    pd.DataFrame
        Le contenu du CSV sous forme de DataFrame.

    Raises
    ------
    FileNotFoundError
        Si l'archive ZIP n'existe pas.
    ValueError
        Si aucun fichier CSV n'est trouvé dans l'archive.
    """
    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"L'archive ZIP n'existe pas : {zip_path}")

    with zipfile.ZipFile(
        file = zip_path, 
        mode = 'r') as z:
        # Trouver le fichier CSV dans le ZIP
        csv_file = [f for f in z.namelist() if f==zip_filename]

        if not csv_file:
            raise ValueError(f"Le fichier {zip_filename} n'a pas été trouvé dans l'archive : {zip_path}")

        with z.open(
                name = zip_filename) as csv_file:
            try:
                return pd.read_csv(
                    filepath_or_buffer = csv_file, 
                    encoding = 'utf-8', 
                    sep = ";")
            except UnicodeDecodeError:
                # Tentative alternative automatique
                return pd.read_csv(
                    filepath_or_buffer = csv_file, 
                    encoding = "latin-1", 
                    sep = ";")

def check_json_in_archive(zip_path:Path, date_str: str, interval_folder: str) -> bool:
    """
    Vérifie si un fichier JSON pour une date est déjà présent dans l'archive.

    Paramètres :
        zip_path (Path) : Chemin du fichier ZIP.
        date_str (str) : date au format 'YYYY-MM-DD'
        interval_folder (str) : 'conso_1h' ou 'conso_30min'

    Retour :
        bool : True si le fichier existe dans l'archive, False sinon
    """
    zip_files = extract_zip_file_list(
                    zip_path = zip_path)
    json_name = f"{interval_folder}/conso_{date_str}.json"
    return json_name in zip_files

def extract_csv_from_zip(zip_path: Path, dest_folder: Path) -> Path:
    """
    Extrait le CSV contenu dans un ZIP dans dest_folder.

    Paramètres :
        zip_path : chemin du fichier ZIP
        dest_folder : chemin vers le dossier de destination du CSV

    Retour :
        chemin du CSV extrait
    """
    with zipfile.ZipFile(
        file = zip_path, 
        mode = 'r') as zipf:
        csv_names = [f for f in zipf.namelist() 
                     if f.lower().endswith(
                                    suffix = '.csv')]
        if not csv_names:
            raise RuntimeError(f"Aucun CSV trouvé dans {zip_path}")
        csv_name = csv_names[0]
        Path.mkdir(dest_folder, exist_ok = True)
        zipf.extract(
            member = csv_name, 
            path = dest_folder)
        extracted_path = dest_folder.joinpath(csv_name)
    return extracted_path