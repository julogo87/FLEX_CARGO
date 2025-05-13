import streamlit as st
import os
import json
import pandas as pd
from io import BytesIO
import base64

def manage_calculation_history():
    st.title("Historial de Cálculos")
    st.write("Lista de cálculos de peso y balance almacenados en la carpeta Output.")

    # Directorio base
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "Output")

    if not os.path.exists(output_dir):
        st.error(f"No se encontró la carpeta Output en: {output_dir}. Asegúrate de que exista y contenga archivos JSON.")
        return

    # Obtener lista de archivos JSON
    json_files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
    if not json_files:
        st.info("No hay cálculos almacenados en la carpeta Output.")
        return

    # Preparar datos para la tabla
    history_data = []
    for json_file in json_files:
        json_path = os.path.join(output_dir, json_file)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            flight_info = data.get("flight_info", {})
            calculated_values = data.get("calculated_values", {})
            manifest_data = data.get("manifest_data", [])

            # Calcular peso total de carga y posiciones asignadas
            manifest_df = pd.DataFrame(manifest_data)
            total_carga = manifest_df["Weight (KGS)"].sum() if not manifest_df.empty else 0.0
            posiciones_asignadas = len(manifest_df[manifest_df["Posición Asignada"] != ""]) if not manifest_df.empty else 0

            # Extraer usuario y licencia del nombre del archivo
            filename_parts = json_file.split("_W&B_")
            if len(filename_parts) > 1:
                user_license = filename_parts[1].replace(".json", "")
                user_parts = user_license.rsplit("_", 1)
                usuario = user_parts[0] if len(user_parts) > 1 else "Desconocido"
                licencia = user_parts[1] if len(user_parts) > 1 else "Sin Licencia"
            else:
                usuario = "Desconocido"
                licencia = "Sin Licencia"

            # Calcular TakeOff Fuel
            takeoff_fuel = calculated_values.get("fuel_kg", 0.0) - calculated_values.get("taxi_fuel", 0.0)

            # Buscar archivo Excel correspondiente
            # Extraer la parte del nombre antes de "_W&B_" (sin usuario ni licencia)
            json_base = filename_parts[0] if len(filename_parts) > 1 else os.path.splitext(json_file)[0]
            excel_path = None
            for f in os.listdir(output_dir):
                if f.endswith(".xlsm") and f.startswith(json_base):
                    excel_path = os.path.join(output_dir, f)
                    break

            history_data.append({
                "Matrícula": flight_info.get("matricula", "N/A"),
                "Número de Vuelo": flight_info.get("numero_vuelo", "N/A"),
                "Fecha": flight_info.get("fecha_vuelo", "N/A"),
                "Ruta": flight_info.get("ruta_vuelo", "N/A"),
                "Peso Total de Carga (kg)": total_carga,
                "BOW (kg)": calculated_values.get("bow", 0.0),
                "TakeOff Fuel (kg)": takeoff_fuel,
                "MZFWD (kg)": calculated_values.get("mzfw_dynamic", 0.0),
                "Trip Fuel (kg)": calculated_values.get("trip_fuel", 0.0),
                "TOW CG (% MAC)": calculated_values.get("tow_mac", 0.0),
                "ZFW CG (% MAC)": calculated_values.get("zfw_mac", 0.0),
                "ZFW (kg)": calculated_values.get("zfw_peso", 0.0),
                "TOW (kg)": calculated_values.get("tow", 0.0),
                "Underload (kg)": calculated_values.get("underload", 0.0),
                "Posiciones Asignadas": posiciones_asignadas,
                "Usuario": usuario,
                "Licencia": licencia,
                "JSON File": json_path,
                "Excel File": excel_path  # Puede ser None si no se encuentra
            })

        except Exception as e:
            st.warning(f"Error al leer {json_file}: {str(e)}")
            continue

    # Crear DataFrame para la tabla
    history_df = pd.DataFrame(history_data)

    # Mostrar tabla
    st.write("### Lista de Cálculos")
    st.dataframe(
        history_df[[
            "Matrícula", "Número de Vuelo", "Fecha", "Ruta", "Peso Total de Carga (kg)",
            "BOW (kg)", "TakeOff Fuel (kg)", "MZFWD (kg)", "Trip Fuel (kg)",
            "TOW CG (% MAC)", "ZFW CG (% MAC)", "ZFW (kg)", "TOW (kg)",
            "Underload (kg)", "Posiciones Asignadas", "Usuario", "Licencia"
        ]],
        column_config={
            "Matrícula": st.column_config.TextColumn("Matrícula"),
            "Número de Vuelo": st.column_config.TextColumn("Número de Vuelo"),
            "Fecha": st.column_config.TextColumn("Fecha"),
            "Ruta": st.column_config.TextColumn("Ruta"),
            "Peso Total de Carga (kg)": st.column_config.NumberColumn("Peso Total de Carga (kg)", format="%.1f"),
            "BOW (kg)": st.column_config.NumberColumn("BOW (kg)", format="%.1f"),
            "TakeOff Fuel (kg)": st.column_config.NumberColumn("TakeOff Fuel (kg)", format="%.1f"),
            "MZFWD (kg)": st.column_config.NumberColumn("MZFWD (kg)", format="%.1f"),
            "Trip Fuel (kg)": st.column_config.NumberColumn("Trip Fuel (kg)", format="%.1f"),
            "TOW CG (% MAC)": st.column_config.NumberColumn("TOW CG (% MAC)", format="%.1f"),
            "ZFW CG (% MAC)": st.column_config.NumberColumn("ZFW CG (% MAC)", format="%.1f"),
            "ZFW (kg)": st.column_config.NumberColumn("ZFW (kg)", format="%.1f"),
            "TOW (kg)": st.column_config.NumberColumn("TOW (kg)", format="%.1f"),
            "Underload (kg)": st.column_config.NumberColumn("Underload (kg)", format="%.1f"),
            "Posiciones Asignadas": st.column_config.NumberColumn("Posiciones Asignadas"),
            "Usuario": st.column_config.TextColumn("Usuario"),
            "Licencia": st.column_config.TextColumn("Licencia")
        },
        use_container_width=True
    )

    # Sección para previsualización
    st.write("### Previsualización de Archivos")
    selected_file = st.selectbox(
        "Seleccione un cálculo para previsualizar",
        history_df.index,
        format_func=lambda x: f"{history_df.loc[x, 'Número de Vuelo']} - {history_df.loc[x, 'Fecha']}"
    )

    if selected_file is not None:
        json_path = history_df.loc[selected_file, "JSON File"]
        excel_path = history_df.loc[selected_file, "Excel File"]

        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Previsualizar JSON**")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    json_content = json.load(f)
                st.json(json_content)
                json_bytes = json.dumps(json_content, indent=4, ensure_ascii=False).encode('utf-8')
                st.download_button(
                    label="Descargar JSON",
                    data=json_bytes,
                    file_name=os.path.basename(json_path),
                    mime="application/json",
                    key=f"download_json_{selected_file}"
                )
            else:
                st.error("El archivo JSON no está disponible.")

        with col2:
            st.write("**Previsualizar Excel**")
            if excel_path and os.path.exists(excel_path):
                try:
                    # Intentar leer el archivo .xlsm con openpyxl como motor
                    excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
                    sheet_names = excel_file.sheet_names
                    if not sheet_names:
                        st.error("El archivo Excel no contiene hojas válidas para previsualizar.")
                    else:
                        # Leer la primera hoja disponible
                        excel_df = pd.read_excel(excel_path, sheet_name=sheet_names[0], engine='openpyxl')
                        st.dataframe(excel_df, use_container_width=True)
                        with open(excel_path, "rb") as f:
                            excel_bytes = f.read()
                        st.download_button(
                            label="Descargar Excel",
                            data=excel_bytes,
                            file_name=os.path.basename(excel_path),
                            mime="application/vnd.ms-excel.sheet.macroEnabled.12",
                            key=f"download_excel_{selected_file}"
                        )
                except Exception as e:
                    st.error(f"No se pudo previsualizar el archivo Excel (.xlsm): {str(e)}")
                    st.write("**Posibles razones del error:**")
                    st.write("- El archivo podría estar protegido con contraseña.")
                    st.write("- El archivo podría contener macros o formatos no soportados.")
                    st.write("- Puede haber un problema con el motor de lectura (openpyxl).")
                    st.write("Puedes descargar el archivo para verlo en Excel.")
                    with open(excel_path, "rb") as f:
                        excel_bytes = f.read()
                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name=os.path.basename(excel_path),
                        mime="application/vnd.ms-excel.sheet.macroEnabled.12",
                        key=f"download_excel_fallback_{selected_file}"
                    )
            else:
                st.error("El archivo Excel no está disponible. Asegúrate de que el archivo .xlsm correspondiente esté en la carpeta Output.")
                st.write(f"**Nombre base del archivo JSON (sin usuario ni licencia):** {json_base}")