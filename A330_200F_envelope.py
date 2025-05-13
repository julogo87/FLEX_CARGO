import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

def plot_cg_envelope(zfw_weight, zfw_mac, tow_weight, tow_mac, lw_weight, lw_mac):
    alpha = 15
    max_peso = 240000

    def proyectar_mac(mac, peso):
        if mac < 25:
            return mac - alpha * (peso / max_peso)
        elif mac > 25:
            return mac + alpha * (peso / max_peso)
        else:
            return mac

    def proyectar_curva(x_vals, y_vals):
        return [proyectar_mac(mac, peso) for mac, peso in zip(x_vals, y_vals)], y_vals

    # Datos originales de envolventes
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

    # Aplicar proyección a las curvas
    x_takeoff_fwd, y_takeoff_fwd = proyectar_curva(x_takeoff_fwd, y_takeoff_fwd)
    x_takeoff_aft, y_takeoff_aft = proyectar_curva(x_takeoff_aft, y_takeoff_aft)
    x_cruise_fwd, y_cruise_fwd = proyectar_curva(x_cruise_fwd, y_cruise_fwd)
    x_cruise_aft, y_cruise_aft = proyectar_curva(x_cruise_aft, y_cruise_aft)
    x_landing_fwd, y_landing_fwd = proyectar_curva(x_landing_fwd, y_landing_fwd)
    x_landing_aft, y_landing_aft = proyectar_curva(x_landing_aft, y_landing_aft)

    # Proyectar los valores de CG
    zfw_mac_proj = proyectar_mac(zfw_mac, zfw_weight)
    tow_mac_proj = proyectar_mac(tow_mac, tow_weight)
    lw_mac_proj = proyectar_mac(lw_mac, lw_weight)

    takeoff_color = '#FF8C00'
    cruise_color = '#1E90FF'
    landing_color = '#32CD32'

    fig, ax = plt.subplots(figsize=(12, 9))

    # Plotear envolventes
    ax.plot(x_takeoff_fwd, y_takeoff_fwd, color=takeoff_color, linewidth=2)
    ax.plot(x_takeoff_aft, y_takeoff_aft, color=takeoff_color, linewidth=2)
    ax.fill_betweenx(y_takeoff_fwd, x_takeoff_fwd, np.interp(y_takeoff_fwd, y_takeoff_aft, x_takeoff_aft), color=takeoff_color, alpha=0.15)

    ax.plot(x_cruise_fwd, y_cruise_fwd, color=cruise_color, linewidth=2)
    ax.plot(x_cruise_aft, y_cruise_aft, color=cruise_color, linewidth=2)
    y_fill_cruise = np.linspace(min(y_cruise_fwd), max(y_cruise_aft), 300)
    ax.fill_betweenx(y_fill_cruise, np.interp(y_fill_cruise, y_cruise_fwd, x_cruise_fwd), np.interp(y_fill_cruise, y_cruise_aft, x_cruise_aft), color=cruise_color, alpha=0.15)

    ax.plot(x_landing_fwd, y_landing_fwd, color=landing_color, linewidth=2)
    ax.plot(x_landing_aft, y_landing_aft, color=landing_color, linewidth=2)
    y_fill_landing = np.linspace(min(y_landing_fwd), max(y_landing_aft), 300)
    ax.fill_betweenx(y_fill_landing, np.interp(y_fill_landing, y_landing_fwd, x_landing_fwd), np.interp(y_fill_landing, y_landing_aft, x_landing_aft), color=landing_color, alpha=0.15)

    # Plotear puntos CG
    ax.plot(zfw_mac_proj, zfw_weight, 'bo', label='ZFW CG', markersize=10)
    ax.plot(tow_mac_proj, tow_weight, marker='o', color=takeoff_color, label='TOW CG', markersize=10)
    ax.plot(lw_mac_proj, lw_weight, 'go', label='LW CG', markersize=10)

    # Líneas de referencia
    ax.axhline(178000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 179000, "MZFW", fontsize=11, color='gray', weight='bold')
    ax.axhline(116000, color='gray', linestyle='--', linewidth=1.5)
    ax.text(44, 117000, "Minimum Weight", fontsize=11, color='gray', weight='bold')

    # Configuración del gráfico
    ax.set_ylabel("Peso (kg)", fontsize=12)
    ax.set_xlabel("% MAC Proyectado", fontsize=12)
    ax.set_title("Envolvente de Centro de Gravedad vs Peso - A330-200F", fontsize=14, weight='bold')

    ax.text(43, 230000, "Takeoff", fontsize=12, weight='bold', bbox=dict(facecolor=takeoff_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    ax.text(43, 222000, "Cruise", fontsize=12, weight='bold', bbox=dict(facecolor=cruise_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))
    ax.text(43, 214000, "Landing", fontsize=12, weight='bold', bbox=dict(facecolor=landing_color, edgecolor='black', boxstyle='round,pad=0.3', alpha=0.8))

    ax.legend(loc='upper left')
    ax.minorticks_on()
    ax.grid(True, which='major', linestyle='--', alpha=0.4)
    ax.grid(True, which='minor', linestyle=':', alpha=0.3)

    plt.tight_layout()

    # Devolver datos de la envolvente para validación
    return {
        "fig": fig,
        "takeoff": {
            "fwd": {"x": x_takeoff_fwd, "y": y_takeoff_fwd},
            "aft": {"x": x_takeoff_aft, "y": y_takeoff_aft}
        },
        "cruise": {
            "fwd": {"x": x_cruise_fwd, "y": y_cruise_fwd},
            "aft": {"x": x_cruise_aft, "y": y_cruise_aft}
        },
        "landing": {
            "fwd": {"x": x_landing_fwd, "y": y_landing_fwd},
            "aft": {"x": x_landing_aft, "y": y_landing_aft}
        },
        "projected_cg": {
            "zfw": zfw_mac_proj,
            "tow": tow_mac_proj,
            "lw": lw_mac_proj
        }
    }