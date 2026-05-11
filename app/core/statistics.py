# -*- coding: utf-8 -*-
"""
Calculs statistiques et indicateurs énergétiques :

- Totaux de consommation et de production
- Moyennes journalières / horaires
- Ratios d'autoconsommation
- Statistiques synthétiques pour l'affichage Streamlit
"""

import pandas as pd
import common.data_tools as dt


# ---------------------------------------------------------------
# ⚡️ Statistiques principales
# ---------------------------------------------------------------

def compute_summary(df: pd.DataFrame) -> dict:
    """
    Calcule les totaux et ratios sur la période sélectionnée.

    Paramètres :
        df (pd.DataFrame) : données fusionnées contenant les colonnes :
            - 'conso' : consommation électrique (Wh)
            - 'prod' : production photovoltaïque (Wh)
            - 'total' : somme conso + prod

    Retour :
        dict : dictionnaire contenant les statistiques principales
    """
    total_conso = df["consommation"].sum()
    total_prod = df["production"].sum()
    total_energy = df["total"].sum()

    ratio_autoconso = (total_prod / total_conso * 100) if total_conso else 0
    ratio_surplus = ((total_prod - total_conso) / total_prod * 100) if total_prod else 0

    return {
        "total_conso_kWh": round(
            number = total_conso / 1000, 
            ndigits = 2),
        "total_prod_kWh": round(
            number = total_prod / 1000, 
            ndigits = 2),
        "total_energy_kWh": round(
            number = total_energy / 1000, 
            ndigits = 2),
        "autoconsommation_%": round(
            number = ratio_autoconso, 
            ndigits = 2),
        "surplus_%": round(
            number = ratio_surplus, 
            ndigits = 2)
    }

def get_summary_info(df: pd.DataFrame, mode: str) -> str:
    """
    Renvoie une chaine Markdown contenant les informations générales
    (production, consommation, totaux) pour la période sélectionnée.

    Paramètres :
        df (pd.DataFrame) : données filtrées
        mode (str) : mode d'affichage (utilisé pour adapter le texte si besoin)

    Retour :
        str : contenu Markdown prêt à être affiché dans Streamlit (st.markdown)
    """
    # la fonction print_general_info de common.data_tools renvoie déjà un texte formaté
    try:
        info = dt.print_general_info(
            display_mode = mode, 
            df = df)
    except Exception:
        # fallback minimal si la fonction n'existe pas ou échoue
        info = (
            f"**Période** : {df['datetime'].min()} → {df['datetime'].max()}\n\n"
            f"- Lignes : {len(df)}\n"
        )
    return info


# ---------------------------------------------------------------
# 📆 Moyennes par période
# ---------------------------------------------------------------

def compute_daily_average(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la moyenne quotidienne de consommation et de production.

    Retour :
        pd.DataFrame : tableau des moyennes par jour.
    """
    df_daily = df.resample(
        rule = "D", 
        on = "datetime").sum(numeric_only = True)
    return df_daily[["conso", "prod", "total"]].round(decimals = 2)


# ---------------------------------------------------------------
# 📊 Statistiques tabulaires pour affichage Streamlit
# ---------------------------------------------------------------

def compute_basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Génère un tableau synthétique des statistiques principales
    à afficher dans Streamlit.

    Paramètres :
        df (pd.DataFrame) : données fusionnées avec colonnes
            'datetime', 'conso', 'prod', 'total'.

    Retour :
        pd.DataFrame : tableau formaté contenant les indicateurs
                       principaux sur la période.
    """
    if df.empty:
        return pd.DataFrame([{
            "Indicateur": "Aucune donnée disponible",
            "Valeur": "-"
        }])

    summary = compute_summary(df)

    # Construction d'un tableau propre pour affichage
    data = [
        ("Consommation totale (kWh)", summary["total_conso_kWh"]),
        ("Production totale (kWh)", summary["total_prod_kWh"]),
        ("Énergie totale (kWh)", summary["total_energy_kWh"]),
        ("Autoconsommation (%)", summary["autoconsommation_%"]),
        ("Surplus de production (%)", summary["surplus_%"]),
        ("Durée analysée (jours)", (df["datetime"].max() - 
                                    df["datetime"].min()).days + 1),
    ]

    stats_df = pd.DataFrame(
        data = data, 
        columns = ["Indicateur", "Valeur"])
    return stats_df
