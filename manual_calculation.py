import streamlit as st
import pandas as pd

def update_position_values(df, idx, new_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
    """
    Actualiza los valores de posición para un ULD en el DataFrame.
    """
    row = df.loc[idx]
    restric = restricciones_df[restricciones_df["Position"] == new_position]
    
    if restric.empty:
        st.error(f"Posición {new_position} inválida.")
        return False
    
    temp_restr_sym = restric["Temp_Restriction_Symmetric"].values[0]
    temp_restr_asym = restric["Temp_Restriction_Asymmetric"].values[0]
    if tipo_carga == "simetrico":
        peso_max = temp_restr_sym if temp_restr_sym != 0 else restric["Symmetric_Max_Weight_(kg)_5%"].values[0]
    else:
        peso_max = temp_restr_asym if temp_restr_asym != 0 else restric["Asymmetric_Max_Weight_(kg)_5%"].values[0]
    
    if new_position in exclusiones_df.columns:
        excluded_positions = exclusiones_df.index[exclusiones_df[new_position] == 0].tolist()
        if any(pos in posiciones_usadas for pos in excluded_positions):
            st.error(f"La posición {new_position} está excluida por posiciones ya asignadas: {excluded_positions}")
            return False
    
    if row["Weight (KGS)"] > peso_max:
        st.error(f"El peso {row['Weight (KGS)']} kg excede el máximo permitido de {peso_max} kg para la posición {new_position}.")
        return False
        
    x_arm = restric["Average_X-Arm_(m)"].values[0]
    y_arm = restric["Average_Y-Arm_(m)"].values[0]
    
    df.at[idx, "X-arm"] = x_arm
    df.at[idx, "Y-arm"] = y_arm
    df.at[idx, "Momento X"] = round(x_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Momento Y"] = round(y_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Posición Asignada"] = new_position
    df.at[idx, "Bodega"] = restric["Bodega"].values[0]
    
    for i in df.index:
        if i != idx and isinstance(df.at[i, "Posiciones Sugeridas"], list):
            df.at[i, "Posiciones Sugeridas"] = [pos for pos in df.at[i, "Posiciones Sugeridas"] if pos != new_position]
    
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
    st.write("### Asignación Manual de Posiciones")
    st.write("Asigne posiciones manualmente a cada ULD haciendo clic en una posición sugerida o ingresándola manualmente.")

    # CSS para botones pequeños y disposición más compacta
    st.markdown(
        """
        <style>
        .small-button {
            padding: 4px 8px;
            font-size: 6px;
            margin: 1px;
            min-width: 70px;
            text-align: center;
        }
        .button-container {
            display: flex;
            flex-wrap: wrap;
            gap: 2px;
        }
        .button-col {
            flex: 0 0 25%;
            box-sizing: border-box;
            padding: 1px;
        }
        .button-label {
            font-size: 10px;
            color: #555;
            text-align: center;
            margin-top: 0px;
            margin-bottom: 0px;
            line-height: 1;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if df is None or df.empty:
        st.warning("No hay un manifiesto cargado. Por favor, cargue un manifiesto primero.")
        return

    # Asegurar índices únicos
    df = df.reset_index(drop=True)
    ulds_pendientes = df[df["Posición Asignada"] == ""].copy()
    
    if ulds_pendientes.empty:
        st.success("Todos los ULDs han sido asignados.")
    else:
        st.write(f"ULDs pendientes de asignar: {len(ulds_pendientes)}")
        
        for i in range(0, len(ulds_pendientes), 4):
            cols = st.columns(4)
            for j in range(4):
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
                            <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: {background_color};'>
                                <h4>{uld}</h4>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']} kg</p>
                                <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                <p><strong>Contour:</strong> {row['Contour']}</p>
                                <p><strong>Notas:</strong> {row['Notes']}</p>
                                <p><strong>Posiciones Sugeridas:</strong></p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        # Mostrar posiciones sugeridas como botones, 4 por fila
                        if isinstance(row["Posiciones Sugeridas"], list) and row["Posiciones Sugeridas"]:
                            # Eliminar duplicados en las posiciones sugeridas
                            posiciones_unicas = list(dict.fromkeys(row["Posiciones Sugeridas"]))
                            num_buttons = len(posiciones_unicas)
                            # Dividir en filas de máximo 4 botones
                            for row_idx in range(0, num_buttons, 4):
                                button_row = posiciones_unicas[row_idx:row_idx + 4]
                                button_cols = st.columns(4)
                                for col_idx, pos in enumerate(button_row):
                                    with button_cols[col_idx]:
                                        # Generar clave única
                                        button_key = f"{tab_prefix}_pos_button_{uld}_{idx}_{pos}_{row_idx}_{col_idx}"
                                        # Obtener peso máximo para la posición
                                        restric = restricciones_df[restricciones_df["Position"] == pos]
                                        if not restric.empty:
                                            temp_restr_sym = restric["Temp_Restriction_Symmetric"].values[0]
                                            temp_restr_asym = restric["Temp_Restriction_Asymmetric"].values[0]
                                            if tipo_carga == "simetrico":
                                                peso_max = temp_restr_sym if temp_restr_sym != 0 else restric["Symmetric_Max_Weight_(kg)_5%"].values[0]
                                            else:
                                                peso_max = temp_restr_asym if temp_restr_asym != 0 else restric["Asymmetric_Max_Weight_(kg)_5%"].values[0]
                                        else:
                                            peso_max = 0
                                        # Botón con peso máximo al pie
                                        st.markdown(
                                            f'<div class="button-col">',
                                            unsafe_allow_html=True
                                        )
                                        if st.button(
                                            pos,
                                            key=button_key,
                                            help=f"Asignar {uld} a {pos}",
                                            use_container_width=False
                                        ):
                                            if pos in posiciones_usadas:
                                                st.error(f"La posición {pos} ya está asignada.")
                                            else:
                                                success = update_position_values(
                                                    df, idx, pos, restricciones_df, tipo_carga,
                                                    posiciones_usadas, exclusiones_df
                                                )
                                                if success:
                                                    posiciones_usadas.add(pos)
                                                    rotaciones[uld] = False
                                                    df.at[idx, "Rotated"] = False
                                                    st.session_state.calculation_state.df = df.copy()
                                                    st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                                                    st.session_state.calculation_state.rotaciones = rotaciones.copy()
                                                    st.success(f"{uld} asignado a {pos}")
                                                    st.rerun()
                                        st.markdown(
                                            f'<div class="button-label">Máx: {peso_max:,.1f} kg</div>',
                                            unsafe_allow_html=True
                                        )
                                        st.markdown('</div>', unsafe_allow_html=True)
                                # Rellenar columnas vacías si hay menos de 4 botones
                                for empty_col in range(len(button_row), 4):
                                    with button_cols[empty_col]:
                                        st.empty()
                        else:
                            st.write("No hay posiciones sugeridas.")
                        # Mantener opción de ingreso manual
                        new_pos = st.text_input(f"Ingrese la posición para {uld}", key=f"{tab_prefix}_pos_{uld}_{idx}")
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
        
        for i in range(0, len(ulds_asignados), 4):
            cols = st.columns(4)
            for j in range(4):
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
                            <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: {background_color};'>
                                <h4>{uld}</h4>
                                <p><strong>Posición Asignada:</strong> {row['Posición Asignada']}</p>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']} kg</p>
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