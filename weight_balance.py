import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from io import StringIO, BytesIO
import copy
try:
    from utils import load_csv_with_fallback, clasificar_base_refinada
    from calculations import sugerencias_final_con_fak, check_cumulative_weights, calculate_final_values
    from manual_calculation import manual_assignment
    from automatic_calculation import automatic_assignment
    from visualizations import print_final_summary, plot_main_deck, plot_lower_decks
    from data_models import FlightData, AircraftData, CalculationState, FinalResults
except ImportError as e:
    st.error(f"Error al importar módulos: {str(e)}. Verifique que todos los archivos necesarios estén en el directorio correcto.")
    st.stop()

# Directorio base
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir
aircraft_db_path = os.path.join(base_dir, "General_aircraft_database.csv")

def weight_balance_calculation():
    st.title("Sistema de Cálculo de Peso y Balance")

    # Contenido principal en una sola columna
    st.markdown('<div id="carga_datos_iniciales_section"></div>', unsafe_allow_html=True)
    st.subheader("Carga de Datos Iniciales")
    
    default_flight_data = {
        "operador": "",
        "numero_vuelo": "",
        "matricula": "",
        "fecha_vuelo": "",
        "hora_vuelo": "",
        "ruta_vuelo": "",
        "revision": "",
        "destino_inicial": "",
        "fuel_kg": 0.0,
        "trip_fuel": 0.0,
        "taxi_fuel": 0.0,
        "tipo_carga": "Simétrico",
        "takeoff_runway": "",
        "rwy_condition": "Dry",
        "flaps_conf": "1+F",
        "temperature": 0.0,
        "air_condition": "On",
        "anti_ice": "Off",
        "qnh": 1013.0,
        "performance_tow": 0.0,
        "performance_lw": 0.0,
        "passengers_cockpit": 0,
        "passengers_supernumerary": 0,
        "ballast_fuel": 0.0
    }
    
    default_calc_state = {
        "df": None,
        "posiciones_usadas": set(),
        "rotaciones": {},
        "bow": 0.0,
        "bow_moment_x": 0.0,
        "bow_moment_y": 0.0,
        "moment_x_fuel_tow": 0.0,
        "moment_y_fuel_tow": 0.0,
        "moment_x_fuel_lw": 0.0,
        "moment_y_fuel_lw": 0.0,
        "passengers_cockpit_total_weight": 0.0,
        "passengers_cockpit_total_moment_x": 0.0,
        "passengers_supernumerary_total_weight": 0.0,
        "passengers_supernumerary_total_moment_x": 0.0,
        "fuel_distribution": {
            "Outer Tank LH": 0.0,
            "Outer Tank RH": 0.0,
            "Inner Tank LH": 0.0,
            "Inner Tank RH": 0.0,
            "Center Tank": 0.0,
            "Trim Tank": 0.0
        },
        "fuel_mode": "Automático"
    }

    if "json_imported" in st.session_state and st.session_state.json_imported:
        try:
            json_data = json.load(st.session_state.json_imported)
            
            flight_info = json_data.get("flight_info", {})
            calculated_values = json_data.get("calculated_values", {})
            passengers = json_data.get("passengers", {})
            takeoff_conditions = json_data.get("takeoff_conditions", {})
            manifest_data = json_data.get("manifest_data", [])
            posiciones_usadas = set(json_data.get("posiciones_usadas", []))
            rotaciones = json_data.get("rotaciones", {})
            
            default_flight_data.update({
                "operador": flight_info.get("operador", ""),
                "numero_vuelo": flight_info.get("numero_vuelo", ""),
                "matricula": flight_info.get("matricula", ""),
                "fecha_vuelo": flight_info.get("fecha_vuelo", ""),
                "hora_vuelo": flight_info.get("hora_vuelo", ""),
                "ruta_vuelo": flight_info.get("ruta_vuelo", ""),
                "revision": flight_info.get("revision", ""),
                "destino_inicial": flight_info.get("destino_inicial", ""),
                "fuel_kg": calculated_values.get("fuel_kg", 0.0),
                "trip_fuel": calculated_values.get("trip_fuel", 0.0),
                "taxi_fuel": calculated_values.get("taxi_fuel", 0.0),
                "tipo_carga": json_data.get("tipo_carga", "Simétrico").capitalize(),
                "takeoff_runway": takeoff_conditions.get("runway", ""),
                "rwy_condition": takeoff_conditions.get("rwy_condition", "Dry"),
                "flaps_conf": takeoff_conditions.get("flaps_conf", "1+F"),
                "temperature": takeoff_conditions.get("temperature", 0.0),
                "air_condition": takeoff_conditions.get("air_condition", "On"),
                "anti_ice": takeoff_conditions.get("anti_ice", "Off"),
                "qnh": takeoff_conditions.get("qnh", 1013.0),
                "performance_tow": takeoff_conditions.get("performance_tow", 0.0),
                "performance_lw": takeoff_conditions.get("performance_lw", 0.0),
                "passengers_cockpit": passengers.get("cockpit", 0),
                "passengers_supernumerary": passengers.get("supernumerary", 0),
                "ballast_fuel": calculated_values.get("ballast_fuel", 0.0)
            })
            
            default_calc_state.update({
                "df": pd.DataFrame(manifest_data) if manifest_data else None,
                "posiciones_usadas": posiciones_usadas,
                "rotaciones": rotaciones,
                "bow": calculated_values.get("bow", 0.0),
                "bow_moment_x": calculated_values.get("bow_moment_x", 0.0),
                "bow_moment_y": calculated_values.get("bow_moment_y", 0.0),
                "moment_x_fuel_tow": calculated_values.get("moment_x_fuel_tow", 0.0),
                "moment_y_fuel_tow": calculated_values.get("moment_y_fuel_tow", 0.0),
                "moment_x_fuel_lw": calculated_values.get("moment_x_fuel_lw", 0.0),
                "moment_y_fuel_lw": calculated_values.get("moment_y_fuel_lw", 0.0),
                "passengers_cockpit_total_weight": passengers.get("cockpit_weight", 0.0),
                "passengers_cockpit_total_moment_x": passengers.get("cockpit_moment_x", 0.0),
                "passengers_supernumerary_total_weight": passengers.get("supernumerary_weight", 0.0),
                "passengers_supernumerary_total_moment_x": passengers.get("supernumerary_moment_x", 0.0),
                "fuel_distribution": calculated_values.get("fuel_distribution", default_calc_state["fuel_distribution"]),
                "fuel_mode": calculated_values.get("fuel_mode", "Automático")
            })
            
            if default_calc_state["df"] is not None:
                if "calculation_state" not in st.session_state:
                    st.session_state.calculation_state = CalculationState(**default_calc_state)
                else:
                    st.session_state.calculation_state.df = default_calc_state["df"].copy()
                    st.session_state.calculation_state.posiciones_usadas = default_calc_state["posiciones_usadas"].copy()
                    st.session_state.calculation_state.rotaciones = default_calc_state["rotaciones"].copy()
            
            st.success("JSON cargado correctamente. Los campos han sido prellenados con los datos del archivo.")
        except Exception as e:
            st.error(f"Error al cargar el JSON: {str(e)}")
            return

    if not os.path.exists(aircraft_db_path):
        st.error(f"No se encontró el archivo en: {aircraft_db_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    aircraft_db = pd.read_csv(aircraft_db_path, sep=";", decimal=",")
    
    tail = st.selectbox("Seleccione el 'Tail' de la aeronave", aircraft_db["Tail"].tolist(), index=aircraft_db["Tail"].tolist().index(default_flight_data["matricula"]) if default_flight_data["matricula"] in aircraft_db["Tail"].tolist() else 0)
    aircraft_info = aircraft_db[aircraft_db["Tail"] == tail].iloc[0]
    
    aircraft_folder = os.path.normpath(os.path.join(base_dir, tail))
    if not os.path.exists(aircraft_folder):
        st.error(f"La carpeta {aircraft_folder} no existe.")
        return

    basic_data_path = os.path.join(aircraft_folder, "basic_data.csv")
    if not os.path.exists(basic_data_path):
        st.error(f"No se encontró el archivo en: {basic_data_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    basic_data = pd.read_csv(basic_data_path, sep=";", decimal=",")

    st.markdown('<div id="restrictions_section"></div>', unsafe_allow_html=True)
    st.subheader("Restricciones Temporales Activas")
    restrictions_path = os.path.join(aircraft_folder, "MD_LD_BULK_restrictions.csv")
    if not os.path.exists(restrictions_path):
        st.error(f"No se encontró el archivo en: {restrictions_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    restricciones_df = pd.read_csv(restrictions_path, sep=";", decimal=",")
    restricciones_df.columns = [col.strip().replace(" ", "_") for col in restricciones_df.columns]
    restricciones_df["Temp_Restriction_Symmetric"] = pd.to_numeric(restricciones_df["Temp_Restriction_Symmetric"], errors="coerce").fillna(0)
    restricciones_df["Temp_Restriction_Asymmetric"] = pd.to_numeric(restricciones_df["Temp_Restriction_Asymmetric"], errors="coerce").fillna(0)

    active_restrictions = restricciones_df[
        (restricciones_df["Temp_Restriction_Symmetric"] != 0) | (restricciones_df["Temp_Restriction_Asymmetric"] != 0)
    ][["Position", "Bodega", "Temp_Restriction_Symmetric", "Temp_Restriction_Asymmetric"]]
    
    if active_restrictions.empty:
        st.info(f"No hay restricciones temporales activas para la aeronave {tail}.")
    else:
        st.write(f"Restricciones temporales activas para la aeronave {tail}:")
        st.dataframe(
            active_restrictions,
            column_config={
                "Position": "Posición",
                "Bodega": "Bodega",
                "Temp_Restriction_Symmetric": "Restricción Temporal Simétrica (kg)",
                "Temp_Restriction_Asymmetric": "Restricción Temporal Asimétrica (kg)"
            },
            use_container_width=True
        )

    exclusions_path = os.path.join(aircraft_folder, "exclusiones.csv")
    if not os.path.exists(exclusions_path):
        st.error(f"No se encontró el archivo en: {exclusions_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    exclusiones_df = pd.read_csv(exclusions_path, sep=";", decimal=",")
    exclusiones_df.set_index(exclusiones_df.columns[0], inplace=True)

    cumulative_restrictions_aft_path = os.path.join(aircraft_folder, "cummulative_restrictions_AFT.csv")
    if not os.path.exists(cumulative_restrictions_aft_path):
        st.error(f"No se encontró el archivo en: {cumulative_restrictions_aft_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    cumulative_restrictions_aft_df = pd.read_csv(cumulative_restrictions_aft_path, sep=";", decimal=",")

    cumulative_restrictions_fwd_path = os.path.join(aircraft_folder, "cummulative_restrictions_FWD.csv")
    if not os.path.exists(cumulative_restrictions_fwd_path):
        st.error(f"No se encontró el archivo en: {cumulative_restrictions_fwd_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    cumulative_restrictions_fwd_df = pd.read_csv(cumulative_restrictions_fwd_path, sep=";", decimal=",")

    fuel_table_path = os.path.join(aircraft_folder, "Usable_fuel_table.csv")
    if not os.path.exists(fuel_table_path):
        st.error(f"No se encontró el archivo en: {fuel_table_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    fuel_table = pd.read_csv(fuel_table_path, sep=";", decimal=",")
    required_fuel_columns = ["Fuel_kg", "MOMENT-X", "MOMENT-Y"]
    if not all(col in fuel_table.columns for col in required_fuel_columns):
        st.error(f"El archivo Usable_fuel_table.csv no contiene las columnas esperadas: {required_fuel_columns}.")
        return

    outer_tanks_path = os.path.normpath(os.path.join(aircraft_folder, "outer_tanks.csv"))
    inner_tanks_path = os.path.normpath(os.path.join(aircraft_folder, "inner_tanks.csv"))
    center_tank_path = os.path.normpath(os.path.join(aircraft_folder, "center_tank.csv"))
    trim_tank_path = os.path.normpath(os.path.join(aircraft_folder, "trim_tank.csv"))

    missing_files = []
    if not os.path.exists(outer_tanks_path):
        missing_files.append("outer_tanks.csv")
    if not os.path.exists(inner_tanks_path):
        missing_files.append("inner_tanks.csv")
    if not os.path.exists(center_tank_path):
        missing_files.append("center_tank.csv")
    if not os.path.exists(trim_tank_path):
        missing_files.append("trim_tank.csv")

    if missing_files:
        st.error(f"Faltan los siguientes archivos en la carpeta de la aeronave: {', '.join(missing_files)}")
        return

    outer_tanks_df = pd.read_csv(outer_tanks_path, sep=";", decimal=",")
    inner_tanks_df = pd.read_csv(inner_tanks_path, sep=";", decimal=",")
    center_tank_df = pd.read_csv(center_tank_path, sep=";", decimal=",")
    trim_tank_df = pd.read_csv(trim_tank_path, sep=";", decimal=",")

    passengers_path = os.path.join(aircraft_folder, "Passengers.csv")
    if not os.path.exists(passengers_path):
        st.error(f"No se encontró el archivo en: {passengers_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    passengers_df = pd.read_csv(passengers_path, sep=";", decimal=",")
    max_passengers_supernumerary = int(passengers_df["Quantity-Passenger"].max())
    if 0 not in passengers_df["Quantity-Passenger"].values:
        passengers_df = pd.concat([pd.DataFrame({"Quantity-Passenger": [0], "Weight": [0], "Moment": [0]}), passengers_df], ignore_index=True)

    flite_deck_path = os.path.join(aircraft_folder, "Flite_deck_passengers.csv")
    if not os.path.exists(flite_deck_path):
        st.error(f"No se encontró el archivo en: {flite_deck_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    flite_deck_df = pd.read_csv(flite_deck_path, sep=";", decimal=",")
    max_passengers_cockpit = int(flite_deck_df["Quantity-Passenger Flite-Deck"].max())
    if 0 not in flite_deck_df["Quantity-Passenger Flite-Deck"].values:
        flite_deck_df = pd.concat([pd.DataFrame({"Quantity-Passenger Flite-Deck": [0], "Weight": [0], "Moment": [0]}), flite_deck_df], ignore_index=True)

    trimset_path = os.path.join(aircraft_folder, "trimset.csv")
    if not os.path.exists(trimset_path):
        st.error(f"No se encontró el archivo en: {trimset_path}. Asegúrate de que el archivo exista en la ruta especificada.")
        return
    trimset_df = pd.read_csv(trimset_path, sep=";", decimal=",")

    st.markdown('<div id="flight_info_section"></div>', unsafe_allow_html=True)
    st.subheader("Información del Vuelo")
    
    col_fuel1, col_fuel2 = st.columns(2)
    with col_fuel1:
        normal_fuel = st.number_input("Combustible Normal (kg)", min_value=0.0, value=float(default_flight_data["fuel_kg"]), key="normal_fuel")
    with col_fuel2:
        ballast_fuel = st.number_input("Combustible Ballast y/o Atrapado (kg)", min_value=0.0, value=float(default_flight_data["ballast_fuel"]), key="ballast_fuel")

    fuel_kg = normal_fuel + ballast_fuel

    col1, col2, col3 = st.columns(3)
    with col1:
        fuel_mode = st.selectbox("Método de Carga de Combustible", ["Automático", "Manual"], index=["Automático", "Manual"].index(default_calc_state["fuel_mode"]))
    with col2:
        trip_fuel = st.number_input("Trip Fuel (kg)", min_value=0.0, max_value=fuel_kg, value=float(default_flight_data["trip_fuel"]), key="trip_fuel")
    with col3:
        taxi_fuel = st.number_input("Taxi Fuel (kg)", min_value=0.0, max_value=fuel_kg - trip_fuel, value=float(default_flight_data["taxi_fuel"]), key="taxi_fuel")

    tank_fuel = default_calc_state["fuel_distribution"]
    if fuel_mode == "Manual":
        st.write("### Cargue Manual de Combustible")
        st.write("Ingrese la cantidad de combustible (kg) en cada tanque.")
        
        tanks = {
            "Outer Tank LH": {"df": outer_tanks_df, "max_kg": 2850},
            "Outer Tank RH": {"df": outer_tanks_df, "max_kg": 2850},
            "Inner Tank LH": {"df": inner_tanks_df, "max_kg": 32950},
            "Inner Tank RH": {"df": inner_tanks_df, "max_kg": 32950},
            "Center Tank": {"df": center_tank_df, "max_kg": 32725},
            "Trim Tank": {"df": trim_tank_df, "max_kg": 4875}
        }

        tank_inputs = st.columns(3)
        for idx, tank in enumerate(tanks.keys()):
            with tank_inputs[idx % 3]:
                tank_fuel[tank] = st.number_input(
                    f"{tank} (kg, máx {tanks[tank]['max_kg']})",
                    min_value=0.0,
                    max_value=float(tanks[tank]['max_kg']),
                    value=float(tank_fuel[tank]),
                    key=f"tank_{tank}"
                )
        
        total_fuel_input = sum(tank_fuel.values())
        if abs(total_fuel_input - (fuel_kg - taxi_fuel)) > 0.01:
            st.error(f"La suma de los tanques ({total_fuel_input:.1f} kg) no coincide con el combustible para TOW ({fuel_kg - taxi_fuel:.1f} kg).")

    col4, col5, col6 = st.columns(3)
    with col4:
        tipo_carga = st.selectbox("Tipo de carga", ["Simétrico", "Asimétrico"], index=["Simétrico", "Asimétrico"].index(default_flight_data["tipo_carga"]))
    with col5:
        destino_inicial = st.text_input("Destino inicial (ej. MIA)", value=default_flight_data["destino_inicial"]).upper()
    with col6:
        takeoff_runway = st.text_input("Pista de despegue (ej. RWY 13)", value=default_flight_data["takeoff_runway"])

    col7, col8, col9 = st.columns(3)
    with col7:
        rwy_condition = st.selectbox("Condición de la pista", ["Dry", "Wet", "Contaminated"], index=0 if not default_flight_data.get("rwy_condition") else ["Dry", "Wet", "Contaminated"].index(default_flight_data["rwy_condition"]))
    with col8:
        flaps_conf = st.selectbox("Configuración de flaps", ["1+F", "2", "3"], index=["1+F", "2", "3"].index(default_flight_data["flaps_conf"]))
    with col9:
        temperature = st.number_input("Temperatura (°C)", value=float(default_flight_data["temperature"]))

    col10, col11, col12 = st.columns(3)
    with col10:
        air_condition = st.selectbox("Aire acondicionado", ["On", "Off"], index=["On", "Off"].index(default_flight_data["air_condition"]))
    with col11:
        anti_ice = st.selectbox("Sistema antihielo", ["On", "Off"], index=["On", "Off"].index(default_flight_data["anti_ice"]))
    with col12:
        qnh = st.number_input("QNH (hPa)", min_value=900.0, max_value=1100.0, value=float(default_flight_data["qnh"]))

    col13, col14, col15 = st.columns(3)
    with col13:
        performance_tow = st.number_input("Performance TOW (kg)", min_value=0.0, value=float(default_flight_data["performance_tow"]))
    with col14:
        performance_lw = st.number_input("Performance LW (kg)", min_value=0.0, value=float(default_flight_data["performance_lw"]))
    with col15:
        passengers_cockpit = st.number_input(f"Pasajeros en cabina de mando (máx {max_passengers_cockpit})", min_value=0, max_value=max_passengers_cockpit, step=1, value=int(default_flight_data["passengers_cockpit"]), key="passengers_cockpit")

    col16, col17, _ = st.columns(3)
    with col16:
        passengers_supernumerary = st.number_input(f"Pasajeros supernumerarios (máx {max_passengers_supernumerary})", min_value=0, max_value=max_passengers_supernumerary, step=1, value=int(default_flight_data["passengers_supernumerary"]), key="passengers_supernumerary")

    if fuel_kg < 0 or taxi_fuel < 0 or trip_fuel < 0:
        st.error("Los valores de combustible no pueden ser negativos.")
        return
    if trip_fuel > (fuel_kg - taxi_fuel):
        st.error("El Trip Fuel no puede ser mayor que el combustible disponible después del Taxi Fuel.")
        return

    aircraft_data = AircraftData(
        tail=tail,
        mtoc=basic_data["MTOW (kg)"].values[0],
        mlw=basic_data["MLW"].values[0],
        mzfw=basic_data["MZFW"].values[0],
        oew=basic_data["OEW"].values[0],
        arm=basic_data["ARM"].values[0],
        moment_aircraft=basic_data["Moment_Aircraft"].values[0],
        cg_aircraft=basic_data["CG_Aircraft"].values[0],
        lemac=basic_data["LEMAC"].values[0],
        mac_length=basic_data["MAC_length"].values[0],
        mrw_limit=basic_data["MRW"].values[0],
        lateral_imbalance_limit=basic_data["Lateral_Imbalance_Limit"].values[0]
    )

    if aircraft_data.mac_length == 0:
        st.error("MAC_length no puede ser cero.")
        return

    if aircraft_data.lemac == 0:
        st.error("LEMAC no puede ser cero.")
        return

    passenger_cockpit_row = flite_deck_df[flite_deck_df["Quantity-Passenger Flite-Deck"] == passengers_cockpit].iloc[0]
    passengers_cockpit_total_weight = passenger_cockpit_row["Weight"]
    passengers_cockpit_total_moment_x = passenger_cockpit_row["Moment"]

    passenger_supernumerary_row = passengers_df[passengers_df["Quantity-Passenger"] == passengers_supernumerary].iloc[0]
    passengers_supernumerary_total_weight = passenger_supernumerary_row["Weight"]
    passengers_supernumerary_total_moment_x = passenger_supernumerary_row["Moment"]

    bow = aircraft_data.oew + passengers_cockpit_total_weight + passengers_supernumerary_total_weight + ballast_fuel
    bow_moment_x = aircraft_data.moment_aircraft + passengers_cockpit_total_moment_x + passengers_supernumerary_total_moment_x
    bow_moment_y = 0

    fuel_for_tow = fuel_kg - taxi_fuel
    fuel_for_lw = fuel_kg - taxi_fuel - trip_fuel

    if fuel_mode == "Automático":
        fuel_row_tow = fuel_table.iloc[(fuel_table["Fuel_kg"] - fuel_for_tow).abs().argsort()[0]]
        moment_x_fuel_tow = fuel_row_tow["MOMENT-X"]
        moment_y_fuel_tow = fuel_row_tow["MOMENT-Y"]
        tank_fuel = {
            "Outer Tank LH": fuel_for_tow * 0.05,
            "Outer Tank RH": fuel_for_tow * 0.05,
            "Inner Tank LH": fuel_for_tow * 0.25,
            "Inner Tank RH": fuel_for_tow * 0.25,
            "Center Tank": fuel_for_tow * 0.40,
            "Trim Tank": fuel_for_tow * 0.0
        }
    else:
        moment_x_fuel_tow = 0.0
        moment_y_fuel_tow = 0.0

        for tank, fuel in tank_fuel.items():
            if fuel > 0:
                tank_df = tanks[tank]["df"]
                closest_row = tank_df.iloc[(tank_df["Kg_Fuel"] - fuel).abs().argsort()[0]]
                closest_fuel = closest_row["Kg_Fuel"]
                ratio = fuel / closest_fuel if closest_fuel != 0 else 0

                if tank == "Outer Tank LH":
                    moment_x_fuel_tow += closest_row["Moment_X_OLH"] * ratio
                    moment_y_fuel_tow += closest_row["Moment_Y_OLH"] * ratio
                elif tank == "Outer Tank RH":
                    moment_x_fuel_tow += closest_row["Moment_X_ORH"] * ratio
                    moment_y_fuel_tow += closest_row["Moment_Y_ORH"] * ratio
                elif tank == "Inner Tank LH":
                    moment_x_fuel_tow += closest_row["Moment_X_ILH"] * ratio
                    moment_y_fuel_tow += closest_row["Moment_Y_ILH"] * ratio
                elif tank == "Inner Tank RH":
                    moment_x_fuel_tow += closest_row["Moment_X_IRH"] * ratio
                    moment_y_fuel_tow += closest_row["Moment_Y_IRH"] * ratio
                elif tank == "Center Tank":
                    moment_x_fuel_tow += closest_row["CT_MOMENT_X"] * ratio
                elif tank == "Trim Tank":
                    moment_x_fuel_tow += closest_row["T_MOMENT_X"] * ratio

    fuel_row_lw = fuel_table.iloc[(fuel_table["Fuel_kg"] - fuel_for_lw).abs().argsort()[0]]
    moment_x_fuel_lw = fuel_row_lw["MOMENT-X"]
    moment_y_fuel_lw = fuel_row_lw["MOMENT-Y"]

    st.markdown('<div id="manifest_section"></div>', unsafe_allow_html=True)
    st.subheader("Carga del Manifiesto")
    manifiesto_option = st.radio("Seleccione cómo ingresar el manifiesto", ["Ingresar Manualmente", "Subir CSV"], index=0)

    if "calculation_state" not in st.session_state:
        st.session_state.calculation_state = CalculationState(**default_calc_state)

    operador = default_flight_data["operador"] or "Operador Desconocido"
    numero_vuelo = default_flight_data["numero_vuelo"] or "Vuelo Desconocido"
    matricula = default_flight_data["matricula"] or tail
    fecha_vuelo = default_flight_data["fecha_vuelo"] or datetime.now().strftime("%d/%m/%Y")
    hora_vuelo = default_flight_data["hora_vuelo"] or datetime.now().strftime("%H:%M")
    ruta_vuelo = default_flight_data["ruta_vuelo"] or "Ruta Desconocida"
    revision = default_flight_data["revision"] or "0"
    fecha_vuelo_safe = fecha_vuelo.replace("/", "_")

    if manifiesto_option == "Subir CSV":
        st.markdown('<div id="manifest_data_section"></div>', unsafe_allow_html=True)
        manifiesto_file = st.file_uploader("Sube el manifiesto CSV", type="csv", key="manifiesto")
        if manifiesto_file:
            df = pd.read_csv(manifiesto_file, skiprows=8, sep=";", encoding="latin-1", header=None, decimal=",")
            df.columns = ["Contour", "Number ULD", "ULD Final Destination", "Weight (KGS)", "Pieces", "Notes", "Extra1", "Extra2", "Extra3", "Extra4"]
            df = df[["Contour", "Number ULD", "ULD Final Destination", "Weight (KGS)", "Pieces", "Notes"]]
            df = df.dropna(subset=["Number ULD", "Weight (KGS)"], how="any")
            df = df[~df["Number ULD"].astype(str).str.upper().str.contains("TOTAL")]
            df = df[~df["Contour"].astype(str).str.upper().str.contains("TOTAL")]
            df["Weight (KGS)"] = pd.to_numeric(df["Weight (KGS)"], errors="coerce")
            
            df[["Pallet Base Size", "Baseplate Code"]] = df["Number ULD"].apply(lambda x: pd.Series(clasificar_base_refinada(x)))
            df["Posiciones Sugeridas"] = df.apply(lambda row: sugerencias_final_con_fak(row, restricciones_df, tipo_carga.lower()), axis=1)
            df["Posición Asignada"] = ""
            df["X-arm"] = None
            df["Y-arm"] = None
            df["Momento X"] = None
            df["Momento Y"] = None
            df["Bodega"] = None
            df["Rotated"] = False
            
            if st.session_state.calculation_state.df is not None:
                prev_df = st.session_state.calculation_state.df
                if prev_df[["Number ULD", "Weight (KGS)"]].equals(df[["Number ULD", "Weight (KGS)"]]):
                    df.update(prev_df[["Posición Asignada", "X-arm", "Y-arm", "Momento X", "Momento Y", "Bodega", "Rotated"]])
                    st.session_state.calculation_state.posiciones_usadas = set(df[df["Posición Asignada"] != ""]["Posición Asignada"].tolist())
                    st.session_state.calculation_state.rotaciones = {row["Number ULD"]: row["Rotated"] for _, row in df[df["Rotated"] != False].iterrows()}
                else:
                    st.session_state.calculation_state.posiciones_usadas = set()
                    st.session_state.calculation_state.rotaciones = {}
            
            st.session_state.calculation_state.df = df.copy()
            st.write("Manifiesto Inicial:", df)

            manifiesto_file.seek(0)
            content = manifiesto_file.read().decode("latin-1")
            lines = content.splitlines()[:10]
            lines = [line.strip().split(";") for line in lines]
            
            operador = lines[2][0]
            revision = lines[4][6]
            fecha_vuelo = lines[6][1]
            hora_vuelo = lines[6][3]
            ruta_vuelo = lines[6][5]
            matricula = lines[6][7]
            numero_vuelo = lines[7][1]
            fecha_vuelo_safe = fecha_vuelo.replace("/", "_")
        elif st.session_state.calculation_state.df is not None:
            st.write("Manifiesto cargado previamente:", st.session_state.calculation_state.df)
            operador = default_flight_data["operador"]
            revision = default_flight_data["revision"]
            fecha_vuelo = default_flight_data["fecha_vuelo"]
            hora_vuelo = default_flight_data["hora_vuelo"]
            ruta_vuelo = default_flight_data["ruta_vuelo"]
            matricula = default_flight_data["matricula"]
            numero_vuelo = default_flight_data["numero_vuelo"]
            fecha_vuelo_safe = fecha_vuelo.replace("/", "_")
    else:
        st.markdown('<div id="manifest_flight_info_section"></div>', unsafe_allow_html=True)
        st.subheader("Información del Vuelo para el Manifiesto")
        st.write("Ingrese los detalles del vuelo para el manifiesto manual.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            operador_manual = st.text_input("Operador", value=default_flight_data["operador"] or "Operador Manual", key="operador_manual")
            numero_vuelo_manual = st.text_input("Número de Vuelo", value=default_flight_data["numero_vuelo"] or "Vuelo Manual", key="numero_vuelo_manual")
        with col2:
            matricula_manual = st.text_input("Matrícula", value=default_flight_data["matricula"] or tail, key="matricula_manual")
            fecha_vuelo_manual = st.text_input("Fecha (DD/MM/YYYY)", value=default_flight_data["fecha_vuelo"] or datetime.now().strftime("%d/%m/%Y"), key="fecha_vuelo_manual")
        with col3:
            hora_vuelo_manual = st.text_input("Hora (HH:MM)", value=default_flight_data["hora_vuelo"] or datetime.now().strftime("%H:%M"), key="hora_vuelo_manual")
            ruta_vuelo_manual = st.text_input("Ruta", value=default_flight_data["ruta_vuelo"] or "Ruta Manual", key="ruta_vuelo_manual")
        
        revision_manual = st.text_input("Revisión de Manifiesto", value=default_flight_data["revision"] or "0", key="revision_manual")
        
        st.markdown('<div id="manifest_data_section"></div>', unsafe_allow_html=True)
        st.subheader("Datos del Manifiesto")
        st.write("Ingrese los datos del manifiesto en la tabla siguiente:")
        if "manifiesto_manual" not in st.session_state:
            st.session_state.manifiesto_manual = pd.DataFrame({
                "Contour": [""],
                "Number ULD": [""],
                "ULD Final Destination": [""],
                "Weight (KGS)": [0.0],
                "Pieces": [0],
                "Notes": [""]
            })
        
        edited_df = st.data_editor(
            st.session_state.manifiesto_manual,
            column_config={
                "Contour": st.column_config.TextColumn("Contour"),
                "Number ULD": st.column_config.TextColumn("Number ULD", required=True),
                "ULD Final Destination": st.column_config.TextColumn("ULD Final Destination"),
                "Weight (KGS)": st.column_config.NumberColumn("Weight (KGS)", min_value=0.0, required=True),
                "Pieces": st.column_config.NumberColumn("Pieces", min_value=0, step=1),
                "Notes": st.column_config.TextColumn("Notes")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"manifiesto_editor_{st.session_state.get('edit_count', 0)}"
        )
        
        if st.button("Confirmar Manifiesto Manual", key="confirm_manifest"):
            if edited_df.empty or edited_df[["Number ULD", "Weight (KGS)"]].isna().any().any():
                st.error("El manifiesto no puede estar vacío y debe incluir 'Number ULD' y 'Weight (KGS)' para cada fila.")
            else:
                df = edited_df.copy()
                df = df.dropna(subset=["Number ULD", "Weight (KGS)"], how="any")
                df = df[~df["Number ULD"].astype(str).str.upper().str.contains("TOTAL")]
                df = df[~df["Contour"].astype(str).str.upper().str.contains("TOTAL")]
                df["Weight (KGS)"] = pd.to_numeric(df["Weight (KGS)"], errors="coerce")
                
                df[["Pallet Base Size", "Baseplate Code"]] = df["Number ULD"].apply(lambda x: pd.Series(clasificar_base_refinada(x)))
                df["Posiciones Sugeridas"] = df.apply(lambda row: sugerencias_final_con_fak(row, restricciones_df, tipo_carga.lower()), axis=1)
                df["Posición Asignada"] = ""
                df["X-arm"] = None
                df["Y-arm"] = None
                df["Momento X"] = None
                df["Momento Y"] = None
                df["Bodega"] = None
                df["Rotated"] = False
                
                if st.session_state.calculation_state.df is not None:
                    prev_df = st.session_state.calculation_state.df
                    df["key"] = df["Number ULD"].astype(str) + "_" + df["Weight (KGS)"].astype(str)
                    prev_df["key"] = prev_df["Number ULD"].astype(str) + "_" + prev_df["Weight (KGS)"].astype(str)
                    for idx, row in df.iterrows():
                        matching_rows = prev_df[prev_df["key"] == row["key"]]
                        if not matching_rows.empty:
                            df.loc[idx, ["Posición Asignada", "X-arm", "Y-arm", "Momento X", "Momento Y", "Bodega", "Rotated"]] = matching_rows.iloc[0][["Posición Asignada", "X-arm", "Y-arm", "Momento X", "Momento Y", "Bodega", "Rotated"]]
                    df = df.drop(columns=["key"])
                    prev_df = prev_df.drop(columns=["key"])
                    st.session_state.calculation_state.posiciones_usadas = set(df[df["Posición Asignada"] != ""]["Posición Asignada"].tolist())
                    st.session_state.calculation_state.rotaciones = {row["Number ULD"]: row["Rotated"] for _, row in df[df["Rotated"] != False].iterrows()}
                else:
                    st.session_state.calculation_state.posiciones_usadas = set()
                    st.session_state.calculation_state.rotaciones = {}
                
                st.session_state.calculation_state.df = df.copy()
                st.session_state.manifiesto_manual = df.copy()
                st.write("Manifiesto Ingresado:", df)
                
                operador = operador_manual
                numero_vuelo = numero_vuelo_manual
                matricula = matricula_manual
                fecha_vuelo = fecha_vuelo_manual
                hora_vuelo = hora_vuelo_manual
                ruta_vuelo = ruta_vuelo_manual
                revision = revision_manual
                fecha_vuelo_safe = fecha_vuelo.replace("/", "_")

    df = st.session_state.calculation_state.df

    if df is None:
        st.warning("Por favor, suba un manifiesto CSV o confirme un manifiesto manual para continuar.")
        return

    flight_data = FlightData(
        operador=operador,
        numero_vuelo=numero_vuelo,
        matricula=matricula,
        fecha_vuelo=fecha_vuelo,
        hora_vuelo=hora_vuelo,
        ruta_vuelo=ruta_vuelo,
        revision=revision,
        destino_inicial=destino_inicial,
        fuel_kg=fuel_kg,
        trip_fuel=trip_fuel,
        taxi_fuel=taxi_fuel,
        tipo_carga=tipo_carga.lower(),
        takeoff_runway=takeoff_runway,
        rwy_condition=rwy_condition,
        flaps_conf=flaps_conf,
        temperature=temperature,
        air_condition=air_condition,
        anti_ice=anti_ice,
        qnh=qnh,
        performance_tow=performance_tow,
        performance_lw=performance_lw,
        passengers_cockpit=passengers_cockpit,
        passengers_supernumerary=passengers_supernumerary
    )

    st.session_state.calculation_state.bow = bow
    st.session_state.calculation_state.bow_moment_x = bow_moment_x
    st.session_state.calculation_state.bow_moment_y = bow_moment_y
    st.session_state.calculation_state.moment_x_fuel_tow = moment_x_fuel_tow
    st.session_state.calculation_state.moment_y_fuel_tow = moment_y_fuel_tow
    st.session_state.calculation_state.moment_x_fuel_lw = moment_x_fuel_lw
    st.session_state.calculation_state.moment_y_fuel_lw = moment_y_fuel_lw
    st.session_state.calculation_state.passengers_cockpit_total_weight = passengers_cockpit_total_weight
    st.session_state.calculation_state.passengers_cockpit_total_moment_x = passengers_cockpit_total_moment_x
    st.session_state.calculation_state.passengers_supernumerary_total_weight = passengers_supernumerary_total_weight
    st.session_state.calculation_state.passengers_supernumerary_total_moment_x = passengers_supernumerary_total_moment_x
    st.session_state.calculation_state.fuel_distribution = tank_fuel
    st.session_state.calculation_state.fuel_mode = fuel_mode

    st.markdown('<div id="calculation_mode_section"></div>', unsafe_allow_html=True)
    st.subheader("Seleccione el Modo de Cálculo")
    tab1, tab2 = st.tabs(["Cálculo Manual", "Cálculo Automático"])

    with tab1:
        st.markdown('<div id="manual_assignment_section"></div>', unsafe_allow_html=True)
        st.subheader("Asignación Manual de Posiciones")
        manual_assignment(
            st.session_state.calculation_state.df,
            restricciones_df,
            flight_data.tipo_carga,
            exclusiones_df,
            st.session_state.calculation_state.posiciones_usadas,
            st.session_state.calculation_state.rotaciones,
            tab_prefix="manual"
        )

    with tab2:
        automatic_assignment(
            st.session_state.calculation_state.df,
            restricciones_df,
            flight_data.tipo_carga,
            exclusiones_df,
            st.session_state.calculation_state.posiciones_usadas,
            st.session_state.calculation_state.rotaciones,
            flight_data.destino_inicial,
            st.session_state.calculation_state.bow,
            st.session_state.calculation_state.bow_moment_x,
            st.session_state.calculation_state.bow_moment_y,
            flight_data.fuel_kg,
            flight_data.taxi_fuel,
            st.session_state.calculation_state.moment_x_fuel_tow,
            st.session_state.calculation_state.moment_y_fuel_tow,
            aircraft_data.lemac,
            aircraft_data.mac_length,
            cumulative_restrictions_fwd_df,
            cumulative_restrictions_aft_df,
            tab_prefix="auto"
        )

    st.markdown('<div id="desassign_pallets_section"></div>', unsafe_allow_html=True)
    st.subheader("Desasignar Pallets")
    st.write("Funcionalidad de desasignación no implementada aún. Contacte al desarrollador para detalles.")

    data_to_save = None
    output_json = None

    if st.session_state.calculation_state.df is not None and st.session_state.calculation_state.df["Posición Asignada"].ne("").any():
        df_asignados = st.session_state.calculation_state.df[st.session_state.calculation_state.df["Posición Asignada"] != ""]
        
        final_results = calculate_final_values(
            df_asignados,
            st.session_state.calculation_state.bow,
            st.session_state.calculation_state.bow_moment_x,
            st.session_state.calculation_state.bow_moment_y,
            flight_data.fuel_kg,
            flight_data.taxi_fuel,
            flight_data.trip_fuel,
            st.session_state.calculation_state.moment_x_fuel_tow,
            st.session_state.calculation_state.moment_y_fuel_tow,
            st.session_state.calculation_state.moment_x_fuel_lw,
            st.session_state.calculation_state.moment_y_fuel_lw,
            aircraft_data.lemac,
            aircraft_data.mac_length,
            aircraft_data.mtoc,
            aircraft_data.mlw,
            aircraft_data.mzfw,
            flight_data.performance_tow,
            trimset_df,
            fuel_distribution=st.session_state.calculation_state.fuel_distribution,
            fuel_mode=st.session_state.calculation_state.fuel_mode
        )

        alerts = []
        if final_results["tow"] > aircraft_data.mtoc:
            alerts.append(f"TOW ({final_results['tow']:.1f} kg) excede el MTOW ({aircraft_data.mtoc:.1f} kg).")
        if performance_tow > 0 and final_results["tow"] > performance_tow:
            alerts.append(f"TOW ({final_results['tow']:.1f} kg) excede el Performance TOW ({performance_tow:.1f} kg).")
        if final_results["lw"] > aircraft_data.mlw:
            alerts.append(f"LW ({final_results['lw']:.1f} kg) excede el MLW ({aircraft_data.mlw:.1f} kg).")
        if performance_lw > 0 and final_results["lw"] > performance_lw:
            alerts.append(f"LW ({final_results['lw']:.1f} kg) excede el Performance LW ({performance_lw:.1f} kg).")

        complies, validation_df = check_cumulative_weights(df_asignados, cumulative_restrictions_fwd_df, cumulative_restrictions_aft_df)

        st.markdown('<div id="validation_section"></div>', unsafe_allow_html=True)
        st.subheader("Validación de Pesos Acumulativos")
        st.dataframe(validation_df, use_container_width=True)

        if not complies:
            if "Posición Asignada" in validation_df.columns:
                non_compliant_positions = validation_df[validation_df["Cumple"] == "No"]["Posición Asignada"].tolist()
                if non_compliant_positions:
                    st.error(f"Las siguientes posiciones no cumplen los pesos acumulativos: {', '.join(non_compliant_positions)}")
                    alerts.append(f"Restricciones acumulativas no cumplidas en posiciones: {', '.join(non_compliant_positions)}")
                else:
                    st.error("No se encontraron posiciones no conformes, pero el cálculo indica incumplimiento.")
                    alerts.append("Validación inconsistente: No hay posiciones no conformes pero complies=False.")
            else:
                st.error("Error: La columna 'Posición Asignada' no está presente en los datos de validación.")
                alerts.append("Error en la validación: Columna 'Posición Asignada' no encontrada.")
        else:
            st.success("Todas las posiciones cumplen los pesos acumulativos.")

        st.markdown('<div id="summary_section"></div>', unsafe_allow_html=True)
        st.subheader("Resumen Final de Peso y Balance")
        print_final_summary(
            df_asignados,
            flight_data.operador,
            flight_data.numero_vuelo,
            flight_data.matricula,
            flight_data.fecha_vuelo,
            flight_data.hora_vuelo,
            flight_data.ruta_vuelo,
            flight_data.revision,
            aircraft_data.oew,
            st.session_state.calculation_state.bow,
            final_results["peso_total"],
            final_results["zfw_peso"],
            final_results["zfw_mac"],
            aircraft_data.mzfw,
            final_results["tow"],
            final_results["tow_mac"],
            aircraft_data.mtoc,
            flight_data.trip_fuel,
            final_results["lw"],
            final_results["lw_mac"],
            aircraft_data.mlw,
            final_results["underload"],
            final_results["mrow"],
            flight_data.takeoff_runway,
            flight_data.flaps_conf,
            flight_data.temperature,
            flight_data.anti_ice,
            flight_data.air_condition,
            final_results["lateral_imbalance"],
            aircraft_data.mlw - st.session_state.calculation_state.bow - (flight_data.fuel_kg - flight_data.taxi_fuel - flight_data.trip_fuel),
            aircraft_data.mtoc - st.session_state.calculation_state.bow - (flight_data.fuel_kg - flight_data.taxi_fuel),
            aircraft_data.mzfw - st.session_state.calculation_state.bow,
            final_results["pitch_trim"],
            complies,
            validation_df,
            fuel_table,
            flight_data.fuel_kg - flight_data.taxi_fuel,
            flight_data.fuel_kg - flight_data.taxi_fuel - flight_data.trip_fuel,
            aircraft_data.mrw_limit,
            aircraft_data.lateral_imbalance_limit,
            st.session_state.calculation_state.fuel_distribution,
            st.session_state.calculation_state.fuel_mode,
            ballast_fuel,
            flight_data.performance_lw,
            flight_data.qnh,
            flight_data.rwy_condition,
            active_restrictions,
            flight_data.performance_tow
        )

        st.markdown('<div id="results_section"></div>', unsafe_allow_html=True)
        st.subheader("Resultados del Cálculo")
        st.write("**Asignaciones Realizadas:**")
        st.dataframe(df_asignados, use_container_width=True)

        # Pallets por Destino
        st.write("**Pallets por Destino:**")
        if not df_asignados.empty:
            destino_summary = df_asignados.groupby("ULD Final Destination").agg({
                "Number ULD": "count",
                "Weight (KGS)": "sum"
            }).reset_index()
            destino_summary.columns = ["Destino", "Cantidad de Pallets", "Peso Total (kg)"]
            st.dataframe(
                destino_summary,
                column_config={
                    "Destino": "Destino",
                    "Cantidad de Pallets": "Cantidad de Pallets",
                    "Peso Total (kg)": st.column_config.NumberColumn("Peso Total (kg)", format="%.1f")
                },
                use_container_width=True
            )
        else:
            st.write("- No hay pallets asignados.")

        # Pallets por Bodega
        st.write("**Pallets por Bodega:**")
        if not df_asignados.empty:
            bodega_summary = df_asignados.groupby("Bodega").agg({
                "Number ULD": "count",
                "Weight (KGS)": "sum"
            }).reset_index()
            bodega_summary.columns = ["Bodega", "Cantidad de Pallets", "Peso Total (kg)"]
            st.dataframe(
                bodega_summary,
                column_config={
                    "Bodega": "Bodega",
                    "Cantidad de Pallets": "Cantidad de Pallets",
                    "Peso Total (kg)": st.column_config.NumberColumn("Peso Total (kg)", format="%.1f")
                },
                use_container_width=True
            )
        else:
            st.write("- No hay pallets asignados.")

        # Gráfica del Main Deck
        st.write("**Distribución de Pallets en Main Deck:**")
        if not df_asignados[df_asignados["Bodega"] == "MD"].empty:
            fig_main_deck = plot_main_deck(df_asignados)
            st.plotly_chart(fig_main_deck, use_container_width=True)
        else:
            st.write("- No hay pallets asignados en Main Deck.")

        # Gráfica de LDF, LDA y Bulk
        st.write("**Distribución de Pallets en LDF, LDA y Bulk:**")
        if not df_asignados[df_asignados["Bodega"].isin(["LDF", "LDA", "BULK"])].empty:
            fig_lower_decks = plot_lower_decks(df_asignados)
            st.plotly_chart(fig_lower_decks, use_container_width=True)
        else:
            st.write("- No hay pallets asignados en LDF, LDA o Bulk.")

        st.markdown('<div id="envelope_section"></div>', unsafe_allow_html=True)
        st.subheader("Envelope")
        try:
            # Seleccionar el módulo de envelope según la aeronave
            if tail == "N342AV":
                try:
                    from N342AV_envelope import plot_cg_envelope
                except ImportError:
                    st.error("No se encontró N342AV_envelope.py")
                    return
            elif tail == "N337QT":
                try:
                    from N337QT_envelope import plot_cg_envelope
                except ImportError:
                    st.error("No se encontró N337QT_envelope.py")
                    return
            elif tail == "N338QT":
                try:
                    from N338QT_envelope import plot_cg_envelope
                except ImportError:
                    st.error("No se encontró N338QT_envelope.py")
                    return
            else:
                try:
                    from A330_200F_envelope import plot_cg_envelope
                except ImportError:
                    st.error("No se encontró A330_200F_envelope.py")
                    return

            temp_results = calculate_final_values(
                df_asignados if not df_asignados.empty else pd.DataFrame(columns=df.columns),
                st.session_state.calculation_state.bow,
                st.session_state.calculation_state.bow_moment_x,
                st.session_state.calculation_state.bow_moment_y,
                flight_data.fuel_kg,
                flight_data.taxi_fuel,
                flight_data.trip_fuel,
                st.session_state.calculation_state.moment_x_fuel_tow,
                st.session_state.calculation_state.moment_y_fuel_tow,
                st.session_state.calculation_state.moment_x_fuel_lw,
                st.session_state.calculation_state.moment_y_fuel_lw,
                aircraft_data.lemac,
                aircraft_data.mac_length,
                aircraft_data.mtoc,
                aircraft_data.mlw,
                aircraft_data.mzfw,
                flight_data.performance_tow,
                trimset_df,
                fuel_distribution=st.session_state.calculation_state.fuel_distribution,
                fuel_mode=st.session_state.calculation_state.fuel_mode
            )
            required_keys = ["zfw_peso", "zfw_mac", "tow", "tow_mac", "lw", "lw_mac"]
            missing_keys = [k for k in required_keys if k not in temp_results or temp_results[k] is None or np.isnan(temp_results[k])]
            if missing_keys:
                st.warning(f"No se puede graficar el envelope. Faltan o son inválidos: {', '.join(missing_keys)}")
                st.write("Valores calculados:", temp_results)
            else:
                plt = plot_cg_envelope(
                    temp_results["zfw_peso"],
                    temp_results["zfw_mac"],
                    temp_results["tow"],
                    temp_results["tow_mac"],
                    temp_results["lw"],
                    temp_results["lw_mac"]
                )
                st.pyplot(plt)
        except Exception as e:
            st.error(f"Error al generar el envelope: {str(e)}")
            st.write("Valores calculados:", temp_results)

        st.subheader("Exportación")
        col_export1, col_export2 = st.columns(2)
        output_folder = os.path.join(base_dir, "Output")
        os.makedirs(output_folder, exist_ok=True)
        execution_time = datetime.now().strftime("%H%M%S")
        output_json = os.path.join(output_folder, f"{aircraft_data.tail}_{flight_data.numero_vuelo}_{fecha_vuelo_safe}_{execution_time}_W&B.json")

        manifest_data = st.session_state.calculation_state.df.to_dict(orient="records")
        for record in manifest_data:
            for key, value in record.items():
                if isinstance(value, (np.int64, np.int32)):
                    record[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    record[key] = float(value)
                elif isinstance(value, (list, np.ndarray)):
                    if isinstance(value, np.ndarray):
                        value = value.tolist()
                    record[key] = [
                        int(v) if isinstance(v, (np.int64, np.int32)) else
                        float(v) if isinstance(v, (np.float64, np.float32)) else
                        None if pd.isna(v) else v
                        for v in value
                    ]
                elif pd.isna(value):
                    record[key] = None

        validation_data = validation_df.to_dict(orient="records")
        for record in validation_data:
            for key, value in record.items():
                if isinstance(value, (np.int64, np.int32)):
                    record[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    record[key] = float(value)
                elif isinstance(value, (list, np.ndarray)):
                    if isinstance(value, np.ndarray):
                        value = value.tolist()
                    record[key] = [
                        int(v) if isinstance(v, (np.int64, np.int32)) else
                        float(v) if isinstance(v, (np.float64, np.float32)) else
                        None if pd.isna(v) else v
                        for v in value
                    ]
                elif pd.isna(value):
                    record[key] = None

        fuel_table_data = fuel_table.to_dict(orient="records")
        for record in fuel_table_data:
            for key, value in record.items():
                if isinstance(value, (np.int64, np.int32)):
                    record[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    record[key] = float(value)
                elif isinstance(value, (list, np.ndarray)):
                    if isinstance(value, np.ndarray):
                        value = value.tolist()
                    record[key] = [
                        int(v) if isinstance(v, (np.int64, np.int32)) else
                        float(v) if isinstance(v, (np.float64, np.float32)) else
                        None if pd.isna(v) else v
                        for v in value
                    ]
                elif pd.isna(value):
                    record[key] = None

        data_to_save = {
            "flight_info": {
                "operador": flight_data.operador,
                "numero_vuelo": flight_data.numero_vuelo,
                "matricula": flight_data.matricula,
                "fecha_vuelo": flight_data.fecha_vuelo,
                "hora_vuelo": flight_data.hora_vuelo,
                "ruta_vuelo": flight_data.ruta_vuelo,
                "revision": flight_data.revision,
                "destino_inicial": flight_data.destino_inicial
            },
            "aircraft_info": {
                "tail": aircraft_data.tail,
                "mtoc": float(aircraft_data.mtoc),
                "mlw": float(aircraft_data.mlw),
                "mzfw": float(aircraft_data.mzfw),
                "oew": float(aircraft_data.oew),
                "arm": float(aircraft_data.arm),
                "moment_aircraft": float(aircraft_data.moment_aircraft),
                "cg_aircraft": float(aircraft_data.cg_aircraft),
                "lemac": float(aircraft_data.lemac),
                "mac_length": float(aircraft_data.mac_length),
                "mrw_limit": float(aircraft_data.mrw_limit),
                "lateral_imbalance_limit": float(aircraft_data.lateral_imbalance_limit)
            },
            "calculated_values": {
                "bow": float(st.session_state.calculation_state.bow),
                "bow_moment_x": float(st.session_state.calculation_state.bow_moment_x),
                "bow_moment_y": float(st.session_state.calculation_state.bow_moment_y),
                "peso_total": float(final_results["peso_total"]),
                "zfw_peso": float(final_results["zfw_peso"]),
                "zfw_momento_x": float(final_results["zfw_momento_x"]),
                "zfw_momento_y": float(final_results["zfw_momento_y"]),
                "zfw_mac": float(final_results["zfw_mac"]),
                "tow": float(final_results["tow"]),
                "tow_momento_x": float(final_results["tow_momento_x"]),
                "tow_momento_y": float(final_results["tow_momento_y"]),
                "tow_mac": float(final_results["tow_mac"]),
                "lw": float(final_results["lw"]),
                "lw_momento_x": float(final_results["lw_momento_x"]),
                "lw_momento_y": float(final_results["lw_momento_y"]),
                "lw_mac": float(final_results["lw_mac"]),
                "fuel_kg": float(flight_data.fuel_kg),
                "taxi_fuel": float(flight_data.taxi_fuel),
                "trip_fuel": float(flight_data.trip_fuel),
                "moment_x_fuel_tow": float(st.session_state.calculation_state.moment_x_fuel_tow),
                "moment_y_fuel_tow": float(st.session_state.calculation_state.moment_y_fuel_tow),
                "moment_x_fuel_lw": float(st.session_state.calculation_state.moment_x_fuel_lw),
                "moment_y_fuel_lw": float(st.session_state.calculation_state.moment_y_fuel_lw),
                "lateral_imbalance": float(final_results["lateral_imbalance"]),
                "underload": float(final_results["underload"]),
                "mrow": float(final_results["mrow"]),
                "pitch_trim": float(final_results["pitch_trim"]),
                "fuel_mode": st.session_state.calculation_state.fuel_mode,
                "fuel_distribution": {k: float(v) for k, v in st.session_state.calculation_state.fuel_distribution.items()},
                "ballast_fuel": float(ballast_fuel)
            },
            "tipo_carga": flight_data.tipo_carga,
            "manifest_data": manifest_data,
            "posiciones_usadas": list(st.session_state.calculation_state.posiciones_usadas),
            "rotaciones": st.session_state.calculation_state.rotaciones,
            "validation_df": validation_data,
            "fuel_table": fuel_table_data,
            "passengers": {
                "cockpit": int(flight_data.passengers_cockpit),
                "supernumerary": int(flight_data.passengers_supernumerary),
                "cockpit_weight": float(st.session_state.calculation_state.passengers_cockpit_total_weight),
                "cockpit_moment_x": float(st.session_state.calculation_state.passengers_cockpit_total_moment_x),
                "supernumerary_weight": float(st.session_state.calculation_state.passengers_supernumerary_total_weight),
                "supernumerary_moment_x": float(st.session_state.calculation_state.passengers_supernumerary_total_moment_x)
            },
            "takeoff_conditions": {
                "runway": flight_data.takeoff_runway,
                "rwy_condition": flight_data.rwy_condition,
                "flaps_conf": flight_data.flaps_conf,
                "temperature": float(flight_data.temperature),
                "air_condition": flight_data.air_condition,
                "anti_ice": flight_data.anti_ice,
                "qnh": float(flight_data.qnh),
                "performance_tow": float(flight_data.performance_tow),
                "performance_lw": float(flight_data.performance_lw)
            }
        }

        with col_export1:
            if alerts:
                st.warning("No se puede exportar debido a las siguientes alertas:")
                for alert in alerts:
                    st.markdown(f"- {alert}")
            else:
                if st.button("Exportar Resultados a JSON", key="export_json"):
                    try:
                        os.makedirs(os.path.dirname(output_json), exist_ok=True)
                        with open(output_json, "w", encoding="utf-8") as f:
                            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
                        st.success(f"Resultados exportados a {output_json}.")
                    except Exception as e:
                        st.error(f"Error al exportar el JSON: {str(e)}")
        
        with col_export2:
            if alerts:
                st.warning("No se puede descargar debido a alertas pendientes.")
            else:
                if st.download_button(
                    label="Descargar Resultados a JSON",
                    data=json.dumps(data_to_save, indent=4, ensure_ascii=False),
                    file_name=f"{aircraft_data.tail}_{flight_data.numero_vuelo}_{fecha_vuelo_safe}_{execution_time}_W&B.json",
                    mime="application/json",
                    key="download_json"
                ):
                    st.success("Archivo JSON listo para descargar.")