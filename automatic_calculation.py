import streamlit as st
from calculations import update_position_values, check_cumulative_weights

def assign_single_position_pallets(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas):
    """
    Asigna automáticamente los pallets que tienen una sola posición sugerida.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
    """
    for idx, row in df[df["Posición Asignada"] == ""].iterrows():
        if len(row["Posiciones Sugeridas"]) == 1:
            # Limpiar la posición para eliminar el peso máximo
            pos = row["Posiciones Sugeridas"][0].split(" (")[0]
            if pos not in posiciones_usadas and update_position_values(df, idx, pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                posiciones_usadas.add(pos)
                df.at[idx, "Rotated"] = False

def strategy_by_cg(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length):
    """
    Estrategia de asignación basada en el centro de gravedad (CG), optimizando TOW CG y ZFW CG alrededor de 28% MAC.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        destino_inicial (str): Destino inicial (no usado en esta estrategia).
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
    
    Returns:
        tuple: (posiciones_usadas, rotaciones)
    """
    df_unassigned = df[df["Posición Asignada"] == ""].copy()  # Sin ordenar por peso
    target_mac = 28.0  # Objetivo para TOW CG y ZFW CG
    rotaciones = {}
    
    for idx, row in df_unassigned.iterrows():
        uld = row["Number ULD"]
        weight = row["Weight (KGS)"]
        # Limpiar las posiciones sugeridas para eliminar el peso máximo
        sugeridas = [pos.split(" (")[0] for pos in row["Posiciones Sugeridas"] if pos.split(" (")[0] not in posiciones_usadas]
        
        if len(sugeridas) == 1:
            pos = sugeridas[0]
            if update_position_values(df, idx, pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                posiciones_usadas.add(pos)
                rotaciones[uld] = False
                df.at[idx, "Rotated"] = False
                continue
        
        best_position = None
        best_combined_deviation = float('inf')
        
        for pos in sugeridas:
            df_temp = df.copy()
            temp_posiciones_usadas = posiciones_usadas.copy()
            if update_position_values(df_temp, idx, pos, restricciones_df, tipo_carga, temp_posiciones_usadas, exclusiones_df):
                temp_posiciones_usadas.add(pos)
                # Calcular TOW CG
                momento_x_total = df_temp[df_temp["Posición Asignada"] != ""]["Momento X"].sum()
                peso_total = df_temp[df_temp["Posición Asignada"] != ""]["Weight (KGS)"].sum()
                tow = bow + peso_total + fuel_kg - taxi_fuel
                tow_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_tow
                tow_mac = ((tow_momento_x / tow - lemac) / mac_length) * 100 if tow != 0 else 0
                tow_mac_deviation = abs(tow_mac - target_mac)
                # Calcular ZFW CG
                zfw = bow + peso_total
                zfw_momento_x = bow_moment_x + momento_x_total
                zfw_mac = ((zfw_momento_x / zfw - lemac) / mac_length) * 100 if zfw != 0 else 0
                zfw_mac_deviation = abs(zfw_mac - target_mac)
                # Combinar desviaciones (ponderadas igualmente)
                combined_deviation = tow_mac_deviation + zfw_mac_deviation
                if combined_deviation < best_combined_deviation:
                    best_combined_deviation = combined_deviation
                    best_position = pos
        
        if best_position:
            update_position_values(df, idx, best_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df)
            posiciones_usadas.add(best_position)
            rotaciones[uld] = False
            df.at[idx, "Rotated"] = False
    
    return posiciones_usadas, rotaciones

def strategy_by_aft_cg(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length):
    """
    Estrategia de asignación basada en el centro de gravedad (CG) con prioridad en colocar los pallets más pesados en las posiciones más traseras (mayor X-arm),
    optimizando TOW CG y ZFW CG alrededor de 28% MAC.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        destino_inicial (str): Destino inicial (no usado en esta estrategia).
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
    
    Returns:
        tuple: (posiciones_usadas, rotaciones)
    """
    df_unassigned = df[df["Posición Asignada"] == ""].copy()
    df_unassigned = df_unassigned.sort_values(by="Weight (KGS)", ascending=False)  # Priorizar pallets más pesados
    target_mac = 28.0  # Objetivo para TOW CG y ZFW CG
    rotaciones = {}
    
    for idx, row in df_unassigned.iterrows():
        uld = row["Number ULD"]
        weight = row["Weight (KGS)"]
        # Limpiar las posiciones sugeridas y ordenarlas por X-arm descendente
        sugeridas = [pos.split(" (")[0] for pos in row["Posiciones Sugeridas"] if pos.split(" (")[0] not in posiciones_usadas]
        
        if len(sugeridas) == 1:
            pos = sugeridas[0]
            if update_position_values(df, idx, pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                posiciones_usadas.add(pos)
                rotaciones[uld] = False
                df.at[idx, "Rotated"] = False
                continue
        
        # Ordenar posiciones sugeridas por X-arm descendente (más aft primero)
        sugeridas_with_xarm = [
            (pos, restricciones_df[restricciones_df["Position"] == pos]["Average_X-Arm_(m)"].iloc[0])
            for pos in sugeridas
            if not restricciones_df[restricciones_df["Position"] == pos].empty
        ]
        sugeridas_with_xarm.sort(key=lambda x: x[1], reverse=True)  # Mayor X-arm primero
        sugeridas = [pos for pos, _ in sugeridas_with_xarm]
        
        best_position = None
        best_combined_deviation = float('inf')
        
        for pos in sugeridas:
            df_temp = df.copy()
            temp_posiciones_usadas = posiciones_usadas.copy()
            if update_position_values(df_temp, idx, pos, restricciones_df, tipo_carga, temp_posiciones_usadas, exclusiones_df):
                temp_posiciones_usadas.add(pos)
                # Calcular TOW CG
                momento_x_total = df_temp[df_temp["Posición Asignada"] != ""]["Momento X"].sum()
                peso_total = df_temp[df_temp["Posición Asignada"] != ""]["Weight (KGS)"].sum()
                tow = bow + peso_total + fuel_kg - taxi_fuel
                tow_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_tow
                tow_mac = ((tow_momento_x / tow - lemac) / mac_length) * 100 if tow != 0 else 0
                tow_mac_deviation = abs(tow_mac - target_mac)
                # Calcular ZFW CG
                zfw = bow + peso_total
                zfw_momento_x = bow_moment_x + momento_x_total
                zfw_mac = ((zfw_momento_x / zfw - lemac) / mac_length) * 100 if zfw != 0 else 0
                zfw_mac_deviation = abs(zfw_mac - target_mac)
                # Combinar desviaciones
                combined_deviation = tow_mac_deviation + zfw_mac_deviation
                if combined_deviation < best_combined_deviation:
                    best_combined_deviation = combined_deviation
                    best_position = pos
        
        if best_position:
            update_position_values(df, idx, best_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df)
            posiciones_usadas.add(best_position)
            rotaciones[uld] = False
            df.at[idx, "Rotated"] = False
    
    return posiciones_usadas, rotaciones

def strategy_by_destination(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length):
    """
    Estrategia de asignación basada en el destino inicial, priorizando destino_inicial en posiciones MD con X-arm <= 35
    y manteniendo TOW CG y ZFW CG alrededor de 28% MAC.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        destino_inicial (str): Destino inicial para priorizar.
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
    
    Returns:
        tuple: (posiciones_usadas, rotaciones)
    """
    df_unassigned = df[df["Posición Asignada"] == ""].copy()
    df_unassigned["Matches_Destination"] = df_unassigned["ULD Final Destination"].str.strip().str.upper() == destino_inicial.upper()
    df_unassigned = df_unassigned.sort_values(by=["Matches_Destination"], ascending=False)  # Priorizar destino, no peso
    
    # Priorizar posiciones en MD con X-arm <= 35, luego LDA
    md_positions = restricciones_df[
        (restricciones_df["Bodega"] == "MD") & 
        (restricciones_df["Average_X-Arm_(m)"] <= 35)
    ]["Position"].sort_values().tolist()
    lda_positions = restricciones_df[restricciones_df["Bodega"] == "LDA"]["Position"].sort_values(ascending=False).tolist()
    preferred_positions_initial = md_positions + lda_positions
    
    target_mac = 28.0  # Objetivo para TOW CG y ZFW CG
    rotaciones = {}
    
    for idx, row in df_unassigned.iterrows():
        uld = row["Number ULD"]
        weight = row["Weight (KGS)"]
        matches_dest = row["Matches_Destination"]
        # Limpiar las posiciones sugeridas para eliminar el peso máximo
        sugeridas = [pos.split(" (")[0] for pos in row["Posiciones Sugeridas"] if pos.split(" (")[0] not in posiciones_usadas]
        
        if len(sugeridas) == 1:
            pos = sugeridas[0]
            if update_position_values(df, idx, pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                posiciones_usadas.add(pos)
                rotaciones[uld] = False
                df.at[idx, "Rotated"] = False
                continue
        
        # Seleccionar posiciones preferidas según el destino
        if matches_dest:
            preferred_positions = [pos for pos in preferred_positions_initial if pos in sugeridas and pos not in posiciones_usadas]
        else:
            preferred_positions = [pos for pos in sugeridas if pos not in posiciones_usadas]
        
        if not preferred_positions:
            preferred_positions = [pos for pos in sugeridas if pos not in posiciones_usadas]
        
        # Filtrar posiciones que mantengan TOW CG y ZFW CG cerca de 28% MAC
        best_position = None
        best_combined_deviation = float('inf')
        
        for pos in preferred_positions:
            df_temp = df.copy()
            temp_posiciones_usadas = posiciones_usadas.copy()
            if update_position_values(df_temp, idx, pos, restricciones_df, tipo_carga, temp_posiciones_usadas, exclusiones_df):
                temp_posiciones_usadas.add(pos)
                # Calcular TOW CG
                momento_x_total = df_temp[df_temp["Posición Asignada"] != ""]["Momento X"].sum()
                peso_total = df_temp[df_temp["Posición Asignada"] != ""]["Weight (KGS)"].sum()
                tow = bow + peso_total + fuel_kg - taxi_fuel
                tow_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_tow
                tow_mac = ((tow_momento_x / tow - lemac) / mac_length) * 100 if tow != 0 else 0
                tow_mac_deviation = abs(tow_mac - target_mac)
                # Calcular ZFW CG
                zfw = bow + peso_total
                zfw_momento_x = bow_moment_x + momento_x_total
                zfw_mac = ((zfw_momento_x / zfw - lemac) / mac_length) * 100 if zfw != 0 else 0
                zfw_mac_deviation = abs(zfw_mac - target_mac)
                # Combinar desviaciones
                combined_deviation = tow_mac_deviation + zfw_mac_deviation
                if combined_deviation < best_combined_deviation:
                    best_combined_deviation = combined_deviation
                    best_position = pos
        
        if best_position:
            update_position_values(df, idx, best_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df)
            posiciones_usadas.add(best_position)
            rotaciones[uld] = False
            df.at[idx, "Rotated"] = False
    
    return posiciones_usadas, rotaciones

def strategy_hybrid(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length):
    """
    Estrategia híbrida que combina destino y CG, priorizando destino_inicial en MD/LDA y optimizando TOW CG y ZFW CG
    alrededor de 28% MAC para el resto.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        destino_inicial (str): Destino inicial para priorizar.
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
    
    Returns:
        tuple: (posiciones_usadas, rotaciones)
    """
    df_unassigned = df[df["Posición Asignada"] == ""].copy()
    df_unassigned["Matches_Destination"] = df_unassigned["ULD Final Destination"].str.strip().str.upper() == destino_inicial.upper()
    df_unassigned = df_unassigned.sort_values(by=["Matches_Destination"], ascending=False)  # Priorizar destino, no peso
    
    # Definir posiciones preferidas para destino_inicial
    md_positions = restricciones_df[
        (restricciones_df["Bodega"] == "MD") & 
        (restricciones_df["Average_X-Arm_(m)"] <= 35)
    ]["Position"].sort_values().tolist()
    lda_positions = restricciones_df[restricciones_df["Bodega"] == "LDA"]["Position"].sort_values(ascending=False).tolist()
    preferred_positions_initial = md_positions + lda_positions
    
    target_mac = 28.0  # Objetivo para TOW CG y ZFW CG
    rotaciones = {}
    
    for idx, row in df_unassigned.iterrows():
        uld = row["Number ULD"]
        weight = row["Weight (KGS)"]
        matches_dest = row["Matches_Destination"]
        # Limpiar las posiciones sugeridas para eliminar el peso máximo
        sugeridas = [pos.split(" (")[0] for pos in row["Posiciones Sugeridas"] if pos.split(" (")[0] not in posiciones_usadas]
        
        if len(sugeridas) == 1:
            pos = sugeridas[0]
            if update_position_values(df, idx, pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                posiciones_usadas.add(pos)
                rotaciones[uld] = False
                df.at[idx, "Rotated"] = False
                continue
        
        # Seleccionar posiciones según el destino o CG
        if matches_dest:
            preferred_positions = [pos for pos in preferred_positions_initial if pos in sugeridas and pos not in posiciones_usadas]
        else:
            preferred_positions = [pos for pos in sugeridas if pos not in posiciones_usadas]
        
        if not preferred_positions:
            preferred_positions = [pos for pos in sugeridas if pos not in posiciones_usadas]
        
        best_position = None
        best_combined_deviation = float('inf')
        
        for pos in preferred_positions:
            df_temp = df.copy()
            temp_posiciones_usadas = posiciones_usadas.copy()
            if update_position_values(df_temp, idx, pos, restricciones_df, tipo_carga, temp_posiciones_usadas, exclusiones_df):
                temp_posiciones_usadas.add(pos)
                # Calcular TOW CG
                momento_x_total = df_temp[df_temp["Posición Asignada"] != ""]["Momento X"].sum()
                peso_total = df_temp[df_temp["Posición Asignada"] != ""]["Weight (KGS)"].sum()
                tow = bow + peso_total + fuel_kg - taxi_fuel
                tow_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_tow
                tow_mac = ((tow_momento_x / tow - lemac) / mac_length) * 100 if tow != 0 else 0
                tow_mac_deviation = abs(tow_mac - target_mac)
                # Calcular ZFW CG
                zfw = bow + peso_total
                zfw_momento_x = bow_moment_x + momento_x_total
                zfw_mac = ((zfw_momento_x / zfw - lemac) / mac_length) * 100 if zfw != 0 else 0
                zfw_mac_deviation = abs(zfw_mac - target_mac)
                # Combinar desviaciones
                combined_deviation = tow_mac_deviation + zfw_mac_deviation
                if combined_deviation < best_combined_deviation:
                    best_combined_deviation = combined_deviation
                    best_position = pos
        
        if best_position:
            update_position_values(df, idx, best_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df)
            posiciones_usadas.add(best_position)
            rotaciones[uld] = False
            df.at[idx, "Rotated"] = False
    
    return posiciones_usadas, rotaciones

def try_all_strategies(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial, optimizacion, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length, cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df):
    """
    Ejecuta la estrategia seleccionada para asignar pallets, reintentando si no se cumplen restricciones acumulativas.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        destino_inicial (str): Destino inicial para priorizar.
        optimizacion (str): Estrategia de optimización ("destino", "cg", "ambos", "aft_cg").
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
        cumulative_restrictions_fwd_df (pd.DataFrame): Restricciones acumulativas FWD.
        cumulative_restrictions_aft_df (pd.DataFrame): Restricciones acumulativas AFT.
    
    Returns:
        tuple: (posiciones_usadas, rotaciones, unassigned_pallets)
    """
    strategies = {
        "cg": strategy_by_cg,
        "destino": strategy_by_destination,
        "ambos": strategy_hybrid,
        "aft_cg": strategy_by_aft_cg
    }
    max_attempts = 2  # Reducido para evitar ciclos innecesarios
    attempt = 1
    unassigned_pallets = []
    rotaciones = {}
    
    strategy = strategies[optimizacion]
    while df["Posición Asignada"].eq("").any() and attempt <= max_attempts:
        temp_posiciones_usadas, temp_rotaciones = strategy(
            df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas.copy(),
            destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel,
            moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length
        )
        posiciones_usadas.update(temp_posiciones_usadas)
        rotaciones.update(temp_rotaciones)
        
        # Verificar restricciones acumulativas
        df_asignados = df[df["Posición Asignada"] != ""].copy()
        complies, _ = check_cumulative_weights(df_asignados, cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df)
        if not complies:
            # Desasignar pallets asignados en este intento
            df.loc[df.index.isin(df_asignados.index), "Posición Asignada"] = ""
            posiciones_usadas = set(df[df["Posición Asignada"] != ""]["Posición Asignada"].tolist())
            rotaciones = {k: v for k, v in rotaciones.items() if k in df[df["Posición Asignada"] != ""]["Number ULD"].values}
            attempt += 1
        else:
            unassigned_pallets = [(row["Number ULD"], row["Weight (KGS)"]) for _, row in df[df["Posición Asignada"] == ""].iterrows()]
            break
    
    return posiciones_usadas, rotaciones, unassigned_pallets

def automatic_assignment(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, rotaciones, destino_inicial, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel, moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length, cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df, tab_prefix=""):
    """
    Realiza la asignación automática de posiciones según la estrategia seleccionada.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        rotaciones (dict): Diccionario de rotaciones.
        destino_inicial (str): Destino inicial para priorizar.
        bow (float): Basic Operating Weight.
        bow_moment_x (float): Momento X del BOW.
        bow_moment_y (float): Momento Y del BOW.
        fuel_kg (float): Combustible total (kg).
        taxi_fuel (float): Combustible de taxi (kg).
        moment_x_fuel_tow (float): Momento X del combustible en TOW.
        moment_y_fuel_tow (float): Momento Y del combustible en TOW.
        lemac (float): Leading Edge of Mean Aerodynamic Chord.
        mac_length (float): Longitud del MAC.
        cumulative_restrictions_fwd_df (pd.DataFrame): Restricciones acumulativas FWD.
        cumulative_restrictions_aft_df (pd.DataFrame): Restricciones acumulativas AFT.
        tab_prefix (str): Prefijo para las claves de los widgets, para evitar conflictos entre pestañas.
    """
    st.write("### Cálculo Automático")
    st.write("Se asignarán todas las posiciones automáticamente según la estrategia seleccionada.")
    
    # Mapa de opciones de visualización a claves internas
    strategy_options = [
        {"label": "CG", "key": "cg"},
        {"label": "AFT CG", "key": "aft_cg"},
        {"label": "Destino", "key": "destino"},
        {"label": "Ambos", "key": "ambos"}
    ]
    optimizacion_label = st.selectbox(
        "Seleccione la estrategia de optimización",
        options=[option["label"] for option in strategy_options],
        key=f"{tab_prefix}_optimizacion"
    )
    # Obtener la clave interna correspondiente
    optimizacion = next(option["key"] for option in strategy_options if option["label"] == optimizacion_label)
    
    if st.button("Ejecutar Cálculo Automático", key=f"{tab_prefix}_ejecutar"):
        status_placeholder = st.empty()
        status_placeholder.info("Procesando...")
        
        # Asignar pallets con una sola posición sugerida
        assign_single_position_pallets(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas)
        
        # Ejecutar la estrategia seleccionada
        posiciones_usadas, rotaciones, unassigned = try_all_strategies(
            df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, destino_inicial,
            optimizacion, bow, bow_moment_x, bow_moment_y, fuel_kg, taxi_fuel,
            moment_x_fuel_tow, moment_y_fuel_tow, lemac, mac_length,
            cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df
        )
        
        status_placeholder.empty()
        
        if not unassigned:
            st.success("✅ Se pudieron asignar todos los pallets.")
        else:
            unassigned_uld = [uld for uld, _ in unassigned]
            st.warning(f"⚠️ Quedaron pallets por asignar: {', '.join(unassigned_uld)}")
        
        # Forzar actualización de la lista de pallets
        st.session_state.calculation_state.df = df.copy()
        st.session_state.calculation_state.posiciones_usadas = posiciones_usadas.copy()
        st.session_state.calculation_state.rotaciones = rotaciones.copy()
        st.rerun()