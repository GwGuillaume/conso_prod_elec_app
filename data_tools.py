import os
import pandas as pd


# ------------- AJOUT DES DATES ET HEURES MANQUANTES AU DATAFRAME --------------- #
def complete_dataframe_datetimes(df, min_freq) -> pd.DataFrame:
    """
    Complète un DataFrame pour qu'il contienne une ligne pour chaque horodatage
    régulier entre la première et la dernière date, à la fréquence spécifiée.

    Cette fonction est utile lorsque certaines données sont manquantes dans la série
    temporelle et qu'on souhaite avoir une base régulière avec des NaN aux
    emplacements absents.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame d'entrée contenant une colonne 'datetime'.

    min_freq : str
        Fréquence temporelle à respecter entre chaque ligne.
        Exemples : '15min', '30min', '1H', etc.

    Retour :
    --------
    df_full : pd.DataFrame
        Nouveau DataFrame avec un datetime toutes les `min_freq`,
        et des valeurs NaN pour les lignes ajoutées.
    """

    # Vérification que la colonne 'datetime' est bien au format datetime
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Définition de la colonne 'datetime' comme index temporel
    df.set_index('datetime', inplace=True)

    # Création d'un index régulier égal à `min_freq` de dates de la
    # première à la dernière date du DataFrame
    full_range = pd.date_range(start=df.index.min(),
                               end=df.index.max(),
                               freq=min_freq)

    # Réindexation du DataFrame avec la plage complète (ajout de lignes avec
    # NaN si nécessaire)
    df_full = df.reindex(full_range)

    # Remplacement des NaN par la valeur 0
    df_full.fillna(value=0, inplace=True)

    # Rétablissement de datetime comme colonne du Dataframe
    df_full = df_full.reset_index().rename(columns={'index': 'datetime'})

    # Tri des lignes par datetime pour conserver un ordre chronologique
    df_full = df_full.sort_values("datetime")

    return df_full

# -------------------------- FUSION DES DATAFRAMES ----------------------------- #
def merge_conso_prod_data(conso_df_30min: pd.DataFrame,
                          prod_df_30min: pd.DataFrame) -> pd.DataFrame:
    """
    Fusionne les DataFrames de consommation et de production électriques (agrégés sur 30 minutes),
    calcule une colonne 'total', gère les valeurs nulles, puis sauvegarde le fichier résultant.

    Paramètres :
    ------------
    conso_df_30min : pd.DataFrame
        DataFrame contenant les données de consommation électrique avec une colonne 'datetime'
        et une colonne 'consommation', agrégées par tranche de 30 minutes.

    prod_df_30min : pd.DataFrame
        DataFrame contenant les données de production électrique avec une colonne 'datetime'
        et une colonne 'production', agrégées par tranche de 30 minutes.

    Retour :
    --------
    merged_df : pd.DataFrame
        DataFrame fusionné contenant les colonnes 'datetime', 'consommation', 'production' et 'total'.
        Le dataframe est également sauvegardé dans un fichier 'global.csv' à la racine du dossier 'data'.
    """

    # Fusion des deux DataFrames sur la colonne 'datetime'
    merged_df = pd.merge(conso_df_30min, prod_df_30min, on="datetime", how="inner")

    # Calcul de la colonne 'total' :
    # - consommation + production si consommation > 0
    # - sinon 0
    merged_df["total"] = merged_df["consommation"] + merged_df["production"]
    merged_df.loc[merged_df["consommation"] == 0, "total"] = 0

    # Remplacer les éventuelles valeurs manquantes par 0
    merged_df.fillna(value=0, inplace=True)

    # Sauvegarde du résultat dans un fichier CSV
    output_path = os.path.join('data', 'global.csv')
    merged_df.to_csv(output_path, sep=";", index=False)

    return merged_df


# -------------------- AFFICHAGE DES INFORMATIONS GÉNÉRALES -------------------- #
def print_general_info(display_mode: str,
                       df: pd.DataFrame,
                       mois_choisi: str | None = None) -> str:
    """
    Génère le texte descriptif des informations générales
    (consommation / production totales + moyennes adaptées).

    Paramètres supplémentaires
    --------------------------
    mois_choisi : str | None
        • Pour display_mode == "Mensuel" : "Tous" ou le mois sélectionné
        • Pour display_mode == "Hebdomadaire": "Toutes" ou le mois sélectionné
    """

    # Fonction de formatage de la puissance (W ou kW)
    def format_puissance(valeur: float) -> str:
        return f"{valeur/1000:,.2f} kW" if valeur >= 1000 else f"{valeur:,.0f} W"

    # Consommation et production totales
    total_conso = df["consommation"].sum()
    total_prod  = df["production"].sum()

    # Consommation et production moyennes
    freq = ""

    if display_mode == "Classique":
        # Moyenne par jour
        nb = df["datetime"].dt.date.nunique()
        freq = "par jour"
        moyenne_conso = total_conso / nb if nb else 0
        moyenne_prod  = total_prod  / nb if nb else 0

    elif display_mode == "Mensuel":
        if mois_choisi == "Tous":
            nb = df["datetime"].dt.to_period("M").nunique()     # Nombre de mois
            freq = "par mois"
        else:                                                   # 1 mois précis → moyenne hebdomadaire
            nb  = df["datetime"].dt.to_period("W").nunique()    # Nombre de semaines
            freq = "par semaine"
        moyenne_conso = total_conso / nb if nb else 0
        moyenne_prod  = total_prod  / nb if nb else 0

    elif display_mode == "Hebdomadaire":
        if mois_choisi == "Toutes":
            nb  = df["datetime"].dt.to_period("W").nunique()    # Moyenne hebdomadaire
            freq = "par semaine"
        else:                                                   # 1 mois précis → moyenne quotidienne
            nb  = df["datetime"].dt.date.nunique()
            freq = "par jour"
        moyenne_conso = total_conso / nb if nb else 0
        moyenne_prod  = total_prod  / nb if nb else 0

    elif display_mode == "Journée spécifique":                  # Moyenne horaire
        nb  = df["datetime"].dt.hour.nunique()
        freq = "par heure"
        moyenne_conso = total_conso / nb if nb else 0
        moyenne_prod  = total_prod  / nb if nb else 0

    # Assemblage du texte à afficher
    return f"""
**Informations générales sur la période :**

- 🔌 Consommation totale : **{format_puissance(total_conso)}**  
  Moyenne {freq} : **{format_puissance(moyenne_conso)}**

- 🌿 Production totale : **{format_puissance(total_prod)}**  
  Moyenne {freq} : **{format_puissance(moyenne_prod)}**
"""
