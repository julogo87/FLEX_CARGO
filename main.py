import streamlit as st
import os
from weight_balance import weight_balance_calculation
from restrictions_manager import manage_temporary_restrictions
from basic_data_manager import manage_basic_data
from data_models import CalculationState  # Importar CalculationState

# Configurar el modo wide para expandir el ancho de la página
st.set_page_config(layout="wide")

# Directorio base
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir

# Ruta del logo
logo_path = os.path.join(base_dir, "logo.png")

# Configurar el sidebar izquierdo
def setup_sidebar():
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=150)
    else:
        st.sidebar.warning("No se encontró el archivo del logo en la ruta especificada.")

    st.sidebar.title("Navegación")
    page = st.sidebar.selectbox("Seleccione una página", ["Cálculo de Peso y Balance", "Gestión de Restricciones Temporales", "Gestión de Datos Básicos"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Acciones")
    if st.sidebar.button("Actualizar Lista de Pallets", key="update_pallets_left"):
        if "calculation_state" in st.session_state and st.session_state.calculation_state.df is not None:
            st.session_state.calculation_state.df = st.session_state.calculation_state.df.copy()
            st.session_state.calculation_state.posiciones_usadas = st.session_state.calculation_state.posiciones_usadas.copy()
            st.session_state.calculation_state.rotaciones = st.session_state.calculation_state.rotaciones.copy()
            st.sidebar.success("Lista de pallets actualizada.")
        else:
            st.sidebar.warning("No hay un manifiesto cargado para actualizar.")
    
    if st.sidebar.button("Borrar y Reiniciar Cálculo", key="reset_calculation_left"):
        if "calculation_state" in st.session_state:
            del st.session_state.calculation_state
        if "manifiesto_manual" in st.session_state:
            del st.session_state.manifiesto_manual
        if "edit_count" in st.session_state:
            del st.session_state.edit_count
        if "json_imported" in st.session_state:
            del st.session_state.json_imported
        st.session_state.calculation_state = CalculationState(
            df=None,
            posiciones_usadas=set(),
            rotaciones={},
            bow=0.0,
            bow_moment_x=0.0,
            bow_moment_y=0.0,
            moment_x_fuel_tow=0.0,
            moment_y_fuel_tow=0.0,
            moment_x_fuel_lw=0.0,
            moment_y_fuel_lw=0.0,
            passengers_cockpit_total_weight=0.0,
            passengers_cockpit_total_moment_x=0.0,
            passengers_supernumerary_total_weight=0.0,
            passengers_supernumerary_total_moment_x=0.0,
            fuel_distribution={
                "Outer Tank LH": 0.0,
                "Outer Tank RH": 0.0,
                "Inner Tank LH": 0.0,
                "Inner Tank RH": 0.0,
                "Center Tank": 0.0,
                "Trim Tank": 0.0
            },
            fuel_mode="Automático"
        )
        st.sidebar.success("Cálculo reiniciado. Por favor, cargue un nuevo manifiesto.")

    if page == "Cálculo de Peso y Balance":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Accesos Rápidos")
        sections = [
            ("Restricciones Temporales Activas", "restrictions_section"),
            ("Información del Vuelo", "flight_info_section"),
            ("Carga del Manifiesto", "manifest_section"),
            ("Información del Vuelo para el Manifiesto", "manifest_flight_info_section"),
            ("Datos del Manifiesto", "manifest_data_section"),
            ("Modo de Cálculo", "calculation_mode_section"),
            ("Asignación Manual de Posiciones", "manual_assignment_section"),
            ("Desasignar Pallets", "desassign_pallets_section"),
            ("Validación de Pesos Acumulativos", "validation_section"),
            ("Resumen Final de Peso y Balance", "summary_section"),
            ("Resultados del Cálculo", "results_section"),
            ("Envelope", "envelope_section")
        ]
        for label, anchor in sections:
            st.sidebar.markdown(f'<a href="#{anchor}" style="text-decoration: none;">{label}</a>', unsafe_allow_html=True)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Importar Cálculo Previo (Opcional)")
        json_file = st.sidebar.file_uploader("Seleccione el archivo JSON", type="json", key="json_import")
        if json_file and "json_imported" not in st.session_state:
            st.session_state.json_imported = json_file

    
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Creado por [Creatividad y Ansiedad]")
    st.sidebar.markdown("Versión 0.1")
    
    return page

# Main execution
def main():
    page = setup_sidebar()

    if page == "Cálculo de Peso y Balance":
        weight_balance_calculation()
    elif page == "Gestión de Restricciones Temporales":
        manage_temporary_restrictions()
    elif page == "Gestión de Datos Básicos":
        manage_basic_data()

if __name__ == "__main__":
    main()