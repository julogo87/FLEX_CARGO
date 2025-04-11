# N342AV_envelope.py
import matplotlib.pyplot as plt

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
        matplotlib.pyplot: Objeto de gráfico para mostrar en Streamlit.
    """
    # Datos de la envolvente
    peso = [116000, 169000, 179000, 182000, 210000, 233000]
    fwd_takeoff = [18, 18, 18, 18, 18, 21.4]
    aft_takeoff = [32, 32, 39.3, 39.3, 39.3, 37.4]
    fwd_cruise = [17, 17, 17, 17, None, 20.4]
    aft_cruise = [41, 41, 41, 41, 41, 38.2]
    fwd_landing = [18, 18, 18, 18, None, None]
    aft_landing = [40, 40, 40, 39.2, None, None]

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

    # Crear la gráfica
    plt.figure(figsize=(10, 6))

    # TAKEOFF
    plt.plot(x_takeoff_fwd, y_takeoff, color=takeoff_color, linewidth=2)
    plt.plot(x_takeoff_aft, y_takeoff, color=takeoff_color, linewidth=2)
    plt.fill_betweenx(y_takeoff, x_takeoff_fwd, x_takeoff_aft, color=takeoff_color, alpha=0.15)
    plt.plot([x_takeoff_fwd[-1], x_takeoff_aft[-1]], [y_takeoff[-1], y_takeoff[-1]], linestyle='--', color=takeoff_color, linewidth=1.5)

    # CRUISE
    plt.plot(x_cruise_fwd, y_cruise, color=cruise_color, linewidth=2)
    plt.plot(x_cruise_aft, y_cruise, color=cruise_color, linewidth=2)
    plt.fill_betweenx(y_cruise, x_cruise_fwd, x_cruise_aft, color=cruise_color, alpha=0.15)
    plt.plot([x_cruise_fwd[-1], x_cruise_aft[-1]], [y_cruise[-1], y_cruise[-1]], linestyle='--', color=cruise_color, linewidth=1.5)

    # LANDING
    plt.plot(x_landing_fwd, y_landing, color=landing_color, linewidth=2)
    plt.plot(x_landing_aft, y_landing, color=landing_color, linewidth=2)
    plt.fill_betweenx(y_landing, x_landing_fwd, x_landing_aft, color=landing_color, alpha=0.15)
    plt.plot([x_landing_fwd[-1], x_landing_aft[-1]], [y_landing[-1], y_landing[-1]], linestyle='--', color=landing_color, linewidth=1.5)

    # Graficar los puntos de ZFW, TOW y LW
    plt.plot(zfw_mac, zfw_weight, 'go', label='ZFW CG', markersize=10)
    plt.plot(tow_mac, tow_weight, 'ro', label='TOW CG', markersize=10)
    plt.plot(lw_mac, lw_weight, 'bo', label='LW CG', markersize=10)

    # Líneas horizontales adicionales
    plt.axhline(170000, color='gray', linestyle='--', linewidth=1.5)
    plt.text(44, 171000, "MZFW", fontsize=11, color='gray', weight='bold')

    plt.axhline(116000, color='gray', linestyle='--', linewidth=1.5)
    plt.text(44, 117000, "Minimum Weight", fontsize=11, color='gray', weight='bold')

    # Ejes y título
    plt.ylabel("Peso (kg)", fontsize=12)
    plt.xlabel("% MAC", fontsize=12)
    plt.title("Envolvente de Centro de Gravedad vs Peso", fontsize=14, weight='bold')

    # Leyenda personalizada por fase
    plt.text(43, 230000, "Takeoff", fontsize=12, weight='bold',
             bbox=dict(facecolor=takeoff_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    plt.text(43, 222000, "Cruise", fontsize=12, weight='bold',
             bbox=dict(facecolor=cruise_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    plt.text(43, 214000, "Landing", fontsize=12, weight='bold',
             bbox=dict(facecolor=landing_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))

    # Leyenda para los puntos ZFW, TOW, LW
    plt.legend(loc='upper left')

    # Cuadrícula detallada
    plt.minorticks_on()
    plt.grid(True, which='major', linestyle='--', alpha=0.4)
    plt.grid(True, which='minor', linestyle=':', alpha=0.3)

    plt.tight_layout()
    return plt