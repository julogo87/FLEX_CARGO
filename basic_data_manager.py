import streamlit as st
import pandas as pd
import os

# Directorio base
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir
aircraft_db_path = os.path.join(base_dir, "General_aircraft_database.csv")

def manage_basic_data():
    st.title("Gestión de Datos Básicos de Aeronaves")
    st.write("Edite los datos básicos de la aeronave seleccionada (por ejemplo, MTOW, MLW, OEW).")

    if not os.path.exists(aircraft_db_path):
        st.error(f"No se encontró el archivo en: {aircraft_db_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    aircraft_db = pd.read_csv(aircraft_db_path, sep=";", decimal=",")

    tail = st.selectbox("Seleccione la aeronave", aircraft_db["Tail"].tolist(), key="tail_basic_data")

    aircraft_folder = os.path.normpath(os.path.join(base_dir, tail))
    basic_data_path = os.path.normpath(os.path.join(aircraft_folder, "basic_data.csv"))
    if not os.path.exists(basic_data_path):
        st.error(f"No se encontró el archivo en: {basic_data_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    basic_data = pd.read_csv(basic_data_path, sep=";", decimal=",")

    st.write(f"Datos básicos de la aeronave {tail}:")
    edited_basic_data = st.data_editor(
        basic_data,
        column_config={
            "MTOW (kg)": st.column_config.NumberColumn("MTOW (kg)", min_value=0.0, step=0.1),
            "MLW": st.column_config.NumberColumn("MLW (kg)", min_value=0.0, step=0.1),
            "MZFW": st.column_config.NumberColumn("MZFW (kg)", min_value=0.0, step=0.1),
            "OEW": st.column_config.NumberColumn("OEW (kg)", min_value=0.0, step=0.1),
            "ARM": st.column_config.NumberColumn("ARM (m)", min_value=0.0, step=0.01),
            "Moment_Aircraft": st.column_config.NumberColumn("Moment Aircraft", step=0.1),
            "CG_Aircraft": st.column_config.NumberColumn("CG Aircraft (m)", min_value=0.0, step=0.01),
            "LEMAC": st.column_config.NumberColumn("LEMAC (m)", min_value=0.0, step=0.01),
            "MAC_length": st.column_config.NumberColumn("MAC Length (m)", min_value=0.0, step=0.01),
            "MRW": st.column_config.NumberColumn("MRW (kg)", min_value=0.0, step=0.1),
            "Lateral_Imbalance_Limit": st.column_config.NumberColumn("Lateral Imbalance Limit", min_value=0.0, step=0.1)
        },
        use_container_width=True,
        num_rows="fixed"
    )

    if st.button("Guardar Datos Básicos"):
        try:
            numeric_columns = ["MTOW (kg)", "MLW", "MZFW", "OEW", "ARM", "Moment_Aircraft", "CG_Aircraft", "LEMAC", "MAC_length", "MRW", "Lateral_Imbalance_Limit"]
            if edited_basic_data[numeric_columns].isna().any().any():
                st.error("Todos los campos numéricos deben tener valores válidos.")
            elif (edited_basic_data[numeric_columns] <= 0).any().any():
                st.error("Los valores numéricos deben ser mayores que cero.")
            elif edited_basic_data["MAC_length"].iloc[0] == 0:
                st.error("MAC_length no puede ser cero.")
            else:
                edited_basic_data.to_csv(basic_data_path, sep=";", decimal=",", index=False)
                st.success(f"Datos básicos guardados para la aeronave {tail} en {basic_data_path}.")
        except Exception as e:
            st.error(f"Error al guardar los datos: {str(e)}")