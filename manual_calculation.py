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
    st.write("Asigne posiciones manualmente a cada ULD.")

    # Verificar que el DataFrame no sea None
    if df is None or df.empty:
        st.warning("No hay un manifiesto cargado. Por favor, cargue un manifiesto primero.")
        return

    # Filtrar ULDs pendientes de asignar
    ulds_pendientes = df[df["Posición Asignada"] == ""].copy()
    
    if ulds_pendientes.empty:
        st.success("Todos los ULDs han sido asignados.")
    else:
        st.write(f"ULDs pendientes de asignar: {len(ulds_pendientes)}")
        
        # Mostrar los ULDs pendientes como tarjetas, 4 por línea
        for i in range(0, len(ulds_pendientes), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(ulds_pendientes):
                    row = ulds_pendientes.iloc[i + j]
                    idx = row.name
                    uld = row["Number ULD"]
                    with cols[j]:
                        background_color = "#f9f9f9"
                        st.markdown(
                            f"""
                            <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: {background_color};'>
                                <h4>{uld}</h4>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']} kg</p>
                                <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                <p><strong>Contour:</strong> {row['Contour']}</p>
                                <p><strong>Notas:</strong> {row['Notes']}</p>
                                <p><strong>Posiciones Sugeridas:</strong> {', '.join(row['Posiciones Sugeridas'])}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
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
                                        # Sincronizar con session_state
                                        st.session_state.calculation_state.df = df.copy()
                                        st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                                        st.session_state.calculation_state.rotaciones = rotaciones.copy()
                                        st.success(f"{uld} asignado a {new_pos}")
                            else:
                                st.warning("Por favor, ingrese una posición válida.")

    # Sección para desasignar pallets
    st.write("### Desasignar Pallets")
    st.write("Seleccione un pallet para desasignar su posición.")
    
    # Filtrar ULDs que ya tienen una posición asignada
    ulds_asignados = df[df["Posición Asignada"] != ""].copy()
    
    if ulds_asignados.empty:
        st.info("No hay ULDs asignados para desasignar.")
    else:
        st.write(f"ULDs asignados: {len(ulds_asignados)}")
        
        # Mostrar los ULDs asignados como tarjetas, 4 por línea
        for i in range(0, len(ulds_asignados), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(ulds_asignados):
                    row = ulds_asignados.iloc[i + j]
                    idx = row.name
                    uld = row["Number ULD"]
                    with cols[j]:
                        background_color = "#e6f3ff"
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
                            # Sincronizar con session_state
                            st.session_state.calculation_state.df = df.copy()
                            st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
                            st.session_state.calculation_state.rotaciones = rotaciones.copy()
                            st.success(f"Posición de {uld} desasignada.")