#!/usr/bin/env python3
"""
update_token.py

Script Selenium pour se connecter sur global.hoymiles.com et récupérer le token.
Ce script est utilisé par external_api_tools.refresh_token().

Usage :
    python update_token.py --mode local
    python update_token.py --mode gha
"""

import os
import argparse
import time
import json
from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

# Charger .env
load_dotenv()
USERNAME = os.getenv("HOYMILES_USER")
PASSWORD = os.getenv("HOYMILES_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("HOYMILES_USER ou HOYMILES_PASSWORD non définis dans .env")

LOGIN_PAGE = "https://global.hoymiles.com/website/login"
TIMEOUT = 20


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
        time.sleep(1)
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
        # fallback cookies
        for c in driver.get_cookies():
            if "token" in (c.get("name") or "").lower():
                token = c.get("value")
                break

    driver.quit()
    return token


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local", "gha"], default="local")
    args = parser.parse_args()

    token = get_token(headless=True)

    if token:
        print(token)  # stdout → capté par external_api_tools.refresh_token()
        if args.mode == "local":
            set_key("../.env", "HOYMILES_TOKEN", token)
            print("✅ Token mis à jour dans .env")
        elif args.mode == "gha":
            gha_env = os.getenv("GITHUB_ENV")
            if gha_env:
                with open(gha_env, "a") as f:
                    f.write(f"HOYMILES_TOKEN={token}\n")
                print("✅ Token exporté dans $GITHUB_ENV")
    else:
        print("❌ Échec récupération token.")
