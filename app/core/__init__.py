# app/core/__init__.py
# -*- coding: utf-8 -*-
"""
Paquet core : logique métier (chargement, fusion, visualisation, statistiques).
"""

from .data_manager import load_merged_data, get_period_limits
from .visualization import plot_production_vs_consumption
from .statistics import get_summary_info
from .config import APP_CONFIG

__all__ = [
    "load_merged_data",
    "get_period_limits",
    "plot_production_vs_consumption",
    "get_summary_info",
    "APP_CONFIG",
]
