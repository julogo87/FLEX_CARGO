import streamlit as st
import pandas as pd
import os

# Directorio base
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir
aircraft_db_path = os.path.join(base_dir, "General_aircraft_database.csv")

def manage_temporary_restrictions():
    st.title("Gestión de Restricciones Temporales")
    st.write("Modifique las restricciones temporales para las posiciones de cualquier aeronave (en kg). Deje en 0 para usar las restricciones predeterminadas.")

    if not os.path.exists(aircraft_db_path):
        st.error(f"No se encontró el archivo en: {aircraft_db_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    aircraft_db = pd.read_csv(aircraft_db_path, sep=";", decimal=",")

    tail = st.selectbox("Seleccione la aeronave para modificar restricciones", aircraft_db["Tail"].tolist(), key="tail_restrictions")

    aircraft_folder = os.path.normpath(os.path.join(base_dir, tail))
    restrictions_path = os.path.normpath(os.path.join(aircraft_folder, "MD_LD_BULK_restrictions.csv"))
    if not os.path.exists(restrictions_path):
        st.error(f"No se encontró el archivo en: {restrictions_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    restricciones_df = pd.read_csv(restrictions_path, sep=";", decimal=",")
    restricciones_df.columns = [col.strip().replace(" ", "_") for col in restricciones_df.columns]
    restricciones_df["Temp_Restriction_Symmetric"] = pd.to_numeric(restricciones_df["Temp_Restriction_Symmetric"], errors="coerce").fillna(0)
    restricciones_df["Temp_Restriction_Asymmetric"] = pd.to_numeric(restricciones_df["Temp_Restriction_Asymmetric"], errors="coerce").fillna(0)

    edited_restricciones = st.data_editor(
        restricciones_df[["Position", "Bodega", "Temp_Restriction_Symmetric", "Temp_Restriction_Asymmetric"]],
        column_config={
            "Position": st.column_config.TextColumn("Posición", disabled=True),
            "Bodega": st.column_config.TextColumn("Bodega", disabled=True),
            "Temp_Restriction_Symmetric": st.column_config.NumberColumn("Restricción Temporal Simétrica (kg)", min_value=0, step=1),
            "Temp_Restriction_Asymmetric": st.column_config.NumberColumn("Restricción Temporal Asimétrica (kg)", min_value=0, step=1)
        },
        use_container_width=True,
        num_rows="fixed"
    )

    restricciones_df["Temp_Restriction_Symmetric"] = edited_restricciones["Temp_Restriction_Symmetric"]
    restricciones_df["Temp_Restriction_Asymmetric"] = edited_restricciones["Temp_Restriction_Asymmetric"]

    if st.button("Guardar Restricciones Temporales"):
        restricciones_df.to_csv(restrictions_path, sep=";", decimal=",", index=False)
        st.success(f"Restricciones temporales guardadas para la aeronave {tail}.")