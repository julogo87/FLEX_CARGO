# calculations.py
import pandas as pd
import streamlit as st
import numpy as np

def sugerencias_final_con_fak(row, restricciones_df, tipo_carga):
    contour = str(row["Contour"]).strip().upper()
    base_size = row["Pallet Base Size"]
    base_code = row["Baseplate Code"]
    peso = row["Weight (KGS)"]
    notas = str(row["Notes"]).upper() if pd.notna(row["Notes"]) else ""
    uld = str(row["Number ULD"]).upper()

    def filter_positions(pos_list):
        filtered = []
        for pos in pos_list:
            restric = restricciones_df[restricciones_df["Position"] == pos]
            if restric.empty:
                continue
            temp_restr_sym = restric["Temp_Restriction_Symmetric"].values[0]
            temp_restr_asym = restric["Temp_Restriction_Asymmetric"].values[0]
            if tipo_carga == "simetrico":
                peso_max = temp_restr_sym if temp_restr_sym != 0 else restric["Symmetric_Max_Weight_(kg)_5%"].values[0]
            else:
                peso_max = temp_restr_asym if temp_restr_asym != 0 else restric["Asymmetric_Max_Weight_(kg)_5%"].values[0]
            if peso <= peso_max:
                filtered.append(pos)
        return filtered

    if "FAK" in notas or "FLIGHT" in notas or "FAK" in uld or "FLIGHT" in uld:
        return filter_positions(["51", "52", "53"])
    if contour not in ["LD", "SBS", "BULK", "FAK", "", "P9", "CL", "CT"]:
        return filter_positions([contour])
    if contour == "P9" or "P9" in notas:
        return filter_positions(["11", "12", "13", "14", "21", "22", "23", "31", "32", "33", "41", "42", "43"])
    if contour == "BULK":
        return filter_positions(["51", "52", "53"])
    if "CL" in notas or contour == "CL":
        if base_code == "M":
            return filter_positions(["AB", "BC", "CE", "EF", "FH", "HJ", "JK", "KM", "MP"])
    if "CT" in notas or contour == "CT":
        if base_code == "M":
            return filter_positions(["12P", "13P", "21P", "22P", "31P", "32P", "41P", "42P", "AA", "BB", "CC", "EE", "FF", "GG", "HH", "JJ", "KK", "LL", "MM", "PP", "RR", "SS", "TT"])
        elif base_code == "K":
            return filter_positions(["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "P", "T", "S", "U", "12P", "13P", "21P", "22P", "31P", "32P", "41P", "42P"])
    if base_size == "96x238.5":
        return filter_positions(["CFR", "FJR", "JLR", "LPR"])
    if base_size == "96x317.5":
        return filter_positions(["CFG", "FJG", "JLG"])
    if contour == "SBS":
        pos_sbs = restricciones_df[
            (restricciones_df["Position"].str.len() == 3) &
            (restricciones_df["Position"].str.endswith(("L", "R"))) &
            (~restricciones_df["Position"].isin(["CFG", "FJG", "JLG", "CFR", "FJR", "JLR", "LPR"]))
        ]
        return filter_positions(pos_sbs["Position"].tolist())
    if contour == "LD":
        pos_ld = restricciones_df[
            (restricciones_df["Bodega"].isin(["LDF", "LDA"])) &
            (restricciones_df["Pallet_Base_size_Allowed"].str.contains(base_code))
        ]
        return filter_positions(pos_ld["Position"].tolist())
    if base_code == "D":
        return filter_positions(["11L", "12L", "13L", "14L", "21L", "22L", "23L", "11R", "12R", "13R", "14R", "21R", "22R", "23R", "31R", "32R", "33R", "41R", "42R", "43R"])
    return []

def update_position_values(df, idx, new_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
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

def check_cumulative_weights(df_asignados, cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df):
    if df_asignados.empty:
        return True, pd.DataFrame(columns=["Posición Asignada", "Región", "Order", "Peso Acumulativo (kg)", "Máximo Permitido (kg)", "Cumple"])
    
    excluded_positions = {"FF", "FHR", "FHL", "FH", "G", "FJR", "FJG", "GG", "HJR", "HJL"}
    
    regions = [
        {"name": "FWD", "positions": set(cumulative_restrictions_fwd_df["Position"]), "table": cumulative_restrictions_fwd_df, "direction": "forward"},
        {"name": "AFT", "positions": set(cumulative_restrictions_aft_df["Position"]), "table": cumulative_restrictions_aft_df, "direction": "backward"}
    ]

    validation_data = []
    warnings = False
    
    for index, row in df_asignados.iterrows():
        position = row["Posición Asignada"]
        x_arm = row["X-arm"]
        weight = row["Weight (KGS)"]
        
        if position in excluded_positions:
            validation_data.append({
                "Posición Asignada": position,
                "Región": "Excluida",
                "Order": None,
                "Peso Acumulativo (kg)": None,
                "Máximo Permitido (kg)": None,
                "Cumple": "N/A"
            })
            continue
        
        found_region = False
        for region in regions:
            if position in region["positions"]:
                found_region = True
                position_data = region["table"][region["table"]["Position"] == position].iloc[0]
                position_order = position_data["Order"]
                max_weight = position_data["Max_Weight"]
                
                if region["direction"] == "forward":
                    relevant_positions = df_asignados[df_asignados["Posición Asignada"].isin(region["positions"]) & ~df_asignados["Posición Asignada"].isin(excluded_positions)].merge(region["table"][["Position", "Order"]], left_on="Posición Asignada", right_on="Position")
                    cumulative_weights = relevant_positions[relevant_positions["Order"] <= position_order]["Weight (KGS)"].sum()
                else:
                    relevant_positions = df_asignados[df_asignados["Posición Asignada"].isin(region["positions"]) & ~df_asignados["Posición Asignada"].isin(excluded_positions)].merge(region["table"][["Position", "Order"]], left_on="Posición Asignada", right_on="Position")
                    cumulative_weights = relevant_positions[relevant_positions["Order"] >= position_order]["Weight (KGS)"].sum()
                
                complies = cumulative_weights <= max_weight
                if not complies:
                    st.warning(f"El peso acumulativo en {region['name']} para la posición {position} (X-arm: {x_arm}) es {cumulative_weights} kg, excede el máximo permitido de {max_weight} kg.")
                    warnings = True
                
                validation_data.append({
                    "Posición Asignada": position,
                    "Región": region["name"],
                    "Order": position_order,
                    "Peso Acumulativo (kg)": round(cumulative_weights, 3),
                    "Máximo Permitido (kg)": round(max_weight, 3),
                    "Cumple": "Sí" if complies else "No"
                })
                break
        
        if not found_region:
            validation_data.append({
                "Posición Asignada": position,
                "Región": "No Aplicable",
                "Order": None,
                "Peso Acumulativo (kg)": None,
                "Máximo Permitido (kg)": None,
                "Cumple": "N/A"
            })
    
    validation_df = pd.DataFrame(validation_data)
    return not warnings, validation_df

def calculate_final_values(
    df_asignados,
    bow,
    bow_moment_x,
    bow_moment_y,
    fuel_kg,
    taxi_fuel,
    trip_fuel,
    moment_x_fuel_tow,
    moment_y_fuel_tow,
    moment_x_fuel_lw,
    moment_y_fuel_lw,
    lemac,
    mac_length,
    aircraft_mtoc,
    aircraft_mlw,
    aircraft_mzfw,
    performance_tow,
    trimset_df,
    fuel_distribution=None,  # Nuevo parámetro
    fuel_mode="Automático"  # Nuevo parámetro
):
    momento_x_total = df_asignados["Momento X"].sum()
    momento_y_total = df_asignados["Momento Y"].sum()
    peso_total = df_asignados["Weight (KGS)"].sum()

    # Calcular ZFW
    zfw_peso = bow + peso_total
    zfw_momento_x = bow_moment_x + momento_x_total
    zfw_momento_y = bow_moment_y + momento_y_total
    zfw_cg_x = round(zfw_momento_x / zfw_peso, 3) if zfw_peso != 0 else 0
    zfw_mac = round(((zfw_cg_x - lemac) / mac_length) * 1, 1)  # Convertir a %MAC (multiplicar por 100)

    # Calcular TOW
    tow = bow + peso_total + fuel_kg - taxi_fuel
    tow_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_tow
    tow_momento_y = bow_moment_y + momento_y_total + moment_y_fuel_tow
    tow_cg_x = round(tow_momento_x / tow, 3) if tow != 0 else 0
    tow_mac = round(((tow_cg_x - lemac) / mac_length) * 1, 1)  # Convertir a %MAC (multiplicar por 100)
    mrow = tow + taxi_fuel

    # Calcular LW
    lw = bow + peso_total + fuel_kg - taxi_fuel - trip_fuel
    lw_momento_x = bow_moment_x + momento_x_total + moment_x_fuel_lw
    lw_momento_y = bow_moment_y + momento_y_total + moment_y_fuel_lw
    lw_cg_x = round(lw_momento_x / lw, 3) if lw != 0 else 0
    lw_mac = round(((lw_cg_x - lemac) / mac_length) * 1, 1)  # Convertir a %MAC (multiplicar por 100)

    lateral_imbalance = abs(tow_momento_y)
    underload = min(aircraft_mtoc, performance_tow) - bow - (fuel_kg - taxi_fuel) - peso_total

    trimset_row = trimset_df.iloc[(trimset_df.iloc[:, 0] - tow_mac).abs().argsort()[0]]
    pitch_trim = trimset_row.iloc[1]

    # Devolver los resultados, incluyendo la distribución de combustible y el modo
    return {
        "peso_total": peso_total,
        "zfw_peso": zfw_peso,
        "zfw_momento_x": zfw_momento_x,
        "zfw_momento_y": zfw_momento_y,
        "zfw_mac": zfw_mac,
        "tow": tow,
        "tow_momento_x": tow_momento_x,
        "tow_momento_y": tow_momento_y,
        "tow_mac": tow_mac,
        "mrow": mrow,
        "lw": lw,
        "lw_momento_x": lw_momento_x,
        "lw_momento_y": lw_momento_y,
        "lw_mac": lw_mac,
        "lateral_imbalance": lateral_imbalance,
        "underload": underload,
        "pitch_trim": pitch_trim,
        "fuel_distribution": fuel_distribution,  # Incluir la distribución de combustible
        "fuel_mode": fuel_mode  # Incluir el modo de combustible
    }