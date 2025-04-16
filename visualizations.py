import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import to_rgba
import textwrap

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
        st.markdown(f'<div class="summary-item"><b>TOW:</b> {tow:,.1f} kg (MAC: {tow_mac:,.1f}%)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MTOW:</b> {mtow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Trip Fuel:</b> {trip_fuel:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>LW:</b> {lw:,.1f} kg (MAC: {lw_mac:,.1f}%)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>MLW:</b> {mlw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Performance LW:</b> {performance_lw:,.1f} kg</div>' if performance_lw > 0 else '<div class="summary-item"><b>Performance LW:</b> No especificado</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Pitch Trim:</b> {pitch_trim:,.1f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Desbalance Lateral:</b> {lateral_imbalance:,.1f} kg (Límite: {lateral_imbalance_limit:,.1f} kg)</div>', unsafe_allow_html=True)
    with col4:
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
            total_bodega_weight = bodega_summary["Weight (KGS)"].sum()
            for _, row in bodega_summary.iterrows():
                st.markdown(f'<div class="summary-item"> - {row["Bodega"]}: {row["Weight (KGS)"]:,.1f} kg</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="summary-item"><b>Total:</b> {total_bodega_weight:,.1f} kg</div>', unsafe_allow_html=True)
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
        
    with col8:
        st.markdown(f'<div class="summary-item"><b>Carga Máx. LW:</b> {max_payload_lw:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Carga Máx. TOW:</b> {max_payload_tow:,.1f} kg</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-item"><b>Carga Máx. ZFW:</b> {max_payload_zfw:,.1f} kg</div>', unsafe_allow_html=True)
        
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
    df_md = df[df["Bodega"] == "MD"].copy()
    if df_md.empty:
        st.warning("No hay pallets asignados en Main Deck.")
        return None

    required_columns = ["X-arm", "Y-arm", "Number ULD", "Posición Asignada", "Weight (KGS)", "ULD Final Destination", "Contour", "Notes"]
    missing_columns = [col for col in required_columns if col not in df_md.columns]
    if missing_columns:
        st.error(f"Faltan columnas en el DataFrame: {', '.join(missing_columns)}")
        return None

    df_md = df_md.dropna(subset=["X-arm", "Y-arm", "Posición Asignada", "Weight (KGS)"])
    df_md = df_md[pd.to_numeric(df_md["X-arm"], errors='coerce').notnull()]
    df_md = df_md[pd.to_numeric(df_md["Y-arm"], errors='coerce').notnull()]
    df_md = df_md[pd.to_numeric(df_md["Weight (KGS)"], errors='coerce').notnull()]
    
    if df_md.empty:
        st.warning("No hay datos válidos para graficar en Main Deck.")
        return None

    destinos = df_md["ULD Final Destination"].astype(str).unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(destinos)))
    color_map = {dest: to_rgba(colors[i], alpha=0.6) for i, dest in enumerate(destinos)}

    fig, ax = plt.subplots(figsize=(22, 6))

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

            if pos in ["CFR", "FJR", "JLR", "LPR"]:
                width = 2
                height = 4
            elif pos in ["CFG", "FJG", "JLG"]:
                width = 2
                height = 6
            else:
                width = 2
                height = 2

            rect = patches.Rectangle(
                (x - width / 2, y - height / 2),
                width,
                height,
                linewidth=1,
                edgecolor='gray',
                facecolor=color_map[destino],
                label=destino
            )
            ax.add_patch(rect)

            max_text_width = int(width * 8)
            wrapped_notas = textwrap.wrap(notas, width=max_text_width, break_long_words=True)[:3]
            wrapped_notas = '\n'.join(wrapped_notas)

            line_height = height / 12
            fontsize = 9
            notes_fontsize = 8

            ax.text(x, y + 3 * line_height, pos, ha='center', va='center', fontsize=fontsize, color='red', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y + 2 * line_height, uld, ha='center', va='center', fontsize=fontsize, color='black', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y + line_height, f"{peso:,.1f} kg", ha='center', va='center', fontsize=fontsize, color='black', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y, destino, ha='center', va='center', fontsize=fontsize, color='black', wrap=True, clip_on=True)
            ax.text(x, y - line_height, contorno, ha='center', va='center', fontsize=fontsize, color='black', wrap=True, clip_on=True)
            ax.text(x, y - height / 2 + line_height / 2, f"Notas: {wrapped_notas}", ha='center', va='bottom', fontsize=notes_fontsize, color='black', wrap=True, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'), clip_on=True)
        except (ValueError, TypeError) as e:
            st.warning(f"Error al procesar pallet {uld}: {str(e)}")
            continue

    ax.set_xlim(14, 55)
    ax.set_ylim(-2.5, 2.5)
    ax.set_yticks(np.arange(-2.5, 3.0, 0.5))
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Distribución de Pallets en Main Deck")
    ax.grid(True)

    handles = [patches.Patch(color=color, label=destino, alpha=0.6) for destino, color in color_map.items()]
    ax.legend(handles=handles, loc='upper right', fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def plot_lower_decks(df):
    df_lower = df[df["Bodega"].isin(["LDF", "LDA", "BULK"])].copy()
    if df_lower.empty:
        st.warning("No hay pallets asignados en LDF, LDA o Bulk.")
        return None

    required_columns = ["X-arm", "Y-arm", "Number ULD", "Posición Asignada", "Weight (KGS)", "ULD Final Destination", "Contour", "Bodega", "Notes"]
    missing_columns = [col for col in required_columns if col not in df_lower.columns]
    if missing_columns:
        st.error(f"Faltan columnas en el DataFrame: {', '.join(missing_columns)}")
        return None

    df_lower = df_lower.dropna(subset=["X-arm", "Y-arm", "Posición Asignada", "Weight (KGS)", "Bodega"])
    df_lower = df_lower[pd.to_numeric(df_lower["X-arm"], errors='coerce').notnull()]
    df_lower = df_lower[pd.to_numeric(df_lower["Y-arm"], errors='coerce').notnull()]
    df_lower = df_lower[pd.to_numeric(df_lower["Weight (KGS)"], errors='coerce').notnull()]
    
    if df_lower.empty:
        st.warning("No hay datos válidos para graficar en LDF, LDA o Bulk.")
        return None

    destinos = df_lower["ULD Final Destination"].astype(str).unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(destinos)))
    color_map = {dest: to_rgba(colors[i], alpha=0.6) for i, dest in enumerate(destinos)}

    fig, ax = plt.subplots(figsize=(22, 6))

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

            width = 1.5
            height = 1.5

            rect = patches.Rectangle(
                (x - width / 2, y - height / 2),
                width,
                height,
                linewidth=1,
                edgecolor='gray',
                facecolor=color_map[destino],
                label=destino
            )
            ax.add_patch(rect)

            max_text_width = int(width * 8)
            wrapped_notas = textwrap.wrap(notas, width=max_text_width, break_long_words=True)[:3]
            wrapped_notas = '\n'.join(wrapped_notas)

            line_height = height / 12
            fontsize = 8
            notes_fontsize = 7

            ax.text(x, y + 3 * line_height, pos, ha='center', va='center', fontsize=fontsize, color='red', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y + 2 * line_height, uld, ha='center', va='center', fontsize=fontsize, color='black', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y + line_height, f"{peso:,.1f} kg", ha='center', va='center', fontsize=fontsize, color='black', fontweight='bold', wrap=True, clip_on=True)
            ax.text(x, y, destino, ha='center', va='center', fontsize=fontsize, color='black', wrap=True, clip_on=True)
            ax.text(x, y - line_height, contorno, ha='center', va='center', fontsize=fontsize, color='black', wrap=True, clip_on=True)
            ax.text(x, y - height / 2 + line_height / 2, f"Notas: {wrapped_notas}", ha='center', va='bottom', fontsize=notes_fontsize, color='black', wrap=True, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'), clip_on=True)
        except (ValueError, TypeError) as e:
            st.warning(f"Error al procesar pallet {uld}: {str(e)}")
            continue

    ax.set_xlim(14, 55)
    ax.set_ylim(-2.5, 2.5)
    ax.set_yticks(np.arange(-2.5, 3.0, 0.5))
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Distribución de Pallets en LDF, LDA y Bulk")
    ax.grid(True)

    handles = [patches.Patch(color=color, label=destino, alpha=0.6) for destino, color in color_map.items()]
    ax.legend(handles=handles, loc='upper right', fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()