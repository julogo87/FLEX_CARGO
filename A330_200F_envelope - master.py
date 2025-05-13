import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

def plot_cg_envelope(zfw_weight, zfw_mac, tow_weight, tow_mac, lw_weight, lw_mac):
    """
    Genera un gráfico de la envolvente de CG (Centro de Gravedad) para ZFW, TOW y LW,
    específico para la aeronave A330-200F con envolventes personalizadas.

    Args:
        zfw_weight (float): Peso en Zero Fuel Weight (kg).
        zfw_mac (float): %MAC en Zero Fuel Weight.
        tow_weight (float): Peso en Takeoff Weight (kg).
        tow_mac (float): %MAC en Takeoff Weight.
        lw_weight (float): Peso en Landing Weight (kg).
        lw_mac (float): %MAC en Landing Weight.

    Returns:
        matplotlib.figure.Figure: Objeto de figura para mostrar en Streamlit.
    """
    # Validate inputs
    inputs = {
        "ZFW Weight": zfw_weight,
        "ZFW MAC": zfw_mac,
        "TOW Weight": tow_weight,
        "TOW MAC": tow_mac,
        "LW Weight": lw_weight,
        "LW MAC": lw_mac
    }
    for name, value in inputs.items():
        if value is None or np.isnan(value):
            st.error(f"Invalid input: {name} is {value}")
            return None

    # Colores por fase
    takeoff_color = '#FF8C00'  # Naranja para Takeoff
    cruise_color = '#1E90FF'   # Azul claro para Cruise
    landing_color = '#32CD32'  # Verde claro para Landing

    # Colores para puntos CG
    zfw_color = 'bo'           # Azul para ZFW CG
    tow_color = '#FF8C00'      # Naranja para TOW CG
    lw_color = 'go'            # Verde para LW CG

    # Función para verificar si un punto está dentro de la envolvente
    def is_point_in_envelope(mac, weight, x_fwd, x_aft, y):
        try:
            if len(x_fwd) < 2 or len(x_aft) < 2 or len(y) < 2:
                st.warning("Insufficient data points for envelope interpolation")
                return False
            if weight < min(y) or weight > max(y):
                st.warning(f"Weight {weight:.1f} kg is outside envelope range [{min(y):.1f}, {max(y):.1f}]")
                return False
            
            # Asegurar que los arrays estén ordenados por y (peso)
            sorted_indices = np.argsort(y)
            y_sorted = np.array(y)[sorted_indices]
            x_fwd_sorted = np.array(x_fwd)[sorted_indices]
            x_aft_sorted = np.array(x_aft)[sorted_indices]
            
            # Interpolar los valores de x_fwd y x_aft para el peso dado
            x_fwd_interp = np.interp(weight, y_sorted, x_fwd_sorted)
            x_aft_interp = np.interp(weight, y_sorted, x_aft_sorted)
            return x_fwd_interp <= mac <= x_aft_interp
        except Exception as e:
            st.warning(f"Error in envelope interpolation: {str(e)}")
            return False

    # Definir datos de las envolventes
    x_takeoff_fwd = [15, 15, 21.4]
    y_takeoff_fwd = [116000, 193200, 233000]
    x_takeoff_aft = [31.39, 39.30, 37.40]
    y_takeoff_aft = [116000, 179000, 233000]

    x_cruise_fwd = [12.13, 12.24, 14.19, 14.5, 21]
    y_cruise_fwd = [109000, 118760, 121760, 193200, 233000]
    x_cruise_aft = [25, 25, 40, 40, 37.4]
    y_cruise_aft = [109000, 116000, 116000, 165000, 233000]

    x_landing_fwd = [13, 13, 15, 15]
    y_landing_fwd = [109000, 118760, 121760, 187000]
    x_landing_aft = [25, 25, 40, 40]
    y_landing_aft = [109000, 116000, 116000, 187000]

    # Verificar si los puntos CG están dentro de las envolventes
    alerts = []
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_takeoff_fwd, x_takeoff_aft, y_takeoff_fwd):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Takeoff.")
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_cruise_fwd, x_cruise_aft, y_cruise_fwd):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Cruise.")
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_landing_fwd, x_landing_aft, y_landing_fwd):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Landing.")

    if not is_point_in_envelope(tow_mac, tow_weight, x_takeoff_fwd, x_takeoff_aft, y_takeoff_fwd):
        alerts.append(f"TOW CG ({tow_weight:.1f} kg, {tow_mac:.1f}% MAC) está fuera de la envolvente de Takeoff.")
    if not is_point_in_envelope(tow_mac, tow_weight, x_cruise_fwd, x_cruise_aft, y_cruise_fwd):
        alerts.append(f"TOW CG ({tow_weight:.1f} kg, {tow_mac:.1f}% MAC) está fuera de la envolvente de Cruise.")

    if not is_point_in_envelope(lw_mac, lw_weight, x_landing_fwd, x_landing_aft, y_landing_fwd):
        alerts.append(f"LW CG ({lw_weight:.1f} kg, {lw_mac:.1f}% MAC) está fuera de la envolvente de Landing.")

    # Mostrar advertencias si hay puntos fuera de las envolventes
    for alert in alerts:
        st.warning(alert)

    # Crear la figura
    fig, ax = plt.subplots(figsize=(10, 6))

    # TAKEOFF
    ax.plot(x_takeoff_fwd, y_takeoff_fwd, color=takeoff_color, linewidth=2)
    ax.plot(x_takeoff_aft, y_takeoff_aft, color=takeoff_color, linewidth=2)
    ax.fill_betweenx(y_takeoff_fwd, x_takeoff_fwd, np.interp(y_takeoff_fwd, y_takeoff_aft, x_takeoff_aft), 
                     color=takeoff_color, alpha=0.15)

    # CRUISE
    ax.plot(x_cruise_fwd, y_cruise_fwd, color=cruise_color, linewidth=2)
    ax.plot(x_cruise_aft, y_cruise_aft, color=cruise_color, linewidth=2)
    y_fill_cruise = np.linspace(min(y_cruise_fwd), max(y_cruise_aft), 300)
    ax.fill_betweenx(y_fill_cruise, np.interp(y_fill_cruise, y_cruise_fwd, x_cruise_fwd), 
                     np.interp(y_fill_cruise, y_cruise_aft, x_cruise_aft), color=cruise_color, alpha=0.15)

    # LANDING
    ax.plot(x_landing_fwd, y_landing_fwd, color=landing_color, linewidth=2)
    ax.plot(x_landing_aft, y_landing_aft, color=landing_color, linewidth=2)
    y_fill_landing = np.linspace(min(y_landing_fwd), max(y_landing_aft), 300)
    ax.fill_betweenx(y_fill_landing, np.interp(y_fill_landing, y_landing_fwd, x_landing_fwd), 
                     np.interp(y_fill_landing, y_landing_aft, x_landing_aft), color=landing_color, alpha=0.15)

    # Graficar los puntos de ZFW, TOW y LW con los colores especificados
    ax.plot(zfw_mac, zfw_weight, zfw_color, label='ZFW CG', markersize=10)
    ax.plot(tow_mac, tow_weight, marker='o', color=tow_color, label='TOW CG', markersize=10)
    ax.plot(lw_mac, lw_weight, lw_color, label='LW CG', markersize=10)

    # Líneas horizontales para MZFW y Minimum Weight
    ax.axhline(178000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 179000, "MZFW", fontsize=11, color='gray', weight='bold')
    ax.axhline(116000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 117000, "Minimum Weight", fontsize=11, color='gray', weight='bold')

    # Ejes y título
    ax.set_ylabel("Peso (kg)", fontsize=12)
    ax.set_xlabel("% MAC", fontsize=12)
    ax.set_title("Envolvente de Centro de Gravedad vs Peso - A330-200F", fontsize=14, weight='bold')

    # Leyenda personalizada por fase
    ax.text(43, 230000, "Takeoff", fontsize=12, weight='bold',
            bbox=dict(facecolor=takeoff_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    ax.text(43, 222000, "Cruise", fontsize=12, weight='bold',
            bbox=dict(facecolor=cruise_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    ax.text(43, 214000, "Landing", fontsize=12, weight='bold',
            bbox=dict(facecolor=landing_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))

    # Leyenda para los puntos ZFW, TOW, LW
    ax.legend(loc='upper left')

    # Cuadrícula detallada
    ax.minorticks_on()
    ax.grid(True, which='major', linestyle='--', alpha=0.4)
    ax.grid(True, which='minor', linestyle=':', alpha=0.3)

    plt.tight_layout()
    return fig