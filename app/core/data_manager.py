# -*- coding: utf-8 -*-
"""
Gestion centralisée du chargement, nettoyage et fusion des données
de consommation et de production électrique.
"""

from common.file_utils import load_clean_data
from common.data_tools import merge_conso_prod_data
from conso_api_tools.config import CSV_30MIN as conso_csv
from prod_api_tools.config import CSV_30MIN as prod_csv


def load_merged_data():
    """
    Charge et fusionne les données de consommation et de production.

    Retour :
        pandas.DataFrame : données fusionnées et prêtes à l'analyse
    """
    conso_df = load_clean_data(conso_csv)
    prod_df = load_clean_data(prod_csv)
    return merge_conso_prod_data(conso_df, prod_df)


def get_period_limits(df):
    """
    Renvoie les bornes min/max disponibles dans le DataFrame.

    Paramètres :
        df (pandas.DataFrame) : données

    Retour :
        tuple(datetime, datetime) : bornes temporelles disponibles
    """
    return df["datetime"].min(), df["datetime"].max()
