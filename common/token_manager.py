# -*- coding: utf-8 -*-
"""
Gestion centralisée du token pour les APIs Hoymiles et Conso.
"""

import os
from dotenv import load_dotenv, set_key

load_dotenv()

def get_token(env_var: str = "HOYMILES_TOKEN") -> str:
    """Retourne le token depuis l'environnement ou .env"""
    token = os.getenv(
        key = env_var)
    if not token:
        raise RuntimeError(f"{env_var} non défini dans l'environnement")
    return token

def save_token(token: str, env_var: str = "HOYMILES_TOKEN") -> None:
    """Sauvegarde le token dans .env ou dans $GITHUB_ENV si en GHA"""
    if os.getenv("GITHUB_ACTIONS"):
        gha_env = os.getenv(
            key = "GITHUB_ENV")
        if gha_env:
            with open(
                file = gha_env, 
                mode = "a") as f:
                f.write(
                    s = f"{env_var}={token}\n")
    else:
        env_path = ".env"
        from dotenv import dotenv_values
        lines = []
        if os.path.exists(path = env_path):
            lines = open(
                        file = env_path, 
                        mode = "r", 
                        encoding = "utf-8").readlines()
        with open(
            file = env_path, 
            mode = "w", 
            encoding = "utf-8") as f:
            found = False
            for line in lines:
                if line.strip().startswith(
                                    prefix = f"{env_var}="):
                    f.write(
                        s = f"{env_var}={token}\n")
                    found = True
                else:
                    f.write(
                        s = line)
            if not found:
                f.write(
                    s = f"{env_var}={token}\n")
