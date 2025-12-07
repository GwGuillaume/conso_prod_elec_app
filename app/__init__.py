# app/__init__.py
# -*- coding: utf-8 -*-
"""
Paquet 'app' : point d'accès aux sous-modules UI et core.
"""

from .core import data_manager, visualization, statistics, config
from .ui import layout, widgets, theme

__all__ = [
    "data_manager",
    "visualization",
    "statistics",
    "config",
    "layout",
    "widgets",
    "theme",
]
