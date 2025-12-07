# -*- coding: utf-8 -*-
"""
api_client.py

Outils bas-niveau pour interagir avec l’API Hoymiles.

Fonctionnalités :
- Télécharge les fichiers ZIP bruts pour une date donnée
- Rafraîchit le token automatiquement si nécessaire
- Ajoute les nouveaux CSV dans le jeu de données principal et dans l’archive
"""

from os import getenv
from pathlib import Path
import tempfile
import zipfile
import shutil
from datetime import datetime
from typing import Optional
import requests
from dotenv import load_dotenv, set_key
from time import sleep
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

from common.config import ROOT_PATH
from common.utils import format_date_to_str, add_file_to_zip, extract_csv_from_zip, clean_csv_columns, append_csvs_to_clean_csv, append_csvs_with_resampling, resampled_data_exists_for_date, read_csv_from_zip
from prod_api_tools.config import LOGIN_PAGE, USERNAME, PASSWORD, TIMEOUT, DATA_FOLDER, API_BASE_URL, CSV_30MIN, CSV_1H


# Charger .env si présent (utile en local)
load_dotenv()

# ---------------------------------------------------------------------
# Helpers pour token
# ---------------------------------------------------------------------

def _current_token() -> Optional[str]:
    """Retourne le token HOYMILES_TOKEN depuis .env ou l'environnement."""
    load_dotenv(override=True)  # recharge le .env à chaque appel
    return getenv("HOYMILES_TOKEN")

def safe_find_multiple(driver, selectors):
    """Essaie plusieurs sélecteurs CSS/XPath en renvoyant le premier élément trouvé."""
    for sel_type, sel in selectors:
        try:
            if sel_type == "css":
                return driver.find_element(By.CSS_SELECTOR, sel)
            elif sel_type == "xpath":
                return driver.find_element(By.XPATH, sel)
        except Exception:
            continue
    return None

def get_token(headless=True):
    """Effectue la connexion et retourne le token Hoymiles."""
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_opts)
    wait = WebDriverWait(driver, TIMEOUT)
    driver.get(LOGIN_PAGE)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-layout")))
    except TimeoutException:
        print("⚠️ Timeout initial : page non chargée complètement.")

    username_input = safe_find_multiple(driver, [
        ("css", "input[name='user_name']"),
        ("css", "input[type='text']"),
        ("xpath", "//input[contains(@placeholder, 'user')]"),
    ])
    password_input = safe_find_multiple(driver, [
        ("css", "input[type='password']"),
        ("xpath", "//input[@type='password']"),
    ])

    if not username_input or not password_input:
        driver.quit()
        raise RuntimeError("❌ Impossible de trouver les champs login/password.")

    username_input.clear()
    username_input.send_keys(USERNAME)
    password_input.clear()
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.ENTER)

    token = None
    for _ in range(15):  # max 15s
        sleep(1)
        try:
            storage = driver.execute_script("return Object.assign({}, window.localStorage);")
            for key in ["token", "access_token", "authorization", "auth_token", "userToken"]:
                if key in storage:
                    token = storage[key]
                    break
            if not token:
                for v in storage.values():
                    try:
                        parsed = json.loads(v)
                        if isinstance(parsed, dict) and "token" in parsed:
                            token = parsed["token"]
                            break
                    except Exception:
                        continue
            if token:
                break
        except Exception:
            continue

    if not token:
        # Cookies de secours
        for c in driver.get_cookies():
            if "token" in (c.get("name") or "").lower():
                token = c.get("value")
                break

    driver.quit()
    return token

def save_token(token: str) -> None:
    """
    Sauvegarde le token :
    - en local : écrit (ou remplace) la variable HOYMILES_TOKEN dans .env
    - dans GitHub Actions : écrit dans le fichier $GITHUB_ENV (s'il existe)
    """
    if getenv("GITHUB_ACTIONS") is None:
        env_path = ROOT_PATH.joinpath(".env")
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        with open(env_path, "w", encoding="utf-8") as fh:
            found = False
            for line in lines:
                if line.strip().startswith("HOYMILES_TOKEN="):
                    fh.write(f"HOYMILES_TOKEN={token}\n")
                    found = True
                else:
                    fh.write(line)
            if not found:
                fh.write(f"HOYMILES_TOKEN={token}\n")
        print(f"💾 Token mis à jour dans {env_path}")
    else:
        gha_env = getenv("GITHUB_ENV")
        if gha_env:
            with open(gha_env, "a", encoding="utf-8") as fh:
                fh.write(f"HOYMILES_TOKEN={token}\n")
            print("💾 Token exporté dans $GITHUB_ENV")
        else:
            print("⚠️ $GITHUB_ENV introuvable — token non exporté.")

