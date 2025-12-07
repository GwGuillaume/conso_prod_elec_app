from babel.dates import format_date
from datetime import datetime, date
from babel.dates import format_date, format_datetime

def format_date_fr(d: datetime | date, pattern="d MMMM y"):
    """
    Formate une date en français en utilisant Babel.

    Paramètres
    ----------
    d : datetime ou date
        La date à formatter.
    pattern : str
        Format Babel désiré.

    Retour
    ------
    str : date formatée en français
    """
    # Si c'est un datetime
    if isinstance(d, datetime):
        return format_datetime(d, format=pattern, locale="fr")

    # Si c'est une date : conversion en datetime (minuit)
    if isinstance(d, date):
        d = datetime(d.year, d.month, d.day)
        return format_datetime(d, format=pattern, locale="fr")

    # Sinon renvoyer tel quel
    return d
