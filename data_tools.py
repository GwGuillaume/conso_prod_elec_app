import pandas as pd


# -------------------- AJOUT DES DATES ET HEURES MANQUANTES --------------------- #
def complete_dataframe_datetimes(df, min_freq):
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

    # Rétablissement de datetime comme colonne du Dataframe
    df_full = df_full.reset_index().rename(columns={'index': 'datetime'})

    return df_full


# -------------------- SOUS-ÉCHANTILLONNAGE D'UN DATAFRAME ---------------------- #
def subsampling_in_15min(df_30min):
    """
    Transforme un DataFrame contenant des données de consommation électrique avec
    unefréquence de 30 minutes en un DataFrame avec une fréquence de 15 minutes.

    Chaque valeur de consommation est divisée équitablement en deux et dupliquée
    sur deux créneaux consécutifs de 15 minutes : à l'instant original et à +15
    minutes.

    Paramètres :
    -----------
    df_30min : pd.DataFrame
        DataFrame contenant au minimum les colonnes 'datetime' et 'consommation'.
        La colonne 'datetime' doit représenter des horodatages espacés de 30
        minutes.

    Retour :
    --------
    df_15min : pd.DataFrame
        Nouveau DataFrame contenant une ligne toutes les 15 minutes, où chaque
        valeur de consommation est divisée par deux et répartie sur deux créneaux.
    """

    # Vérification que la colonne 'datetime' est bien au format datetime
    df_30min['datetime'] = pd.to_datetime(df_30min['datetime'])

    # Création du nouveau DataFrame avec deux lignes pour chaque ligne originale :
    # une à l'heure d'origine et une autre à +15 minutes, chacune portant la moitié
    # de la consommation.
    df_15min = pd.DataFrame({
        'datetime': pd.concat([
            df_30min['datetime'],
            df_30min['datetime'] + pd.Timedelta(minutes=15)
        ], ignore_index=True),
        'consommation': pd.concat([
            df_30min['consommation'] / 2,
            df_30min['consommation'] / 2
        ], ignore_index=True)
    })

    # Tri des lignes par datetime pour conserver un ordre chronologique
    df_15min = df_15min.sort_values('datetime').reset_index(drop=True)

    return df_15min