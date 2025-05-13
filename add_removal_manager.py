import streamlit as st
import pandas as pd
import os

# Directorio base
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir
aircraft_db_path = os.path.join(base_dir, "General_aircraft_database.csv")

def manage_add_removal():
    st.title("Gestión de Adiciones y Remociones")
    st.write("Modifique los componentes de adición o remoción para la aeronave seleccionada (por ejemplo, peso, brazo X, brazo Y).")

    if not os.path.exists(aircraft_db_path):
        st.error(f"No se encontró el archivo en: {aircraft_db_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    aircraft_db = pd.read_csv(aircraft_db_path, sep=";", decimal=",")

    tail = st.selectbox("Seleccione la aeronave", aircraft_db["Tail"].tolist(), key="tail_add_removal")

    aircraft_folder = os.path.normpath(os.path.join(base_dir, tail))
    add_removal_path = os.path.normpath(os.path.join(aircraft_folder, "add_removal.csv"))
    if not os.path.exists(add_removal_path):
        # Crear un DataFrame vacío con las columnas esperadas si el archivo no existe
        add_removal_df = pd.DataFrame(columns=["component", "Weight", "Average X-Arm (m)", "Average Y-Arm (m)"])
        add_removal_df.to_csv(add_removal_path, sep=";", decimal=",", index=False)
    else:
        add_removal_df = pd.read_csv(add_removal_path, sep=";", decimal=",")
        # Explicitly convert the 'component' column to string to avoid type mismatch
        add_removal_df["component"] = add_removal_df["component"].astype(str)

    # Asegurar que las columnas numéricas sean de tipo float
    numeric_columns = ["Weight", "Average X-Arm (m)", "Average Y-Arm (m)"]
    for col in numeric_columns:
        add_removal_df[col] = pd.to_numeric(add_removal_df[col], errors="coerce").fillna(0.0)

    edited_add_removal = st.data_editor(
        add_removal_df,
        column_config={
            "component": st.column_config.TextColumn("Componente", required=True),
            "Weight": st.column_config.NumberColumn("Peso (kg)", min_value=0.0, step=0.1),
            "Average X-Arm (m)": st.column_config.NumberColumn("Brazo X (m)", step=0.01),
            "Average Y-Arm (m)": st.column_config.NumberColumn("Brazo Y (m)", step=0.01)
        },
        use_container_width=True,
        num_rows="dynamic",
        key=f"add_removal_editor_{tail}"
    )

    if st.button("Guardar Adiciones/Remociones"):
        try:
            if edited_add_removal.empty:
                st.warning("La tabla está vacía. Se guardará un archivo vacío.")
            elif edited_add_removal["component"].isna().any():
                st.error("Todos los componentes deben tener un nombre válido.")
            elif edited_add_removal[numeric_columns].isna().any().any():
                st.error("Todos los campos numéricos deben tener valores válidos.")
            else:
                edited_add_removal.to_csv(add_removal_path, sep=";", decimal=",", index=False)
                st.success(f"Adiciones y remociones guardadas para la aeronave {tail} en {add_removal_path}.")
        except Exception as e:
            st.error(f"Error al guardar los datos: {str(e)}")