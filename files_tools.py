import os
import glob
import pandas as pd
from datetime import datetime, timedelta
import requests
import zipfile
import shutil


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

    # Chargement du fichier en ignorant les erreurs d'encodage
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



# ----------------- TÉLÉCHARGEMENT DES DONNÉES DE PRODUCTION -------------------- #
def download_raw_production_zip_file(site_id: int, date, dossier_destination: str = "data/prod/raw_csv_files") -> str:
    """
    Télécharge une archive ZIP contenant les données de production photovoltaïque
    pour un site donné et une date spécifique, depuis l'API Hoymiles.
    """

    # Conversion de la date en string
    if isinstance(date, datetime):
        date = date.date()
    if hasattr(date, "strftime"):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://global.hoymiles.com",
        "Referer": "https://global.hoymiles.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "authorization": "2.4PMyNY7DGNaOEYvbsatvLlFW5cnN5XDILQSAdayaDGHwF7SLufh3qprIeQSku0PctltkVj3XcXdahidPn.0",
        "language": "fr-fr"
    }

    cookies = {
        "__hstc": "VALEUR_VALIDÉE",
        "hubspotutk": "VALEUR_VALIDÉE",
        "_ga": "VALEUR_VALIDÉE",
        "_ga_61ZC562X9S": "VALEUR_VALIDÉE"
    }

    # Étape 1 : Prévisualisation
    payload_select = {
        "sid_list": [site_id],
        "sid": site_id,
        "start_date": date_str,
        "end_date": date_str,
        "page": 1,
        "page_size": 20
    }
    resp1 = requests.post(
        "https://neapi.hoymiles.com/pvm-report/api/0/station/report/select_power_by_station",
        headers=headers, cookies=cookies, json=payload_select
    )
    print("Étape 1 : prévisualisation ->", resp1.status_code)

    # Étape 2 : Exportation
    payload_export = {
        "quota": "STATION_POWER",
        "sid_list": [site_id],
        "sid": site_id,
        "start_date": date_str,
        "end_date": date_str,
        "page": 1,
        "page_size": 20
    }
    resp2 = requests.post(
        "https://neapi.hoymiles.com/pvm-report/api/0/station/report/export_station_data",
        headers=headers, cookies=cookies, json=payload_export
    )
    print("Étape 2 : exportation ->", resp2.status_code)

    # Étape 3 : Vérification du contenu
    try:
        resp2_json = resp2.json()
    except Exception as e:
        raise RuntimeError(f"Impossible de décoder la réponse JSON : {e}\nRéponse brute : {resp2.text}")

    export_data = resp2_json.get("data")

    if isinstance(export_data, str):
        # L’API renvoie parfois un message au lieu d’un dict avec url
        raise RuntimeError(f"L’API Hoymiles a renvoyé un message : {export_data}")

    if not isinstance(export_data, dict) or "url" not in export_data:
        raise RuntimeError(f"Réponse inattendue de l’API Hoymiles : {resp2_json}")

    zip_url = export_data["url"]
    print("URL de téléchargement :", zip_url[:100], "...")

    # Étape 4 : Téléchargement ZIP
    os.makedirs(dossier_destination, exist_ok=True)
    chemin_zip = os.path.join(dossier_destination, f"station_power_{date_str}.zip")

    r = requests.get(zip_url)
    r.raise_for_status()

    with open(chemin_zip, "wb") as f:
        f.write(r.content)

    print(f"Archive téléchargée avec succès : {chemin_zip}")
    return chemin_zip


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
        new_filename = "_data_".join(base_name.rsplit('_', 1)) + ext
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
                                raw_csv_root_filename, clean_csv_filename,
                                site_id=156600):
    """
    Traite l'ensemble des fichiers CSV contenant les données de production électrique
    issues d'exports Hoymiles et les fusionne en un seul DataFrame. Les données
    manquantes sont automatiquement téléchargées via l’API Hoymiles.

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

    site_id : int, par défaut 156600
        Identifiant du site Hoymiles.

    Retour :
    --------
    df_all : pd.DataFrame
        DataFrame contenant deux colonnes : 'datetime' (horodatage) et 'production'
                                            (en watts).
    """

    raw_csv_files_path = os.path.join(production_data_path, production_data_folder)

    # -------------------------------
    # 1 - Identifier les dates déjà présentes
    # -------------------------------
    fichiers_existants = glob.glob(os.path.join(raw_csv_files_path, raw_csv_root_filename))
    dates_existantes = set()

    for fichier in fichiers_existants:
        # Exemple de nom : station_power_data_2025-03-25.csv
        try:
            date_str = os.path.basename(fichier).split("_")[-1].replace(".csv", "")
            dates_existantes.add(datetime.strptime(date_str, "%Y-%m-%d").date())
        except Exception:
            continue

    if dates_existantes:
        date_debut = min(dates_existantes)
    else:
        # Si aucun fichier présent, on part de la date du 2025-03-25
        date_debut = datetime.strptime("2025-03-25", "%Y-%m-%d").date()

    date_fin = datetime.today().date()

    # ------------------------------------
    # 2 - Télécharger les dates manquantes
    # ------------------------------------
    date_courante = date_debut
    while date_courante <= date_fin:
        if date_courante not in dates_existantes:
            print(f"📥 Téléchargement des données du {date_courante} ...")
            try:
                download_raw_production_zip_file(
                    site_id=site_id,
                    date=date_courante.strftime("%Y-%m-%d"),
                    dossier_destination=raw_csv_files_path
                )
            except Exception as e:
                print(f"❌ Erreur téléchargement {date_courante} : {e}")
        date_courante += timedelta(days=1)

    # -------------------------------
    # 3 - Extraire les fichiers ZIP nouvellement téléchargés
    # -------------------------------
    extract_and_organize_zip_files(raw_csv_files_path,
                                   delete_archives=True)

    # -------------------------------
    # 4 - Fusionner tous les CSV
    # -------------------------------
    csv_files = glob.glob(os.path.join(raw_csv_files_path, raw_csv_root_filename))
    df_list = []

    for file in csv_files:
        df = pd.read_csv(file, sep=",")  # séparateur = virgule
        df_list.append(df.loc[:, ['Time', 'Production (W)']])

    if not df_list:
        raise RuntimeError("❌ Aucun fichier CSV trouvé après extraction.")

    df_all = pd.concat(df_list, ignore_index=True)
    df_all.rename(columns={"Time": "datetime", "Production (W)": "production"},
                  inplace=True)

    # Conversion des types
    df_all["datetime"] = pd.to_datetime(df_all["datetime"],
                                        yearfirst=True,
                                        errors="coerce")
    df_all["production"] = pd.to_numeric(df_all["production"],
                                         errors="coerce")

    # Tri par datetime
    df_all = df_all.sort_values('datetime').reset_index(drop=True)

    # Sauvegarder le fichier concaténé
    output_path = os.path.join(production_data_path, clean_csv_filename)
    df_all.to_csv(output_path, sep=";", index=False)

    print(f"✅ Données fusionnées sauvegardées dans {output_path}")

    return df_all