def refresh_token(mode: str = "local") -> Optional[str]:
    """
    Rafraîchit le token Hoymiles directement en appelant la fonction get_token().

    Paramètres
    ----------
    mode : str
        - "local" : met à jour le fichier .env avec le nouveau token.
        - "gha" : exporte le token vers l'environnement GitHub Actions (GITHUB_ENV).

    Retour
    ------
    str | None
        Le token récupéré, ou None en cas d'échec.
    """
    try:
        token = get_token(headless=True)
    except Exception as e:
        print(f"❌ Erreur lors du rafraîchissement du token : {e}")
        return None

    if not token:
        print("❌ Aucun token trouvé après tentative de connexion Hoymiles.")
        return None

    print("✅ Token récupéré avec succès.")

    if mode == "local":
        # On suppose que le .env est à la racine du projet
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if not env_path.exists():
            print(f"⚠️ Fichier .env non trouvé à {env_path}")
        else:
            set_key(str(env_path), "HOYMILES_TOKEN", token)
            print("✅ Token mis à jour dans .env")

    elif mode == "gha":
        gha_env = getenv("GITHUB_ENV")
        if gha_env:
            with open(gha_env, "a", encoding="utf-8") as f:
                f.write(f"HOYMILES_TOKEN={token}\n")
            print("✅ Token exporté dans $GITHUB_ENV")
        else:
            print("⚠️ Variable GITHUB_ENV non définie — impossible d’exporter le token.")

    return token


# ---------------------------------------------------------------------
# Fonctions HTTP (preview / export / download)
# ---------------------------------------------------------------------
def _get_headers(token: Optional[str] = None) -> dict:
    """
    Construit les en-têtes pour les requêtes Hoymiles.
    Le site attend le cookie/clé smc_prod_token → donc 'authorization' brut.
    """
    tok = token or _current_token()
    if not tok:
        raise RuntimeError("⚠️ Aucun token disponible (HOYMILES_TOKEN non défini).")
    return {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://global.hoymiles.com",
        "Referer": "https://global.hoymiles.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
        # Le cookie smc_prod_token se reflète côté API comme 'authorization'
        "authorization": tok,
    }


def _get_cookies() -> dict:
    """Construit des cookies à partir des variables d'environnement (si disponibles)."""
    return {
        "__hstc": getenv("HOYMILES_HSTC", ""),
        "hubspotutk": getenv("HOYMILES_HUBSPOT", ""),
        "_ga": getenv("HOYMILES_GA", ""),
        "_ga_61ZC562X9S": getenv("HOYMILES_GA61", "")
    }


def build_payload(site_id: int, date_str: str, quota: str|None="STATION_POWER") -> dict:
    """
    Construit et retourne un dictionnaire (payload) utilisé pour interroger une API.

    Paramètres
    ----------
    site_id : int
        Identifiant unique du site pour lequel la requête doit être effectuée.
    date_str : str
        Date au format texte (par exemple '2025-01-15') utilisée à la fois comme
        date de début et date de fin dans la requête.
    quota : str
        Quota ("STATION_POWER" par défaut)

    Retour
    ------
    dict
        Un dictionnaire contenant les paramètres nécessaires à la requête API :
        - sid_list : liste contenant l'identifiant du site
        - sid : identifiant unique du site
        - start_date : date de début sous forme de chaîne
        - end_date : date de fin sous forme de chaîne
        - page : numéro de page (1 par défaut)
        - page_size : nombre d'éléments par page (20 par défaut)
    """

    # Construction du dictionnaire de paramètres avec les valeurs fournies
    if quota is not None:
        payload = {
            "quota" : quota
        }
    else:
        payload = {}

    payload_common = {
        "sid_list": [site_id],  # La liste doit contenir l'identifiant du site
        "sid": site_id,  # Identifiant direct du site
        "start_date": date_str,  # Date de début de la période
        "end_date": date_str,  # Date de fin de la période (identique ici)
        "page": 1,  # Première page par défaut
        "page_size": 20  # Taille de page par défaut
    }

    payload = dict(payload, **payload_common)

    # Retour du dictionnaire construit
    return payload


