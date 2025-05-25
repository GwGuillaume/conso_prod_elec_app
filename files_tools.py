import os
import glob
import pandas as pd


# ------------------- TRAITEMENT DES FICHIERS DE CONSOMMATION ------------------- #
def process_raw_consumption_file(consumption_data_path, consumption_data_folder,
                                 raw_csv_filename, clean_csv_filename):
    """
    Traite les fichiers bruts de consommation électrique issus d'un export depuis
    l'espace particulier d'EDF (https://suiviconso.edf.fr/comprendre), pour en
    extraire les données utiles et les convertir en un DataFrame propre avec des
    types corrects.

    Le fichier brut contient des dates sur des lignes séparées et des lignes
    horaires avec consommation associée. Le résultat est sauvegardé dans un fichier
    CSV nettoyé.

    Paramètres :
    -----------
    consumption_data_path : str
        Chemin de base vers le dossier contenant les données de consommation.

    consumption_data_folder : str
        Nom du sous-dossier contenant les fichiers CSV bruts.

    raw_csv_filename : str
        Nom du fichier brut à traiter (par exemple :
                                       'mes-puissances-atteintes-30min-....csv').

    clean_csv_filename : str
        Nom du fichier CSV nettoyé à générer en sortie.

    Retour :
    --------
    df : pd.DataFrame
        DataFrame contenant deux colonnes : 'datetime' (timestamps) et
                                            'consommation' (valeurs numériques).
    """

    # Chargement du  fichier en ignorant les erreurs d'encodage
    with open(os.path.join(consumption_data_path, consumption_data_folder, raw_csv_filename),
              "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Filtrage des lignes utiles (en retirant l'entête et les lignes vides)
    useful_data = []
    current_date = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue  # ligne vide
        # Ligne contenant uniquement une date
        if "/" in line and ":" not in line:
            current_date = line.split(';')[0]
            continue
        # Lignes contenant les données horaires de consommation (séparateur point-virgule)
        if "R�elle" in line:
            parts = line.split(";")
            if len(parts) >= 2:
                heure = parts[0].strip()
                consommation = parts[1].strip()
                full_datetime = f"{current_date} {heure}"
                useful_data.append([full_datetime, consommation])

    # Création du DataFrame avec pour colonnes datetime et consommation
    df = pd.DataFrame(useful_data, columns=["datetime", "consommation"])

    # Conversion des chaînes de caractères en types adaptés
    df["datetime"] = pd.to_datetime(df["datetime"], dayfirst=True, errors="coerce")
    df["consommation"] = pd.to_numeric(df["consommation"], errors="coerce")

    # Suppression des enregistrements pour lesquels un seul enregistrement est présent pour la journée
    df["date"] = df["datetime"].dt.date
    df = df[df.groupby("date")["date"].transform("size") > 1]

    # Suppression de la colonne temporaire "date_tmp"
    df = df.drop(columns="date")

    # Tri des lignes par datetime pour conserver un ordre chronologique
    df = df.sort_values('datetime').reset_index(drop=True)

    # Sauvegarde du DataFrame nettoyé dans un fichier CSV
    outpath = os.path.join(consumption_data_path, clean_csv_filename)
    df.to_csv(outpath, sep=";", index=False)

    return df


import os
import glob
import zipfile
import shutil


# ----------- DÉCOMPRESSION DES ARCHIVES ET RENOMMAGE DES FICHIERS -------------- #
def extract_and_organize_zip_files(zip_folder_path: str, delete_archives: bool = False):
    """
    Décompresse tous les fichiers ZIP présents dans un dossier, renomme le fichier extrait
    selon le nom du dossier de décompression, puis le déplace vers le dossier parent.

    Les dossiers de décompression sont ensuite supprimés. Les archives ZIP peuvent être
    supprimées si souhaité.

    Paramètres :
    ------------
    zip_folder_path : str
        Chemin vers le dossier contenant les fichiers ZIP à traiter.

    delete_archives : bool, par défaut False
        Si True, les fichiers ZIP originaux sont supprimés après traitement.

    Effets :
    --------
    - Chaque archive ZIP est extraite dans un dossier temporaire.
    - Le fichier CSV extrait est renommé avec le nom du dossier (même nom que l'archive, sans extension).
    - Ce fichier est déplacé dans le dossier racine (zip_folder_path).
    - Les dossiers temporaires de décompression sont supprimés.
    - Les archives ZIP peuvent être supprimées selon l'option delete_archives.
    """

    # Liste tous les fichiers ZIP dans le dossier donné
    zip_files = glob.glob(os.path.join(zip_folder_path, "*.zip"))

    for zip_file in zip_files:
        # Nom sans extension .zip
        base_name = os.path.splitext(os.path.basename(zip_file))[0]
        extract_dir = os.path.join(zip_folder_path, base_name)

        # Crée un dossier temporaire pour l'extraction
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Cherche le fichier extrait dans le dossier (supposé unique)
        extracted_files = glob.glob(os.path.join(extract_dir, "*"))
        if len(extracted_files) != 1:
            print(f"⚠️ Fichier inattendu dans {extract_dir}, attendu un seul fichier.")
            continue

        extracted_file = extracted_files[0]
        ext = os.path.splitext(extracted_file)[1]
        new_filename = base_name + ext
        new_filepath = os.path.join(zip_folder_path, new_filename)

        # Déplacement et renommage
        shutil.move(extracted_file, new_filepath)

        # Suppression du dossier temporaire
        shutil.rmtree(extract_dir)

        # Suppression de l'archive si demandé
        if delete_archives:
            os.remove(zip_file)


# -------------------- TRAITEMENT DES FICHIERS DE PRODUCTION -------------------- #
def process_raw_production_repo(production_data_path, production_data_folder,
                                raw_csv_root_filename, clean_csv_filename):
    """
    Traite l'ensemble de fichiers CSV contenant les données de production électrique
    issues d'un export depuis le site web de surveillance, de gestion et de dépannage
    de l'installation photovoltaïque
    (https://global.hoymiles.com/website/plant/detail/156600/report) et les fusionne
    en un seul Dataframe. Le résultat est sauvegardé dans un fichier CSV nettoyé.

    Paramètres :
    -----------
    production_data_path : str
        Chemin vers le dossier racine contenant les fichiers de production.

    production_data_folder : str
        Nom du sous-dossier dans lequel se trouvent les fichiers CSV bruts.

    raw_csv_root_filename : str
        Motif de recherche des fichiers CSV bruts (ex: "station_power_data_*.csv").

    clean_csv_filename : str
        Nom du fichier de sortie contenant les données nettoyées.

    Retour :
    --------
    df_all : pd.DataFrame
        DataFrame contenant deux colonnes : 'datetime' (horodatage) et 'production'
                                            (en watts).
    """

    # Décompression des archives et renommage des ficheir
    extract_and_organize_zip_files("data/prod/raw_csv_files", delete_archives=True)

    # Recherche de tous les fichiers CSV correspondant au motif dans le dossier spécifié
    csv_files = glob.glob(os.path.join(production_data_path,
                                       production_data_folder,
                                       raw_csv_root_filename))

    # Lire et concaténer tous les fichiers CSV dans un seul DataFrame
    df_list = []

    for file in csv_files:
        df = pd.read_csv(file, sep=",")  # séparateur = virgule
        df_list.append(df.loc[:, ['Time', 'Production (W)']])

    # Fusionner tous les DataFrames
    df_all = pd.concat(df_list, ignore_index=True)
    df_all.rename(columns={"Time": "datetime", "Production (W)": "production"},
                  inplace=True)

    # Conversion des types
    df_all["datetime"] = pd.to_datetime(df_all["datetime"],
                                        yearfirst=True,
                                        errors="coerce")
    df_all["production"] = pd.to_numeric(df_all["production"],
                                         errors="coerce")

    # Tri des lignes par datetime pour conserver un ordre chronologique
    df_all = df_all.sort_values('datetime').reset_index(drop=True)

    # Sauvegarder le fichier concaténé
    output_path = os.path.join(production_data_path, clean_csv_filename)
    df_all.to_csv(output_path, sep=";", index=False)

    return df_all