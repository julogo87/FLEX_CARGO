import streamlit as st
import pandas as pd
from utils import calculate_peso_maximo_efectivo

def update_position_values(df, idx, new_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
    """
    Actualiza los valores de posición para un ULD en el DataFrame.

    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        idx (int): Índice de la fila a actualizar.
        new_position (str): Nueva posición a asignar.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.

    Returns:
        bool: True si la asignación fue exitosa, False si falló.
    """
    new_position_clean = new_position.split(" (")[0] if " (" in new_position else new_position
    
    row = df.loc[idx]
    restric = restricciones_df[
        (restricciones_df["Position"] == new_position_clean) &
        (restricciones_df["Pallet_Base_size_Allowed"] == row["Baseplate Code"])
    ]
    if restric.empty:
        restric = restricciones_df[restricciones_df["Position"] == new_position_clean]
    if restric.empty:
        st.error(f"Posición {new_position_clean} inválida.")
        return False
    
    peso_max = calculate_peso_maximo_efectivo(restric.iloc[0], tipo_carga)
    
    print(f"Validando {new_position_clean} para {row['Number ULD']}, peso={row['Weight (KGS)']:.1f}, peso_max={peso_max:.1f}, base_code={row['Baseplate Code']}, tipo_carga={tipo_carga}")
    
    if new_position_clean in exclusiones_df.columns:
        excluded_positions = exclusiones_df.index[exclusiones_df[new_position_clean] == 0].tolist()
        if any(pos in posiciones_usadas for pos in excluded_positions):
            st.error(f"La posición {new_position_clean} está excluida por posiciones ya asignadas: {excluded_positions}")
            return False
    
    if row["Weight (KGS)"] > peso_max:
        st.error(f"El peso {row['Weight (KGS)']:.1f} kg excede el máximo permitido de {peso_max:.1f} kg para la posición {new_position_clean}.")
        return False
        
    x_arm = restric["Average_X-Arm_(m)"].values[0]
    y_arm = restric["Average_Y-Arm_(m)"].values[0]
    
    df.at[idx, "X-arm"] = x_arm
    df.at[idx, "Y-arm"] = y_arm
    df.at[idx, "Momento X"] = round(x_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Momento Y"] = round(y_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Posición Asignada"] = new_position_clean
    df.at[idx, "Bodega"] = restric["Bodega"].values[0]
    
    for i in df.index:
        if i != idx and isinstance(df.at[i, "Posiciones Sugeridas"], list):
            df.at[i, "Posiciones Sugeridas"] = [pos for pos in df.at[i, "Posiciones Sugeridas"] if pos.split(" (")[0] != new_position_clean]
    
    return True

def manual_assignment(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, rotaciones, tab_prefix=""):
    """
    Realiza la asignación manual de posiciones a los ULDs y permite desasignar pallets.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        rotaciones (dict): Diccionario de rotaciones.
        tab_prefix (str): Prefijo para las claves de los widgets, para evitar conflictos entre pestañas.
    """
    #st.write("### Asignación Manual de Posiciones")
    st.write("Asigne posiciones manualmente a cada ULD seleccionando una posición sugerida de la lista desplegable o ingresándola manualmente.")

    # Selección del modo de visualización
    view_mode = st.radio(
        "Seleccione el modo de visualización:",
        ["Tarjetas", "Tabla"],
        key=f"{tab_prefix}_view_mode"
    )

    # Control para ordenar
    sort_option = st.selectbox(
        "Ordenar por:",
        ["Peso", "Destino", "Contorno"],
        key=f"{tab_prefix}_sort_option"
    )

    # Mapear opciones de ordenación a columnas del DataFrame
    sort_column_map = {
        "Peso": "Weight (KGS)",
        "Destino": "ULD Final Destination",
        "Contorno": "Contour"
    }
    sort_column = sort_column_map[sort_option]

    # Ordenar el DataFrame primero por el criterio seleccionado y luego por peso descendente
    df_sorted = df.sort_values(by=[sort_column, "Weight (KGS)"], ascending=[True, False]).copy()

    st.write(f"Tipo de cargue usado: {tipo_carga}")

    # Estilos CSS
    st.markdown(
        """
        <style>
        .small-button {
            padding: 4px 8px;
            font-size: 12px;
            margin: 2px;
            min-width: 70px;
            text-align: center;
        }
        .pallet-card {
            border: 1px solid #ddd;
            padding: 8px;
            border-radius: 5px;
            background-color: #f9f9f9;
            margin-bottom: 10px;
        }
        .pallet-card p {
            margin: 2px 0;
            line-height: 1.2;
            font-size: 12px;
        }
        .pallet-card h4 {
            margin: 2px 0;
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if df is None or df.empty:
        st.warning("No hay un manifiesto cargado. Por favor, cargue un manifiesto primero.")
        return

    df = df_sorted.reset_index(drop=True)

    # Modo Tabla
    if view_mode == "Tabla":
        st.write("### Asignación por Tabla")
        ulds_pendientes = df[df["Posición Asignada"] == ""].copy()
        
        if ulds_pendientes.empty:
            st.success("Todos los ULDs han sido asignados.")
        else:
            st.write(f"ULDs pendientes de asignar: {len(ulds_pendientes)}")
            
            # Crear una copia para edición, incluyendo Weight (KGS)
            edited_df = ulds_pendientes[["Contour", "Number ULD", "Weight (KGS)", "ULD Final Destination", "Notes", "Posiciones Sugeridas", "Posición Asignada"]].copy()
            edited_df["Seleccionar Posición"] = ""
            edited_df["Ingresar Posición"] = ""
            
            # Editor de datos
            edited_data = st.data_editor(
                edited_df,
                column_config={
                    "Contour": st.column_config.TextColumn("Contour", disabled=True),
                    "Number ULD": st.column_config.TextColumn("Number ULD", disabled=True),
                    "Weight (KGS)": st.column_config.NumberColumn("Weight (KGS)", format="%.1f", disabled=True),
                    "ULD Final Destination": st.column_config.TextColumn("ULD Final Destination", disabled=True),
                    "Notes": st.column_config.TextColumn("Notes", disabled=True),
                    "Posiciones Sugeridas": st.column_config.TextColumn("Posiciones Sugeridas", disabled=True),
                    "Posición Asignada": st.column_config.TextColumn("Posición Asignada", disabled=True),
                    "Seleccionar Posición": st.column_config.SelectboxColumn(
                        "Seleccionar Posición",
                        options=[""] + sorted(set(
                            pos for row in ulds_pendientes["Posiciones Sugeridas"]
                            if isinstance(row, list)
                            for pos in row
                            if pos.split(" (")[0] not in posiciones_usadas
                        )),
                        default=""
                    ),
                    "Ingresar Posición": st.column_config.TextColumn("Ingresar Posición Manual")
                },
                use_container_width=True,
                num_rows="fixed",
                key=f"{tab_prefix}_table_editor"
            )
            
            # Botón para aplicar cambios
            if st.button("Aplicar Asignaciones", key=f"{tab_prefix}_apply_table"):
                for idx in edited_data.index:
                    row = edited_data.loc[idx]
                    uld = row["Number ULD"]
                    selected_pos = row["Seleccionar Posición"]
                    manual_pos = row["Ingresar Posición"]
                    original_idx = df[df["Number ULD"] == uld].index[0]
                    
                    # Usar la posición seleccionada o la ingresada manualmente
                    new_pos = selected_pos if selected_pos else manual_pos
                    if new_pos:
                        if new_pos.split(" (")[0] in posiciones_usadas:
                            st.error(f"La posición {new_pos.split(' (')[0]} ya está asignada.")
                        else:
                            success = update_position_values(
                                df, original_idx, new_pos, restricciones_df, tipo_carga,
                                posiciones_usadas, exclusiones_df
                            )
                            if success:
                                posiciones_usadas.add(new_pos.split(" (")[0])
                                rotaciones[uld] = False
                                df.at[original_idx, "Rotated"] = False
                                st.session_state.calculation_state.df = df.copy()
                                st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                                st.session_state.calculation_state.rotaciones = rotaciones.copy()
                                st.success(f"{uld} asignado a {new_pos.split(' (')[0]}")
                st.rerun()

    # Modo Tarjetas
    else:
        st.write("### Asignación por Tarjetas")
        ulds_pendientes = df[df["Posición Asignada"] == ""].copy()
        
        if ulds_pendientes.empty:
            st.success("Todos los ULDs han sido asignados.")
        else:
            st.write(f"ULDs pendientes de asignar: {len(ulds_pendientes)}")
            
            for i in range(0, len(ulds_pendientes), 5):
                cols = st.columns(5)
                for j in range(5):
                    if i + j < len(ulds_pendientes):
                        row = ulds_pendientes.iloc[i + j]
                        idx = row.name
                        uld = row["Number ULD"]
                        with cols[j]:
                            contour = str(row["Contour"]).strip().upper()
                            color_map = {
                                "LD": "#e6f3ff", "SBS": "#f0e6ff", "BULK": "#e6ffe6",
                                "FAK": "#fff0e6", "P9": "#ffe6e6", "CL": "#e6e6ff",
                                "CT": "#e6ffff", "": "#f9f9f9"
                            }
                            background_color = color_map.get(contour, "#f9f9f9")
                            st.markdown(
                                f"""
                                <div class='pallet-card' style='background-color: {background_color};'>
                                    <h4>{uld}</h4>
                                    <p><strong>Peso:</strong> {row['Weight (KGS)']:.1f} kg</p>
                                    <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                    <p><strong>Contour:</strong> {row['Contour']}</p>
                                    <p><strong>Notas:</strong> {row['Notes']}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            if isinstance(row["Posiciones Sugeridas"], list) and row["Posiciones Sugeridas"]:
                                available_positions = [pos for pos in row["Posiciones Sugeridas"] if pos.split(" (")[0] not in posiciones_usadas]
                                if available_positions:
                                    selected_pos = st.selectbox(
                                        f"Seleccione posición para {uld}",
                                        [""] + available_positions,
                                        key=f"{tab_prefix}_pos_select_{uld}_{idx}",
                                        label_visibility="collapsed"
                                    )
                                    if selected_pos:
                                        if selected_pos.split(" (")[0] in posiciones_usadas:
                                            st.error(f"La posición {selected_pos.split(' (')[0]} ya está asignada.")
                                        else:
                                            success = update_position_values(
                                                df, idx, selected_pos, restricciones_df, tipo_carga,
                                                posiciones_usadas, exclusiones_df
                                            )
                                            if success:
                                                posiciones_usadas.add(selected_pos.split(" (")[0])
                                                rotaciones[uld] = False
                                                df.at[idx, "Rotated"] = False
                                                st.session_state.calculation_state.df = df.copy()
                                                st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                                                st.session_state.calculation_state.rotaciones = rotaciones.copy()
                                                st.success(f"{uld} asignado a {selected_pos.split(' (')[0]}")
                                                st.rerun()
                                else:
                                    st.write("No hay posiciones sugeridas disponibles.")
                            else:
                                st.write("No hay posiciones sugeridas.")
                            new_pos = st.text_input(
                                f"Ingrese posición manualmente para {uld}",
                                key=f"{tab_prefix}_pos_manual_{uld}_{idx}",
                                placeholder="Ej: 11L"
                            )
                            if st.button("Asignar Posición", key=f"{tab_prefix}_assign_{uld}_{idx}"):
                                if new_pos:
                                    if new_pos in posiciones_usadas:
                                        st.error("La posición ya está asignada a otro ULD.")
                                    else:
                                        if update_position_values(df, idx, new_pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                                            posiciones_usadas.add(new_pos)
                                            rotaciones[uld] = False
                                            df.at[idx, "Rotated"] = False
                                            st.session_state.calculation_state.df = df.copy()
                                            st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                                            st.session_state.calculation_state.rotaciones = rotaciones.copy()
                                            st.success(f"{uld} asignado a {new_pos}")
                                            st.rerun()

    # Sección para desasignar pallets
    st.write("### Desasignar Pallets")
    st.write("Seleccione un pallet para desasignar su posición.")
    
    ulds_asignados = df[df["Posición Asignada"] != ""].copy()
    
    if ulds_asignados.empty:
        st.info("No hay ULDs asignados para desasignar.")
    else:
        st.write(f"ULDs asignados: {len(ulds_asignados)}")
        
        for i in range(0, len(ulds_asignados), 5):
            cols = st.columns(5)
            for j in range(5):
                if i + j < len(ulds_asignados):
                    row = ulds_asignados.iloc[i + j]
                    idx = row.name
                    uld = row["Number ULD"]
                    with cols[j]:
                        contour = str(row["Contour"]).strip().upper()
                        color_map = {
                            "LD": "#e6f3ff", "SBS": "#f0e6ff", "BULK": "#e6ffe6",
                            "FAK": "#fff0e6", "P9": "#ffe6e6", "CL": "#e6e6ff",
                            "CT": "#e6ffff", "": "#f9f9f9"
                        }
                        background_color = color_map.get(contour, "#e6f3ff")
                        st.markdown(
                            f"""
                            <div class='pallet-card' style='background-color: {background_color};'>
                                <h4>{uld}</h4>
                                <p><strong>Posición Asignada:</strong> {row['Posición Asignada']}</p>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']:.1f} kg</p>
                                <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                <p><strong>Contour:</strong> {row['Contour']}</p>
                                <p><strong>Notas:</strong> {row['Notes']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if st.button("Desasignar", key=f"{tab_prefix}_deassign_{uld}_{idx}"):
                            position_to_remove = df.at[idx, "Posición Asignada"]
                            df.at[idx, "Posición Asignada"] = ""
                            df.at[idx, "X-arm"] = None
                            df.at[idx, "Y-arm"] = None
                            df.at[idx, "Momento X"] = None
                            df.at[idx, "Momento Y"] = None
                            df.at[idx, "Bodega"] = None
                            df.at[idx, "Rotated"] = False
                            if position_to_remove in posiciones_usadas:
                                posiciones_usadas.remove(position_to_remove)
                            if uld in rotaciones:
                                del rotaciones[uld]
                            st.session_state.calculation_state.df = df.copy()
                            st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                            st.session_state.calculation_state.rotaciones = rotaciones.copy()
                            st.success(f"Posición de {uld} desasignada.")
                            st.rerun()