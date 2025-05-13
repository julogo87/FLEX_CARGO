import pandas as pd
import streamlit as st
import numpy as np
import os
from utils import calculate_peso_maximo_efectivo

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
            restric = restricciones_df[
                (restricciones_df["Position"] == pos) &
                (restricciones_df["Pallet_Base_size_Allowed"] == base_code)
            ]
            if restric.empty:
                restric = restricciones_df[restricciones_df["Position"] == pos]  # Fallback
            if restric.empty:
                print(f"Advertencia: Posición {pos} no encontrada en restricciones_df para base {base_code}")
                continue
            peso_max = calculate_peso_maximo_efectivo(restric.iloc[0], tipo_carga)
            if peso <= peso_max:
                filtered.append(f"{pos} ({peso_max:.1f} kg)")
        return filtered

    contour_positions = {
        "SBS": ["ABL", "ABR", "BCL", "BCR", "CEL", "CER", "EFL", "EFR",
                "FHL", "FHR", "HJL", "HJR", "JKL", "JKR", "KML",
                "KMR", "MPL", "MPR", "PRL", "PRR"],
        "TT": ["TT"],
        "SS": ["SS"],
        "RR": ["RR"],
        "PRR": ["PRR"],
        "PRL": ["PRL"],
        "PP": ["PP"],
        "BULK": ["51", "52", "53"],
        "FAK": ["51", "52", "53"]
    }
    
    # Explicit check for Contour AKE or RKN
    if contour in ["AKE", "RKN"]:
        pos_ake_rkn = [
            "11R", "11L", "12R", "12L", "13R", "13L", "14R", "14L",
            "21R", "21L", "22R", "22L", "23R", "23L",
            "31R", "31L", "32R", "32L", "33R", "33L",
            "41R", "41L", "42R", "42L", "43R", "43L"
        ]
        return filter_positions(pos_ake_rkn)
    
    # Existing contour-based assignments
    if contour in contour_positions:
        return filter_positions(contour_positions[contour])
    
    # Handle LD contours, excluding AKE/RKN since they are already handled
    if contour.startswith("LD"):
        if uld.startswith("PMC"):
            pos_pmc = ["12P", "13P", "21P", "22P", "31P", "32P", "41P", "42P"]
            return filter_positions(pos_pmc)
        elif uld.startswith("PLA"):
            pos_pla = ["11", "12", "13", "14", "21", "22", "23", "31", "32", "33", "41", "42", "43"]
            return filter_positions(pos_pla)
        else:
            pos_ld = [
                "11L", "11R", "12L", "12P", "12R", "13L", "13P", "13R",
                "14L", "14R", "21L", "21P", "21R", "22L", "22P", "22R",
                "23L", "23R", "31L", "31P", "31R", "32L", "32P", "32R",
                "33L", "33R", "41L", "41P", "41R", "42L", "42P", "42R",
                "43L", "43R"
            ]
            return filter_positions(pos_ld)

    # Handle special cases based on Notes or ULD
    if "FAK" in notas or "FLIGHT" in notas or "FAK" in uld or "FLIGHT" in uld:
        return filter_positions(["51", "52", "53"])
    if contour == "P9" or "P9" in notas:
        return filter_positions(["11"])
    if "CL" in notas or contour == "CL":
        if base_code == "M":
            return filter_positions(["AB", "BC", "CE", "EF", "FH", "HJ", "JK", "KM", "MP"])
    if "CT" in notas or contour == "CT":
        if base_code == "M":
            return filter_positions(["12P", "13P", "21P", "22P", "31P", "32P", "41P", "42P", "AA", "BB", "CC", "EE", "FF", "GG", "HH", "JJ", "KK", "LL", "MM", "PP", "RR", "SS", "TT"])
        elif base_code == "K":
            return filter_positions(["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "P", "T", "S", "U", "12P", "13P", "21P", "22P", "31P", "32P", "41P", "42P"])
    return []

def update_position_values(df, idx, new_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
    row = df.loc[idx]
    restric = restricciones_df[
        (restricciones_df["Position"] == new_position) &
        (restricciones_df["Pallet_Base_size_Allowed"] == row["Baseplate Code"])
    ]
    if restric.empty:
        restric = restricciones_df[restricciones_df["Position"] == new_position]
    if restric.empty:
        st.error(f"Posición {new_position} inválida.")
        return False
    
    peso_max = calculate_peso_maximo_efectivo(restric.iloc[0], tipo_carga)
    
    print(f"Validando {new_position} para {row['Number ULD']}, peso={row['Weight (KGS)']:.1f}, peso_max={peso_max:.1f}, base_code={row['Baseplate Code']}, tipo_carga={tipo_carga}")
    
    if new_position in exclusiones_df.columns:
        excluded_positions = exclusiones_df.index[exclusiones_df[new_position] == 0].tolist()
        if any(pos in posiciones_usadas for pos in excluded_positions):
            st.error(f"La posición {new_position} está excluida por posiciones ya asignadas: {excluded_positions}")
            return False
    
    if row["Weight (KGS)"] > peso_max:
        st.error(f"El peso {row['Weight (KGS)']:.1f} kg excede el máximo permitido de {peso_max:.1f} kg para la posición {new_position}.")
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
                    st.warning(f"El peso acumulativo en {region['name']} para la posición {position} (X-arm: {x_arm}) es {cumulative_weights:.1f} kg, excede el máximo permitido de {max_weight:.1f} kg.")
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
    fuel_distribution=None,
    fuel_mode="Automático",
    tail="N342AV",
    ballast_fuel=0.0,
    performance_lw=0.0
):
    # Load add_removal.csv for the specified tail
    add_removal_path = os.path.join(tail, "add_removal.csv")
    add_removal_weight = 0.0
    add_removal_moment_x = 0.0
    add_removal_moment_y = 0.0
    
    try:
        if os.path.exists(add_removal_path):
            add_removal_df = pd.read_csv(add_removal_path, sep=";")
            # Validate required columns
            required_columns = ["component", "Weight", "Average X-Arm (m)", "Average Y-Arm (m)"]
            if not all(col in add_removal_df.columns for col in required_columns):
                st.warning(f"El archivo {add_removal_path} no contiene todas las columnas requeridas: {required_columns}")
            else:
                # Calculate total weight and moments
                add_removal_weight = add_removal_df["Weight"].sum()
                add_removal_moment_x = (add_removal_df["Weight"] * add_removal_df["Average X-Arm (m)"]).sum()
                add_removal_moment_y = (add_removal_df["Weight"] * add_removal_df["Average Y-Arm (m)"]).sum()
                st.info(f"Componentes adicionales cargados: Peso total = {add_removal_weight:.1f}")
        else:
            st.warning(f"No se encontró el archivo {add_removal_path}. Se usarán los valores BOW originales sin ajustes.")
    except Exception as e:
        st.warning(f"Error al leer {add_removal_path}: {str(e)}. Se usarán los valores BOW originales sin ajustes.")

    # Adjust BOW and moments with add_removal components
    adjusted_bow = bow + add_removal_weight
    adjusted_bow_moment_x = bow_moment_x + add_removal_moment_x
    adjusted_bow_moment_y = bow_moment_y + add_removal_moment_y

    momento_x_total = df_asignados["Momento X"].sum() if not df_asignados.empty else 0.0
    momento_y_total = df_asignados["Momento Y"].sum() if not df_asignados.empty else 0.0
    peso_total = df_asignados["Weight (KGS)"].sum() if not df_asignados.empty else 0.0

    zfw_peso = adjusted_bow + peso_total
    zfw_momento_x = adjusted_bow_moment_x + momento_x_total
    zfw_momento_y = adjusted_bow_moment_y + momento_y_total
    zfw_cg_x = round(zfw_momento_x / zfw_peso, 3) if zfw_peso != 0 else 0
    zfw_mac = round(((zfw_cg_x - lemac) / mac_length) * 1, 1)  # Convertido a %

    # MROW Calculation (includes all fuel, including taxi fuel)
    mrow = adjusted_bow + peso_total + fuel_kg
    mrow_momento_x = adjusted_bow_moment_x + momento_x_total + moment_x_fuel_tow
    mrow_momento_y = adjusted_bow_moment_y + momento_y_total + moment_y_fuel_tow
    mrow_cg_x = round(mrow_momento_x / mrow, 3) if mrow != 0 else 0
    mrow_mac = round(((mrow_cg_x - lemac) / mac_length) * 1, 1)  # Convertido a %

    tow = adjusted_bow + peso_total + fuel_kg - taxi_fuel
    tow_momento_x = adjusted_bow_moment_x + momento_x_total + moment_x_fuel_tow
    tow_momento_y = adjusted_bow_moment_y + momento_y_total + moment_y_fuel_tow
    tow_cg_x = round(tow_momento_x / tow, 3) if tow != 0 else 0
    tow_mac = round(((tow_cg_x - lemac) / mac_length) * 1, 1)  # Convertido a %

    lw = adjusted_bow + peso_total + fuel_kg - taxi_fuel - trip_fuel
    lw_momento_x = adjusted_bow_moment_x + momento_x_total + moment_x_fuel_lw
    lw_momento_y = adjusted_bow_moment_y + momento_y_total + moment_y_fuel_lw
    lw_cg_x = round(lw_momento_x / lw, 3) if lw != 0 else 0
    lw_mac = round(((lw_cg_x - lemac) / mac_length) * 1, 1)  # Convertido a %

    lateral_imbalance = abs(tow_momento_y) if tow_momento_y is not None else 0.0

    if tail != "N342AV":
        if tow <= 227000:
            mzfw_dynamic = 178000
            mzfw_formula = "MZFWD = 178000 kg (TOW <= 227000 kg)"
        else:
            mzfw_dynamic = 178000 - (tow - 227000) / 1.2
            mzfw_formula = f"MZFWD = 178000 - ({tow:.1f} - 227000) / 1.2 = {mzfw_dynamic:.1f} kg"
        mzfw_dynamic -= ballast_fuel
        mtow_dynamic = -1.2 * mzfw_dynamic + 440600
        mtow_formula = f"MTOWD = -1.2 * {mzfw_dynamic:.1f} + 440600 = {mtow_dynamic:.1f} kg"
    else:
        mzfw_dynamic = aircraft_mzfw - ballast_fuel
        mzfw_formula = None
        mtow_dynamic = aircraft_mtoc
        mtow_formula = None

    max_payload_zfw = mzfw_dynamic - adjusted_bow
    mtow_used = mtow_dynamic if tail != "N342AV" else aircraft_mtoc
    if performance_tow > 0:
        tow_limit = min(mtow_used, performance_tow)
    else:
        tow_limit = mtow_used
    max_payload_tow = tow_limit - adjusted_bow - (fuel_kg - taxi_fuel)
    if performance_lw > 0:
        lw_limit = min(aircraft_mlw, performance_lw)
    else:
        lw_limit = aircraft_mlw
    max_payload_lw = lw_limit - adjusted_bow - (fuel_kg - taxi_fuel - trip_fuel)
    underload = max(0, min(max_payload_lw, max_payload_tow, max_payload_zfw) - peso_total)

    trimset_row = trimset_df.iloc[(trimset_df.iloc[:, 0] - tow_mac).abs().argsort()[0]]
    pitch_trim = trimset_row.iloc[1]

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
        "mrow_momento_x": mrow_momento_x,
        "mrow_momento_y": mrow_momento_y,
        "mrow_mac": mrow_mac,
        "lw": lw,
        "lw_momento_x": lw_momento_x,
        "lw_momento_y": lw_momento_y,
        "lw_mac": lw_mac,
        "lateral_imbalance": lateral_imbalance,
        "underload": underload,
        "pitch_trim": pitch_trim,
        "fuel_distribution": fuel_distribution,
        "fuel_mode": fuel_mode,
        "max_payload_lw": max_payload_lw,
        "max_payload_tow": max_payload_tow,
        "max_payload_zfw": max_payload_zfw,
        "mzfw_dynamic": mzfw_dynamic,
        "mzfw_formula": mzfw_formula,
        "mtow_dynamic": mtow_dynamic,
        "mtow_formula": mtow_formula
    }