def request_production_preview(site_id: int, target_date: datetime) -> dict:
    """
    Appelle l'endpoint de prévisualisation (select_power_by_station).
    Retourne le JSON de la réponse.
    """
    # 1️⃣ Datetime format to String
    date_str = format_date_to_str(target_date)

    resp = requests.post(
        API_BASE_URL + "select_power_by_station",
        headers=_get_headers(),
        cookies=_get_cookies(),
        json=build_payload(site_id=site_id, date_str=date_str, quota=None)
    )
    resp.raise_for_status()
    return resp.json()


def request_production_export(site_id: int, date_str: str) -> dict:
    """Effectue une requête d'export de production Hoymiles pour une journée donnée."""
    url = API_BASE_URL + "export_station_data"

    response = requests.post(
        url=url,
        headers=_get_headers(_current_token()),
        cookies=_get_cookies(),
        json=build_payload(site_id=site_id, date_str=date_str, quota="STATION_POWER"),
        timeout=30)

    data = response.json().get("data")
    resp = json.loads(response.text)

    if resp["message"] != "success":
        msg = resp["message"].lower()

        # VRAIES erreurs de token
        if any(x in msg for x in ["token", "verify", "unauthorized", "401", "403"]):
            raise RuntimeError("token error")

        # Operation error → ce n'est PAS un token error
        if "operation error" in msg:
            raise RuntimeError(f"operation_error: {resp}")

        raise RuntimeError(f"Erreur Hoymiles pour {date_str}: {resp}")

    return data


def download_raw_production_zip_file(site_id: int,
                                     target_date: datetime,
                                     dest_dir: Path) -> Path:
    """
    Télécharge l'archive ZIP produite par export_station_data pour une date donnée.
    - Gère le polling tant que Hoymiles n'a pas encore généré le fichier.
    - Retente automatiquement en cas de "Operation error" ou data=None.
    """
    # 1️⃣ Datetime format to String
    date_str = format_date_to_str(target_date)

    # 1️⃣ Vérification de l'existence de données pour ce jour-là
    preview = request_production_preview(site_id, target_date)
    if preview.get('message') != 'success':
        raise RuntimeError(f"Échec : aucune donnée pour {date_str} (réponse preview: {preview.get('message')})")

    # 2️⃣ Lancement de l'export
    export_resp = request_production_export(site_id, date_str)
    # 3️⃣ Téléchargement du ZIP
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    chemin_zip = dest_dir.joinpath(f"station_power_{date_str}.zip")
    print(f"📦 Téléchargement de l'archive {export_resp.get('file_name')}")
    r = requests.get(export_resp.get('url'), timeout=90)
    r.raise_for_status()
    with open(chemin_zip, "wb") as fh:
        fh.write(r.content)

    print(f"✅ Archive téléchargée : {chemin_zip}")
    return chemin_zip


