# visualizations.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def plot_aircraft_layout(df, restricciones_df):
    """
    Genera gráficos interactivos para las bodegas de la aeronave con las posiciones asignadas,
    mostrando cada pallet como una tarjeta estilizada usando Plotly. Genera dos gráficos:
    uno para Main Deck (MD) y otro combinado para LDA, LDF y Bulk.
    Las tarjetas están a escala según las dimensiones reales de los pallets/ULDs.
    
    Args:
        df (pd.DataFrame): DataFrame con las asignaciones de carga.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones y posiciones.
    
    Returns:
        dict: Diccionario con los gráficos de Plotly para Main Deck y Lower Deck (LDA, LDF, Bulk).
    """
    # Definir las dimensiones del avión (valores aproximados)
    aircraft_length = 60  # Longitud total del avión (m)
    aircraft_width = 6    # Ancho máximo del avión (m)
    
    # Dimensiones reales de los pallets/ULDs (en metros)
    md_width = 2.44  # Ancho de un pallet en Main Deck (96 pulgadas = 2.44 m)
    md_height = 3.18  # Alto de un pallet en Main Deck (125 pulgadas = 3.18 m)
    ld_width = 1.6   # Ancho de un ULD LD3 en LDA/LDF (1.6 m)
    ld_height = 1.5  # Alto de un ULD LD3 en LDA/LDF (1.5 m)
    bulk_width = 1.0  # Ancho de una posición de Bulk (estimado, ajusta según datos reales)
    bulk_height = 1.0  # Alto de una posición de Bulk (estimado, ajusta según datos reales)

    # Separar las posiciones por bodega
    md_df = df[df["Posición Asignada"].isin(restricciones_df[restricciones_df["Bodega"] == "MD"]["Position"])]
    lda_df = df[df["Posición Asignada"].isin(restricciones_df[restricciones_df["Bodega"] == "LDA"]["Position"])]
    ldf_df = df[df["Posición Asignada"].isin(restricciones_df[restricciones_df["Bodega"] == "LDF"]["Position"])]
    bulk_df = df[df["Posición Asignada"].isin(restricciones_df[restricciones_df["Bodega"] == "BULK"]["Position"])]
    
    # Diccionario para almacenar los gráficos
    figures = {"Main Deck": None, "Lower Deck": None}
    
    # Función auxiliar para crear un gráfico para una o más bodegas
    def create_bodega_plot(bodega_dfs, bodega_names, colors, title, width_heights):
        fig = go.Figure()
        
        # Dibujar el contorno del avión (simplificado como un rectángulo)
        fig.add_trace(go.Scatter(
            x=[0, aircraft_length, aircraft_length, 0, 0],
            y=[-aircraft_width/2, -aircraft_width/2, aircraft_width/2, aircraft_width/2, -aircraft_width/2],
            mode='lines',
            line=dict(color='black', width=2),
            fill='toself',
            fillcolor='lightgray',
            opacity=0.3,
            showlegend=False
        ))
        
        # Variable para verificar si hay posiciones asignadas
        has_positions = False
        
        # Procesar cada bodega
        for bodega_df, bodega_name, color, (width, height) in zip(bodega_dfs, bodega_names, colors, width_heights):
            x_positions = []
            y_positions = []
            colors_list = []
            annotations = []
            
            # Procesar las posiciones asignadas para esta bodega
            for _, row in bodega_df.iterrows():
                if row["Posición Asignada"]:
                    pos = restricciones_df[restricciones_df["Position"] == row["Posición Asignada"]]
                    if not pos.empty:
                        x_arm = pos["Average_X-Arm_(m)"].values[0]
                        y_arm = pos["Average_Y-Arm_(m)"].values[0]
                        
                        # Indicar que hay posiciones asignadas
                        has_positions = True
                        
                        # Agregar la posición a las listas
                        x_positions.append(x_arm)
                        y_positions.append(y_arm)
                        colors_list.append(color)
                        
                        # Crear la anotación (tarjeta) con la información del ULD
                        uld_number = row["Number ULD"]
                        weight = row["Weight (KGS)"]
                        position = row["Posición Asignada"]
                        
                        # Texto de la tarjeta
                        text = f"ULD: {uld_number}<br>Peso: {weight:.1f} kg<br>Pos: {position}"
                        
                        # Agregar la anotación como una tarjeta
                        annotations.append(dict(
                            x=x_arm,
                            y=y_arm,
                            text=text,
                            showarrow=False,
                            font=dict(size=10, color='black'),
                            bgcolor=color,
                            opacity=0.8,
                            bordercolor='black',
                            borderwidth=1,
                            borderpad=4,
                            align='center',
                            xanchor='center',
                            yanchor='middle',
                            width=width * 20,  # Escalar para que el texto se ajuste al tamaño real
                            height=height * 20  # Escalar para que el texto se ajuste al tamaño real
                        ))
            
            # Agregar los puntos de las posiciones (como rectángulos a escala)
            for x, y in zip(x_positions, y_positions):
                fig.add_shape(
                    type="rect",
                    x0=x - width / 2,
                    y0=y - height / 2,
                    x1=x + width / 2,
                    y1=y + height / 2,
                    line=dict(color='black', width=1),
                    fillcolor=color,
                    opacity=0.3
                )
        
        # Si no hay posiciones asignadas, devolver None
        if not has_positions:
            return None
        
        # Agregar las anotaciones (tarjetas)
        fig.update_layout(
            annotations=annotations,
            xaxis_title="X-arm (m)",
            yaxis_title="Y-arm (m)",
            title=title,
            xaxis=dict(range=[-5, aircraft_length + 5], showgrid=True, gridcolor='lightgray'),
            yaxis=dict(range=[-aircraft_width, aircraft_width], showgrid=True, gridcolor='lightgray'),
            plot_bgcolor='white',
            width=900,
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            showlegend=False
        )
        
        return fig

    # Crear gráfico para Main Deck (MD)
    figures["Main Deck"] = create_bodega_plot(
        bodega_dfs=[md_df],
        bodega_names=["Main Deck (MD)"],
        colors=["red"],
        title="Esquema de Carga - Main Deck (MD)",
        width_heights=[(md_width, md_height)]
    )

    # Crear gráfico combinado para LDA, LDF y Bulk
    figures["Lower Deck"] = create_bodega_plot(
        bodega_dfs=[lda_df, ldf_df, bulk_df],
        bodega_names=["Lower Deck Aft (LDA)", "Lower Deck Forward (LDF)", "Bulk"],
        colors=["blue", "green", "purple"],
        title="Esquema de Carga - Lower Deck (LDA: Azul, LDF: Verde, Bulk: Morado)",
        width_heights=[(ld_width, ld_height), (ld_width, ld_height), (bulk_width, bulk_height)]
    )
    
    return figures

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