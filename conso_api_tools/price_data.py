# -*- coding: utf-8 -*-
"""Téléchargement et normalisation de séries de prix de consommation en euros/kWh."""

import io
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests


DEFAULT_PRICE_OUTPUT_PATH = Path("data/conso/consumption_prices.csv")


def _normalize_price_dataframe(price_df: pd.DataFrame) -> pd.DataFrame:
    """Normalise un DataFrame de prix vers un format standard."""
    if price_df.empty:
        return pd.DataFrame(columns=["datetime", "price_eur_per_kwh"])

    datetime_col = None
    for candidate in ["datetime", "date", "timestamp", "time"]:
        if candidate in price_df.columns:
            datetime_col = candidate
            break

    price_col = None
    for candidate in ["price_eur_per_kwh", "price_per_kwh", "price", "value", "cost"]:
        if candidate in price_df.columns:
            price_col = candidate
            break

    if datetime_col is None or price_col is None:
        raise ValueError("Le fichier de prix ne contient pas de colonnes datetime/price reconnues")

    normalized = price_df[[datetime_col, price_col]].copy()
    normalized.columns = ["datetime", "price_eur_per_kwh"]
    normalized["datetime"] = pd.to_datetime(normalized["datetime"], errors="coerce")
    normalized = normalized.dropna(subset=["datetime", "price_eur_per_kwh"]).sort_values("datetime")
    return normalized.reset_index(drop=True)


def load_price_history(price_path: str | Path | None = None) -> pd.DataFrame | None:
    """Charge une série de prix depuis un fichier CSV local."""
    resolved_path = Path(price_path) if price_path is not None else DEFAULT_PRICE_OUTPUT_PATH
    if not resolved_path.exists():
        return None

    price_df = pd.read_csv(resolved_path, sep=";")
    if price_df.empty:
        return None
    return _normalize_price_dataframe(price_df)


def download_price_history(
    output_path: str | Path | None = None,
    source_url: str | None = None,
    *,
    timeout_seconds: int = 30,
) -> pd.DataFrame:
    """Télécharge une série de prix depuis une URL ou un fichier local et la sauvegarde en CSV."""
    resolved_output = Path(output_path) if output_path is not None else DEFAULT_PRICE_OUTPUT_PATH
    resolved_url = source_url or os.getenv("PRICE_DATA_URL")

    if not resolved_url:
        raise RuntimeError("Aucune source de prix configurée. Définissez PRICE_DATA_URL ou fournissez un fichier local.")

    if resolved_url.startswith(("http://", "https://")):
        response = requests.get(resolved_url, timeout=timeout_seconds)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "csv" in content_type or resolved_url.endswith(".csv"):
            price_df = pd.read_csv(io.StringIO(response.text))
        else:
            payload = response.json()
            if isinstance(payload, list):
                price_df = pd.DataFrame(payload)
            elif isinstance(payload, dict):
                if isinstance(payload.get("data"), list):
                    price_df = pd.DataFrame(payload["data"])
                elif isinstance(payload.get("prices"), list):
                    price_df = pd.DataFrame(payload["prices"])
                else:
                    raise ValueError("Le format JSON de prix n'est pas pris en charge")
            else:
                raise ValueError("Le format de réponse prix n'est pas pris en charge")
    else:
        price_df = pd.read_csv(resolved_url, sep=";")

    normalized = _normalize_price_dataframe(price_df)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(resolved_output, sep=";", index=False)
    return normalized
