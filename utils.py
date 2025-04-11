# utils.py
import pandas as pd
import os
import streamlit as st

def load_csv_with_fallback(uploaded_file, default_path, title):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file, sep=";", decimal=",")
    elif os.path.exists(default_path):
        return pd.read_csv(default_path, sep=";", decimal=",")
    else:
        st.error(f"No se encontró el archivo en: {default_path}. Sube el archivo manualmente.")
        return None

def clasificar_base_refinada(uld_code):
    code = str(uld_code).strip().upper()
    prefix = code[:3]
    if prefix in ["PMC", "PMQ", "PMH"]:
        return "96x125", "M"
    elif prefix in ["PAJ", "PLA"]:
        return "88x125", "A"
    elif prefix == "PAG":
        return "88x125", "G"
    elif prefix == "AKE":
        return "60.4x61.5", "D"
    elif "FLIGHT" in code or "FAK" in code:
        return "FAK", "FAK"
    else:
        return "Desconocido", "?"