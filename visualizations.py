# visualizations.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

def plot_aircraft_layout(df, restricciones_df):
    """
    Genera un gráfico del layout de la aeronave con las posiciones asignadas, mostrando cada pallet
    como una tarjeta con información (número ULD, peso, posición).
    
    Args:
        df (pd.DataFrame): DataFrame con las asignaciones de carga.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones y posiciones.
    
    Returns:
        matplotlib.pyplot: Objeto de gráfico para mostrar en Streamlit.
    """
    fig, ax = plt.subplots(figsize=(15, 5))
    
    # Definir las dimensiones del avión (valores aproximados)
    aircraft_length = 60  # Longitud total del avión (m)
    aircraft_width = 6    # Ancho máximo del avión (m)
    
    # Dibujar el contorno del avión (simplificado como un rectángulo)
    ax.plot([0, aircraft_length, aircraft_length, 0, 0], 
            [-aircraft_width/2, -aircraft_width/2, aircraft_width/2, aircraft_width/2, -aircraft_width/2], 
            'k-')
    
    # Dimensiones de las tarjetas (en metros, ajustadas al espacio del gráfico)
    card_width = 4.0  # Ancho de la tarjeta (m)
    card_height = 2.0  # Alto de la tarjeta (m)

    # Dibujar posiciones asignadas como tarjetas
    for _, row in df.iterrows():
        if row["Posición Asignada"]:
            pos = restricciones_df[restricciones_df["Position"] == row["Posición Asignada"]]
            if not pos.empty:
                x_arm = pos["Average_X-Arm_(m)"].values[0]
                y_arm = pos["Average_Y-Arm_(m)"].values[0]
                bodega = pos["Bodega"].values[0]
                
                # Seleccionar color según la bodega
                if bodega == "MD":
                    color = 'red'
                elif bodega == "LDA":
                    color = 'blue'
                elif bodega == "LDF":
                    color = 'green'
                else:
                    continue
                
                # Calcular las esquinas de la tarjeta (centrado en X-arm, Y-arm)
                x_lower_left = x_arm - card_width / 2
                y_lower_left = y_arm - card_height / 2
                
                # Dibujar el rectángulo de la tarjeta
                rect = Rectangle((x_lower_left, y_lower_left), card_width, card_height, 
                               edgecolor='black', facecolor=color, alpha=0.3)
                ax.add_patch(rect)
                
                # Agregar información dentro de la tarjeta
                uld_number = row["Number ULD"]
                weight = row["Weight (KGS)"]
                position = row["Posición Asignada"]
                
                # Texto dentro de la tarjeta (centrado verticalmente)
                text = f"ULD: {uld_number}\nPeso: {weight:.1f} kg\nPos: {position}"
                ax.text(x_arm, y_arm, text, fontsize=8, ha='center', va='center', color='black', 
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.2'))

    # Configurar ejes
    ax.set_xlim(-5, aircraft_length + 5)
    ax.set_ylim(-aircraft_width, aircraft_width)
    ax.set_xlabel("X-arm (m)")
    ax.set_ylabel("Y-arm (m)")
    ax.set_title("Esquema de Carga de la Aeronave (Main Deck: Rojo, LDA: Azul, LDF: Verde)")
    ax.grid(True)
    
    return fig

def print_final_summary(
    df_asignados,
    operador,
    numero_vuelo,
    matricula,
    fecha_vuelo,
    hora_vuelo,
    ruta_vuelo,
    revision,
    oew,
    bow,
    peso_total,
    zfw_peso,
    zfw_mac,
    mzfw,
    tow,
    tow_mac,
    mtoc,
    trip_fuel,
    lw,
    lw_mac,
    mlw,
    underload,
    mrow,
    takeoff_runway,
    flaps_conf,
    temperature,
    anti_ice,
    air_condition,
    lateral_imbalance,
    underload_mlw,
    underload_mtoc,
    underload_mzfw,
    pitch_trim,
    complies,
    validation_df,
    fuel_table,
    fuel_tow,
    fuel_lw,
    mrw_limit,
    lateral_imbalance_limit,
    fuel_distribution,
    fuel_mode
):
    st.subheader("Resumen Final del Cálculo de Peso y Balance")
    
    st.write("### Información del Vuelo")
    st.write(f"**Operador:** {operador}")
    st.write(f"**Número de Vuelo:** {numero_vuelo} | **Matrícula:** {matricula}")
    st.write(f"**Fecha:** {fecha_vuelo} | **Hora:** {hora_vuelo}")
    st.write(f"**Ruta:** {ruta_vuelo} | **Revisión:** {revision}")

    st.write("### Pesos Calculados")
    st.write(f"**OEW (Peso Operacional Vacío):** {oew:.1f} kg")
    st.write(f"**BOW (Peso Operacional Básico):** {bow:.1f} kg")
    st.write(f"**Peso Total de Carga:** {peso_total:.1f} kg")
    st.write(f"**ZFW (Peso Cero Combustible):** {zfw_peso:.1f} kg | **%MAC ZFW:** {zfw_mac:.2f}% | **MZFW:** {mzfw:.1f} kg")
    st.write(f"**TOW (Peso al Despegue):** {tow:.1f} kg | **%MAC TOW:** {tow_mac:.2f}% | **MTOW:** {mtoc:.1f} kg")
    st.write(f"**LW (Peso al Aterrizaje):** {lw:.1f} kg | **%MAC LW:** {lw_mac:.2f}% | **MLW:** {mlw:.1f} kg")
    st.write(f"**MRW (Peso Máximo de Rampa):** {mrow:.1f} kg | **Límite MRW:** {mrw_limit:.1f} kg")

    st.write("### Combustible")
    st.write(f"**Combustible TOW:** {fuel_tow:.1f} kg")
    st.write(f"**Trip Fuel:** {trip_fuel:.1f} kg")
    st.write(f"**Combustible LW:** {fuel_lw:.1f} kg")

    if fuel_mode == "Manual":
        st.write("#### Distribución de Combustible por TANQUE (kg)")
        st.write(f"**Outer Tank LH:** {fuel_distribution.get('Outer Tank LH', 0.0):.1f} kg")
        st.write(f"**Outer Tank RH:** {fuel_distribution.get('Outer Tank RH', 0.0):.1f} kg")
        st.write(f"**Inner Tank LH:** {fuel_distribution.get('Inner Tank LH', 0.0):.1f} kg")
        st.write(f"**Inner Tank RH:** {fuel_distribution.get('Inner Tank RH', 0.0):.1f} kg")
        st.write(f"**Center Tank:** {fuel_distribution.get('Center Tank', 0.0):.1f} kg")
        st.write(f"**Trim Tank:** {fuel_distribution.get('Trim Tank', 0.0):.1f} kg")
    else:
        st.write("#### Distribución de Combustible por TANQUE (kg)")
        st.write("No disponible en modo Automático.")

    st.write("### Underload")
    st.write(f"**Underload MLW:** {underload_mlw:.1f} kg")
    st.write(f"**Underload MTOW:** {underload_mtoc:.1f} kg")
    st.write(f"**Underload MZFW:** {underload_mzfw:.1f} kg")
    st.write(f"**Underload Final:** {underload:.1f} kg")

    st.write("### Condiciones de Despegue")
    st.write(f"**Pista de Despegue:** {takeoff_runway}")
    st.write(f"**Configuración de Flaps:** {flaps_conf}")
    st.write(f"**Temperatura:** {temperature} °C")
    st.write(f"**Aire Acondicionado:** {air_condition}")
    st.write(f"**Sistema Antihielo:** {anti_ice}")

    st.write("### Balance Lateral")
    st.write(f"**Imbalance Lateral:** {lateral_imbalance:.1f} | **Límite:** {lateral_imbalance_limit:.1f}")

    st.write("### Pitch Trim")
    st.write(f"**Pitch Trim:** {pitch_trim}")

    st.write("### Validación de Pesos Acumulativos")
    if complies:
        st.success("Todos los pesos acumulativos cumplen con las restricciones.")
    st.write(validation_df)