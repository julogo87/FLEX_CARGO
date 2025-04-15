import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def print_final_summary(
    df_asignados, operador, numero_vuelo, matricula, fecha_vuelo, hora_vuelo, ruta_vuelo, revision,
    oew, bow, peso_total, zfw_peso, zfw_mac, mzfw, tow, tow_mac, mtow, trip_fuel, lw, lw_mac, mlw,
    underload, mrow, takeoff_runway, flaps_conf, temperature, anti_ice, air_condition, lateral_imbalance,
    max_payload_lw, max_payload_tow, max_payload_zfw, pitch_trim, complies, validation_df, fuel_table,
    fuel_tow, fuel_lw, mrw_limit, lateral_imbalance_limit, fuel_distribution, fuel_mode,
    ballast_fuel, performance_lw, qnh, rwy_condition, active_restrictions, performance_tow
):
    """
    Muestra un resumen final de los cálculos de peso y balance, organizado y visualmente atractivo.
    """
    # Estilo para un diseño más limpio
    st.markdown(
        """
        <style>
        .summary-box {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f8f9fa;
        }
        .summary-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 10px;
        }
        .summary-item {
            font-size: 1em;
            margin: 5px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Información del Vuelo
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">✈️ Información del Vuelo</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="summary-item"><b>Operador:</b> {operador}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Número de Vuelo:</b> {numero_vuelo}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Matrícula:</b> {matricula}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="summary-item"><b>Fecha:</b> {fecha_vuelo}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Hora:</b> {hora_vuelo}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Ruta:</b> {ruta_vuelo}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Revisión:</b> {revision}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Pesos Principales
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">⚖️ Pesos Principales</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f'<div class="summary-item"><b>OEW:</b> {oew:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>BOW:</b> {bow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Peso Total Carga:</b> {peso_total:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>ZFW:</b> {zfw_peso:,.1f} kg (MAC: {zfw_mac:,.1f}%)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MZFW:</b> {mzfw:,.1f} kg</div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="summary-item"><b>TOW:</b> {tow:,.1f} kg (MAC: {tow_mac:,.1f}%)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MTOW:</b> {mtow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Trip Fuel:</b> {trip_fuel:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>LW:</b> {lw:,.1f} kg (MAC: {lw_mac:,.1f}%)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MLW:</b> {mlw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Performance LW:</b> {performance_lw:,.1f} kg</div>' if performance_lw > 0 else '<div class="summary-item"><b>Performance LW:</b> No especificado</div>', unsafe_allow_html=True)
        # Pallets por Destino
        st.markdown('<div class="summary-item"><b>Pallets por Destino:</b></div>', unsafe_allow_html=True)
        if not df_asignados.empty:
            destino_summary = df_asignados.groupby("ULD Final Destination")["Weight (KGS)"].sum().reset_index()
            for _, row in destino_summary.iterrows():
                st.markdown(f'<div class="summary-item"> - {row["ULD Final Destination"]}: {row["Weight (KGS)"]:,.1f} kg</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="summary-item"> - No hay pallets asignados.</div>', unsafe_allow_html=True)
        # Pallets por Bodega
        st.markdown('<div class="summary-item"><b>Pallets por Bodega:</b></div>', unsafe_allow_html=True)
        if not df_asignados.empty:
            bodega_summary = df_asignados.groupby("Bodega")["Weight (KGS)"].sum().reset_index()
            for _, row in bodega_summary.iterrows():
                st.markdown(f'<div class="summary-item"> - {row["Bodega"]}: {row["Weight (KGS)"]:,.1f} kg</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="summary-item"> - No hay pallets asignados.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Condiciones de Despegue
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">🛫 Condiciones de Despegue</div>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(f'<div class="summary-item"><b>Pista:</b> {takeoff_runway}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Condición de Pista:</b> {rwy_condition}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Flaps:</b> {flaps_conf}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Temperatura:</b> {temperature} °C</div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="summary-item"><b>Aire Acondicionado:</b> {air_condition}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Antihielo:</b> {anti_ice}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>QNH:</b> {qnh} hPa</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Performance TOW:</b> {performance_tow:,.1f} kg</div>' if performance_tow > 0 else '<div class="summary-item"><b>Performance TOW:</b> No especificado</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Restricciones y Límites
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">🚨 Restricciones y Límites</div>', unsafe_allow_html=True)
    col7, col8 = st.columns(2)
    with col7:
        st.markdown(f'<div class="summary-item"><b>Underload:</b> {underload:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MROW:</b> {mrow:,.1f} kg (Límite: {mrw_limit:,.1f} kg)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Desbalance Lateral:</b> {lateral_imbalance:,.1f} kg (Límite: {lateral_imbalance_limit:,.1f} kg)</div>', unsafe_allow_html=True)
    with col8:
        st.markdown(f'<div class="summary-item"><b>Carga Máx. LW:</b> {max_payload_lw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Carga Máx. TOW:</b> {max_payload_tow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Carga Máx. ZFW:</b> {max_payload_zfw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Pitch Trim:</b> {pitch_trim:,.1f}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Combustible
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">⛽ Combustible</div>', unsafe_allow_html=True)
    col9, col10 = st.columns(2)
    with col9:
        st.markdown(f'<div class="summary-item"><b>Combustible en TOW:</b> {fuel_tow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Combustible en LW:</b> {fuel_lw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Ballast Fuel:</b> {ballast_fuel:,.1f} kg</div>', unsafe_allow_html=True)
    with col10:
        st.markdown(f'<div class="summary-item"><b>Modo de Carga:</b> {fuel_mode}</div>', unsafe_allow_html=True)
        st.markdown('<div class="summary-item"><b>Distribución de Combustible:</b></div>', unsafe_allow_html=True)
        for tank, fuel in fuel_distribution.items():
            st.markdown(f'<div class="summary-item"> - {tank}: {fuel:,.1f} kg</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Restricciones Temporales Activas
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">📋 Restricciones Temporales Activas</div>', unsafe_allow_html=True)
    if active_restrictions.empty:
        st.info("No hay restricciones temporales activas.")
    else:
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
    st.markdown('</div>', unsafe_allow_html=True)

    # Estado de Cumplimiento
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown('<div class="summary-title">✅ Estado de Cumplimiento</div>', unsafe_allow_html=True)
    if complies:
        st.success("Todas las restricciones acumulativas se cumplen.")
    else:
        st.error("Algunas restricciones acumulativas no se cumplen. Revise la validación de pesos acumulativos.")
    st.markdown('</div>', unsafe_allow_html=True)

def plot_main_deck(df):
    """
    Genera una gráfica Plotly para los pallets en el Main Deck con tamaños específicos por posición.
    - CFR, FJR, JLR, LPR: 2x4 metros.
    - CFG, FJG, JLG: 2x6 metros.
    - Otros: 2x2 metros.
    - Eje X: siempre de 14 a 80.
    - Eje Y: de -2.5 a 2.5 con paso de 0.5.

    Args:
        df (pd.DataFrame): DataFrame con los datos de los pallets asignados.

    Returns:
        plotly.graph_objects.Figure: Gráfica interactiva del Main Deck.
    """
    # Filtrar pallets en Main Deck (MD)
    df_md = df[df["Bodega"] == "MD"].copy()
    if df_md.empty:
        st.warning("No hay pallets asignados en Main Deck.")
        return None

    # Validar columnas necesarias
    required_columns = ["X-arm", "Y-arm", "Number ULD", "Posición Asignada", "Weight (KGS)", "ULD Final Destination", "Contour"]
    missing_columns = [col for col in required_columns if col not in df_md.columns]
    if missing_columns:
        st.error(f"Faltan columnas en el DataFrame: {', '.join(missing_columns)}")
        return None

    # Eliminar filas con valores nulos o no numéricos en X-arm, Y-arm
    df_md = df_md.dropna(subset=["X-arm", "Y-arm", "Posición Asignada", "Weight (KGS)"])
    df_md = df_md[pd.to_numeric(df_md["X-arm"], errors='coerce').notnull()]
    df_md = df_md[pd.to_numeric(df_md["Y-arm"], errors='coerce').notnull()]
    df_md = df_md[pd.to_numeric(df_md["Weight (KGS)"], errors='coerce').notnull()]
    
    if df_md.empty:
        st.warning("No hay datos válidos para graficar en Main Deck.")
        return None

    # Crear una paleta de colores para destinos
    destinos = df_md["ULD Final Destination"].astype(str).unique()
    colors = px.colors.qualitative.Plotly
    color_map = {dest: colors[i % len(colors)] for i, dest in enumerate(destinos)}

    # Inicializar la figura
    fig = go.Figure()

    # Añadir pallets como rectángulos con tamaños según posición
    shapes = []
    annotations = []
    for _, row in df_md.iterrows():
        try:
            x = float(row["X-arm"])
            y = float(row["Y-arm"])
            uld = str(row["Number ULD"])
            pos = str(row["Posición Asignada"]).strip()
            peso = float(row["Weight (KGS)"])
            destino = str(row["ULD Final Destination"])
            contorno = str(row["Contour"])
            notas = str(row["Notes"]) if pd.notna(row["Notes"]) else "Sin notas"

            # Definir tamaño según posición
            if pos in ["CFR", "FJR", "JLR", "LPR"]:
                width = 2
                height = 4
            elif pos in ["CFG", "FJG", "JLG"]:
                width = 2
                height = 6
            else:
                width = 2
                height = 2

            # Añadir rectángulo como forma
            shapes.append(
                dict(
                    type="rect",
                    x0=x - width / 2,
                    y0=y - height / 2,
                    x1=x + width / 2,
                    y1=y + height / 2,
                    fillcolor=color_map[destino],
                    opacity=0.6,
                    line=dict(color="black", width=1)
                )
            )

            # Añadir anotación con la información
            text = f"ULD: {uld}<br>Pos: {pos}<br>Peso: {peso:,.1f} kg<br>Dest: {destino}<br>Cont: {contorno}"
            annotations.append(
                dict(
                    x=x,
                    y=y,
                    text=text,
                    showarrow=False,
                    font=dict(size=7, color="black"),
                    align="center",
                    xanchor="center",
                    yanchor="middle"
                )
            )

            # Añadir punto para tooltip
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(size=1, opacity=0),
                    hovertext=notas,
                    hoverinfo="text",
                    showlegend=False
                )
            )
        except (ValueError, TypeError) as e:
            st.warning(f"Error al procesar pallet {uld}: {str(e)}")
            continue

    # Configurar el layout
    fig.update_layout(
        title="Distribución de Pallets en Main Deck",
        xaxis=dict(title="X-arm (metros)", showgrid=True, range=[14, 55]),
        yaxis=dict(title="Y-arm (metros)", showgrid=True, range=[-2.5, 2.5], dtick=0.5),
        shapes=shapes,
        annotations=annotations,
        showlegend=False,
        plot_bgcolor="white",
        width=1000,
        height=300
    )

    # Añadir leyenda de colores
    for destino, color in color_map.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=10, color=color),
                name=destino,
                showlegend=True
            )
        )

    return fig

def plot_lower_decks(df):
    """
    Genera una gráfica Plotly para los pallets en LDF, LDA y Bulk con tamaño de 1.5x1.5 metros.
    - Eje X: siempre de 14 a 80.
    - Eje Y: de -2.5 a 2.5 con paso de 0.5.

    Args:
        df (pd.DataFrame): DataFrame con los datos de los pallets asignados.

    Returns:
        plotly.graph_objects.Figure: Gráfica interactiva de LDF, LDA y Bulk.
    """
    # Filtrar pallets en LDF, LDA y Bulk
    df_lower = df[df["Bodega"].isin(["LDF", "LDA", "BULK"])].copy()
    if df_lower.empty:
        st.warning("No hay pallets asignados en LDF, LDA o Bulk.")
        return None

    # Validar columnas necesarias
    required_columns = ["X-arm", "Y-arm", "Number ULD", "Posición Asignada", "Weight (KGS)", "ULD Final Destination", "Contour", "Bodega"]
    missing_columns = [col for col in required_columns if col not in df_lower.columns]
    if missing_columns:
        st.error(f"Faltan columnas en el DataFrame: {', '.join(missing_columns)}")
        return None

    # Eliminar filas con valores nulos o no numéricos en X-arm, Y-arm
    df_lower = df_lower.dropna(subset=["X-arm", "Y-arm", "Posición Asignada", "Weight (KGS)", "Bodega"])
    df_lower = df_lower[pd.to_numeric(df_lower["X-arm"], errors='coerce').notnull()]
    df_lower = df_lower[pd.to_numeric(df_lower["Y-arm"], errors='coerce').notnull()]
    df_lower = df_lower[pd.to_numeric(df_lower["Weight (KGS)"], errors='coerce').notnull()]
    
    if df_lower.empty:
        st.warning("No hay datos válidos para graficar en LDF, LDA o Bulk.")
        return None

    # Crear una paleta de colores para destinos
    destinos = df_lower["ULD Final Destination"].astype(str).unique()
    colors = px.colors.qualitative.Plotly
    color_map = {dest: colors[i % len(colors)] for i, dest in enumerate(destinos)}

    # Inicializar la figura
    fig = go.Figure()

    # Añadir pallets como rectángulos de 1.5x1.5 metros
    shapes = []
    annotations = []
    for _, row in df_lower.iterrows():
        try:
            x = float(row["X-arm"])
            y = float(row["Y-arm"])
            uld = str(row["Number ULD"])
            pos = str(row["Posición Asignada"]).strip()
            peso = float(row["Weight (KGS)"])
            destino = str(row["ULD Final Destination"])
            contorno = str(row["Contour"])
            bodega = str(row["Bodega"])
            notas = str(row["Notes"]) if pd.notna(row["Notes"]) else "Sin notas"

            # Tamaño del rectángulo: 1.5x1.5 metros
            width = 1.5
            height = 1.5

            # Añadir rectángulo como forma
            shapes.append(
                dict(
                    type="rect",
                    x0=x - width / 2,
                    y0=y - height / 2,
                    x1=x + width / 2,
                    y1=y + height / 2,
                    fillcolor=color_map[destino],
                    opacity=0.6,
                    line=dict(color="black", width=1)
                )
            )

            # Añadir anotación con la información
            text = f"ULD: {uld}<br>Pos: {pos}<br>Peso: {peso:,.1f} kg<br>Dest: {destino}<br>Cont: {contorno}"
            annotations.append(
                dict(
                    x=x,
                    y=y,
                    text=text,
                    showarrow=False,
                    font=dict(size=6, color="black"),
                    align="center",
                    xanchor="center",
                    yanchor="middle"
                )
            )

            # Añadir punto para tooltip
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(size=1, opacity=0),
                    hovertext=notas,
                    hoverinfo="text",
                    showlegend=False
                )
            )
        except (ValueError, TypeError) as e:
            st.warning(f"Error al procesar pallet {uld}: {str(e)}")
            continue

    # Separar regiones por bodega (líneas verticales según X-arm)
    if not df_lower.empty:
        x_ranges = {
            "LDF": (df_lower[df_lower["Bodega"] == "LDF"]["X-arm"].min(), df_lower[df_lower["Bodega"] == "LDF"]["X-arm"].max()),
            "LDA": (df_lower[df_lower["Bodega"] == "LDA"]["X-arm"].min(), df_lower[df_lower["Bodega"] == "LDA"]["X-arm"].max()),
            "BULK": (df_lower[df_lower["Bodega"] == "BULK"]["X-arm"].min(), df_lower[df_lower["Bodega"] == "BULK"]["X-arm"].max())
        }
        y_max = 2.5
        y_min = -2.5

        for bodega, (x_min, x_max) in x_ranges.items():
            if pd.notna(x_min) and pd.notna(x_max):
                # Línea izquierda
                shapes.append(
                    dict(
                        type="line",
                        x0=x_min-1,
                        y0=y_min-1,
                        x1=x_min-1,
                        y1=y_max+1,
                        line=dict(color="black", width=2, dash="dash")
                    )
                )
                # Línea derecha
                shapes.append(
                    dict(
                        type="line",
                        x0=x_max+1,
                        y0=y_min-1,
                        x1=x_max+1,
                        y1=y_max+1,
                        line=dict(color="black", width=2, dash="dash")
                    )
                )
                # Etiqueta de la bodega
                annotations.append(
                    dict(
                        x=(x_min + x_max) / 2,
                        y=y_max,
                        text=bodega,
                        showarrow=False,
                        font=dict(size=12, color="black"),
                        xanchor="center",
                        yanchor="bottom"
                    )
                )

    # Configurar el layout
    fig.update_layout(
        title="Distribución de Pallets en LDF, LDA y Bulk",
        xaxis=dict(title="X-arm (metros)", showgrid=True, range=[14, 55]),
        yaxis=dict(title="Y-arm (metros)", showgrid=True, range=[-2.5, 2.5], dtick=0.5),
        shapes=shapes,
        annotations=annotations,
        showlegend=False,
        plot_bgcolor="white",
        width=1000,
        height=300
    )

    # Añadir leyenda de colores
    for destino, color in color_map.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=10, color=color),
                name=destino,
                showlegend=True
            )
        )

    return fig