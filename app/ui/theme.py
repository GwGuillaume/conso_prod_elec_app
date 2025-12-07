# app/ui/theme.py
# -*- coding: utf-8 -*-
"""
Thème et styles pour l'application Streamlit.

Contient une fonction utilitaire `apply_theme()` qui applique des ajustements
CSS légers ou des constantes de style. Streamlit propose déjà un système de
thème via `.streamlit/config.toml`, mais on fournit ici quelques règles
complémentaires si besoin.
"""

import streamlit as st

def apply_theme():
    """
    Applique des réglages UI additionnels (CSS) pour améliorer l'affichage.

    Remarque :
        - Ne surcharge pas la configuration `st.set_page_config`.
        - Utilise du CSS injecté via `st.markdown` si nécessaire.
    """
    css = """
    <style>
    /* Ajustement fin des éléments */
    .stButton>button { border-radius: 10px !important; padding: 6px 12px; }
    .stRadio .st-a11y { margin-bottom: 6px; }
    .main .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
