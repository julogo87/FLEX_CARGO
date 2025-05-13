import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

def plot_cg_envelope(zfw_weight, zfw_mac, tow_weight, tow_mac, lw_weight, lw_mac):
    """
    Genera un gráfico de la envolvente de CG (Centro de Gravedad) para ZFW, TOW y LW,
    específico para la aeronave N342AV.
    
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

    # Datos de la envolvente
    peso = [116000, 169000, 179000, 182000, 210000, 233000]
    fwd_takeoff = [18, 18, 18, 18, 18, 21.4]
    aft_takeoff = [32, 32, 39.3, 39.3, 39.3, 37.4]
    fwd_cruise = [17, 17, 17, 17, 17, 20.4]
    aft_cruise = [41, 41, 41, 41, 41, 38.2]
    fwd_landing = [18, 18, 18, 18, 18, 18]
    aft_landing = [40, 40, 40, 39.2, 39.2, 39.2]

    # Colores por fase
    takeoff_color = '#FF8C00'
    cruise_color = '#1E90FF'
    landing_color = '#32CD32'

    # Función para filtrar datos válidos
    def filter_pair_valid(x1, x2, y):
        return [(a, b, c) for a, b, c in zip(x1, x2, y) if a is not None and b is not None]

    # Datos filtrados
    takeoff_valid = filter_pair_valid(fwd_takeoff, aft_takeoff, peso)
    cruise_valid = filter_pair_valid(fwd_cruise, aft_cruise, peso)
    landing_valid = filter_pair_valid(fwd_landing, aft_landing, peso)

    x_takeoff_fwd, x_takeoff_aft, y_takeoff = zip(*takeoff_valid)
    x_cruise_fwd, x_cruise_aft, y_cruise = zip(*cruise_valid)
    x_landing_fwd, x_landing_aft, y_landing = zip(*landing_valid)

    # Función para verificar si un punto está dentro de la envolvente
    def is_point_in_envelope(mac, weight, x_fwd, x_aft, y):
        try:
            if len(x_fwd) < 2 or len(x_aft) < 2 or len(y) < 2:
                st.warning("Insufficient data points for envelope interpolation")
                return False
            if weight < min(y) or weight > max(y):
                st.warning(f"Weight {weight:.1f} kg is outside envelope range [{min(y):.1f}, {max(y):.1f}]")
                return False
            # Asegurar que los arrays estén ordenados por y
            sorted_indices = np.argsort(y)
            y_sorted = np.array(y)[sorted_indices]
            x_fwd_sorted = np.array(x_fwd)[sorted_indices]
            x_aft_sorted = np.array(x_aft)[sorted_indices]
            x_fwd_interp = np.interp(weight, y_sorted, x_fwd_sorted)
            x_aft_interp = np.interp(weight, y_sorted, x_aft_sorted)
            return x_fwd_interp <= mac <= x_aft_interp
        except Exception as e:
            st.warning(f"Error in envelope interpolation: {str(e)}")
            return False

    # Verificar si los puntos CG están dentro de las envolventes
    alerts = []
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_takeoff_fwd, x_takeoff_aft, y_takeoff):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Takeoff.")
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_cruise_fwd, x_cruise_aft, y_cruise):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Cruise.")
    if not is_point_in_envelope(zfw_mac, zfw_weight, x_landing_fwd, x_landing_aft, y_landing):
        alerts.append(f"ZFW CG ({zfw_weight:.1f} kg, {zfw_mac:.1f}% MAC) está fuera de la envolvente de Landing.")

    if not is_point_in_envelope(tow_mac, tow_weight, x_takeoff_fwd, x_takeoff_aft, y_takeoff):
        alerts.append(f"TOW CG ({tow_weight:.1f} kg, {tow_mac:.1f}% MAC) está fuera de la envolvente de Takeoff.")
    if not is_point_in_envelope(tow_mac, tow_weight, x_cruise_fwd, x_cruise_aft, y_cruise):
        alerts.append(f"TOW CG ({tow_weight:.1f} kg, {tow_mac:.1f}% MAC) está fuera de la envolvente de Cruise.")

    if not is_point_in_envelope(lw_mac, lw_weight, x_landing_fwd, x_landing_aft, y_landing):
        alerts.append(f"LW CG ({lw_weight:.1f} kg, {lw_mac:.1f}% MAC) está fuera de la envolvente de Landing.")

    # Mostrar advertencias si hay puntos fuera de las envolventes
    for alert in alerts:
        st.warning(alert)

    # Crear la figura
    fig, ax = plt.subplots(figsize=(10, 6))

    # TAKEOFF
    sorted_indices = np.argsort(y_takeoff)
    y_takeoff_sorted = np.array(y_takeoff)[sorted_indices]
    x_takeoff_fwd_sorted = np.array(x_takeoff_fwd)[sorted_indices]
    x_takeoff_aft_sorted = np.array(x_takeoff_aft)[sorted_indices]
    ax.plot(x_takeoff_fwd_sorted, y_takeoff_sorted, color=takeoff_color, linewidth=2)
    ax.plot(x_takeoff_aft_sorted, y_takeoff_sorted, color=takeoff_color, linewidth=2)
    ax.fill_betweenx(y_takeoff_sorted, x_takeoff_fwd_sorted, x_takeoff_aft_sorted, 
                     color=takeoff_color, alpha=0.15)

    # CRUISE
    sorted_indices = np.argsort(y_cruise)
    y_cruise_sorted = np.array(y_cruise)[sorted_indices]
    x_cruise_fwd_sorted = np.array(x_cruise_fwd)[sorted_indices]
    x_cruise_aft_sorted = np.array(x_cruise_aft)[sorted_indices]
    ax.plot(x_cruise_fwd_sorted, y_cruise_sorted, color=cruise_color, linewidth=2)
    ax.plot(x_cruise_aft_sorted, y_cruise_sorted, color=cruise_color, linewidth=2)
    ax.fill_betweenx(y_cruise_sorted, x_cruise_fwd_sorted, x_cruise_aft_sorted, 
                     color=cruise_color, alpha=0.15)

    # LANDING
    sorted_indices = np.argsort(y_landing)
    y_landing_sorted = np.array(y_landing)[sorted_indices]
    x_landing_fwd_sorted = np.array(x_landing_fwd)[sorted_indices]
    x_landing_aft_sorted = np.array(x_landing_aft)[sorted_indices]
    ax.plot(x_landing_fwd_sorted, y_landing_sorted, color=landing_color, linewidth=2)
    ax.plot(x_landing_aft_sorted, y_landing_sorted, color=landing_color, linewidth=2)
    ax.fill_betweenx(y_landing_sorted, x_landing_fwd_sorted, x_landing_aft_sorted, 
                     color=landing_color, alpha=0.15)

    # Graficar los puntos de ZFW, TOW y LW con los colores solicitados
    ax.plot(zfw_mac, zfw_weight, 'bo', label='ZFW CG', markersize=10)
    ax.plot(tow_mac, tow_weight, marker='o', color='#FF8C00', label='TOW CG', markersize=10)
    ax.plot(lw_mac, lw_weight, 'go', label='LW CG', markersize=10)

    # Líneas horizontales adicionales
    ax.axhline(170000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 171000, "MZFW", fontsize=11, color='gray', weight='bold')

    ax.axhline(116000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 117000, "Minimum Weight", fontsize=11, color='gray', weight='bold')

    # Ejes y título
    ax.set_ylabel("Peso (kg)", fontsize=12)
    ax.set_xlabel("% MAC", fontsize=12)
    ax.set_title("Envolvente de Centro de Gravedad vs Peso - N342AV", fontsize=14, weight='bold')

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