def fetch_and_archive(target_date: datetime, site_id: int, archive_path: Path, csv_path_30min: Path, csv_path_1h: Path) -> bool:
    """
    Télécharge et intègre les données de production pour une date donnée.
    Optimisé pour éviter les téléchargements et traitements inutiles.

    Paramètres :
        target_date (datetime) : date cible
        site_id (int) : identifiant de la station Hoymiles
        archive_path (Path) : chemin du fichier ZIP d’archive (raw_prod_files.zip)
        csv_path_30min (Path) : chemin du fichier CSV cumulatif moyenné sur 30min
        csv_path_1h (Path) : chemin du fichier CSV cumulatif moyenné sur 1h

    Retourne :
        bool : True si de nouvelles données ont été téléchargées, False sinon
    """

    # ----------------------------------------------------------
    # 1) Vérification : le fichier existe-t-il déjà dans le ZIP ?
    # ----------------------------------------------------------

    zip_filename = "prod_" + target_date.strftime("%Y-%m-%d") + ".csv"
    already_in_zip = False

    if archive_path.exists():
        with zipfile.ZipFile(archive_path, "r") as z:
            already_in_zip = zip_filename in z.namelist()

    # ----------------------------------------------------------
    # 2) Vérification : données présentes dans les resamplés ?
    # ----------------------------------------------------------

    if already_in_zip:
        has_data = resampled_data_exists_for_date(target_date=target_date,
                                                  csv_30min=csv_path_30min, csv_1h=csv_path_1h)

        if has_data:
            print(f"⏩ Données déjà intégrées pour {target_date.date()} — aucune action nécessaire.")
            return True

        print(f"♻️ Données déjà dans le ZIP mais resamplages manquants → reconstruction…")

        # Dans ce cas : lire les données du ZIP
        df = read_csv_from_zip(zip_path=archive_path, zip_filename=zip_filename)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.to_csv(tmp.name, sep=";", index=False)

        append_csvs_with_resampling(
            csv_paths=[Path(tmp.name)],
            csv_30min=csv_path_30min,
            csv_1h=csv_path_1h
        )

        return True

    # ----------------------------------------------------------
    # 3) Sinon → téléchargement normal
    # ----------------------------------------------------------

    temp_dir = tempfile.TemporaryDirectory()
    temp_file = Path(temp_dir.name)

    try:
        try:
            zip_path = download_raw_production_zip_file(
                site_id=site_id,
                target_date=target_date,
                dest_dir=temp_file
            )
        except Exception as e:
            msg = str(e).lower()

            is_token_issue = any(x in msg for x in ["token error", "401", "403", "verify"])
            is_operation_error = "operation_error" in msg  # ce qu’on renvoie depuis request_production_export

            if is_token_issue and not is_operation_error:
                print("⚠️ Problème de token — tentative de rafraîchissement…")
                new_token = refresh_token(mode="gha" if getenv("GITHUB_ACTIONS") else "local")
                if not new_token:
                    raise RuntimeError("❌ Impossible de rafraîchir le token Hoymiles.")

                # 🔁 Second essai
                try:
                    zip_path = download_raw_production_zip_file(
                        site_id=site_id,
                        target_date=target_date,
                        dest_dir=temp_file
                    )
                except Exception as e2:
                    raise RuntimeError(f"token error après refresh: {e2}")

            else:
                raise

        # Extraction du CSV brut
        csv_extracted = extract_csv_from_zip(zip_path=zip_path, dest_folder=temp_file)

        # Renommage des colonnes Hoymiles
        prod_csv_map = {"Time": "datetime", "Production (W)": "production"}
        clean_csv_columns(source_csv=csv_extracted, columns_map=prod_csv_map)

        # Ajout à l’archive
        add_file_to_zip(tmp_file=csv_extracted,
                        zip_path=archive_path,
                        target_date=target_date)

        # Mise à jour des fichiers resamplés
        append_csvs_with_resampling(
            csv_paths=[csv_extracted],
            csv_30min=csv_path_30min,
            csv_1h=csv_path_1h
        )

        print(f"✅ Données de production intégrées pour {target_date.date()}")
        sleep(1)
        return True

    except Exception as e:
        print(f"❌ Erreur lors du traitement de {target_date.date()} : {e}")
        return False

    finally:
        shutil.rmtree(temp_file, ignore_errors=True)

    # temp_dir = tempfile.TemporaryDirectory()
    # temp_file = Path(temp_dir.name)
    # try:
    #     try:
    #         zip_path = download_raw_production_zip_file(site_id=site_id,
    #                                                     target_date=target_date,
    #                                                     dest_dir=temp_file)
    #     except Exception as e:
    #         msg = str(e).lower()
    #         if "token error" in msg or "401" in msg or "403" in msg or "verify" in msg:
    #             print("⚠️ Problème de token détecté — tentative de rafraîchissement...")
    #             new_token = refresh_token(mode="gha" if getenv("GITHUB_ACTIONS") else "local")
    #             if not new_token:
    #                 raise RuntimeError("❌ Impossible de rafraîchir le token Hoymiles.")
    #             zip_path = download_raw_production_zip_file(site_id=site_id,
    #                                                         target_date=target_date,
    #                                                         dest_dir=temp_file)
    #         else:
    #             raise
    #
    #     csv_extracted = extract_csv_from_zip(zip_path=zip_path,
    #                                          dest_folder=temp_file)
    #     # Mapping des colonnes Hoymiles
    #     prod_csv_map = {
    #         "Time": "datetime",
    #         "Production (W)": "production",
    #     }
    #     # Extraction, et renommage des colonnes du fichier csv
    #     clean_csv_columns(source_csv=csv_extracted, columns_map=prod_csv_map)
    #     # Renommage du fichier csv et ajout à l'archive
    #     add_file_to_zip(tmp_file=csv_extracted, zip_path=archive_path, target_date=target_date)
    #     append_csvs_with_resampling(csv_paths=[csv_extracted],
    #                                 csv_30min=csv_path_30min,
    #                                 csv_1h=csv_path_1h)
    #     print(f"✅ Données de production intégrées pour {target_date}")
    #     sleep(1)  # pour éviter la surcharge de l'API
    #     return True
    #
    # except Exception as e:
    #     print(f"❌ Erreur lors du traitement de {target_date} : {e}")
    #     return False
    #
    # finally:
    #     shutil.rmtree(temp_file, ignore_errors=True)
