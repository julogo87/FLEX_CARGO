import streamlit as st
import os
import subprocess
import time
import json
import pandas as pd
import hashlib
from weight_balance import weight_balance_calculation
from restrictions_manager import manage_temporary_restrictions
from basic_data_manager import manage_basic_data
from add_removal_manager import manage_add_removal
from history_manager import manage_calculation_history
from data_models import CalculationState

st.set_page_config(
    layout="wide",
    page_title="Weight & Balance App",
    page_icon="✈️",
    initial_sidebar_state="expanded"
)

# Inject CSS to style the login and welcome pages
st.markdown(
    """
    <style>
    [data-testid="stToolbar"] {
        visibility: hidden;
    }
    .login-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 30px;
        border-radius: 15px;
        background-color: #ffffff; /* Fondo blanco para todo el contenedor */
        box-shadow: none; /* Sin sombra */
        text-align: center;
    }
    .login-logo {
        max-width: 200px;
        margin-bottom: 20px;
    }
    .login-title {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 20px;
    }
    .welcome-container {
        max-width: 1200px;
        margin: 40px auto;
        padding: 40px;
        border-radius: 20px;
        background-color: #ffffff; /* Fondo blanco sólido */
        box-shadow: none; /* Sin sombra */
        text-align: center;
    }
    .welcome-message {
        font-size: 2.5em;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 10px;
    }
    .welcome-subtext {
        font-size: 1.2em;
        color: #555;
        margin-bottom: 30px;
    }
    .options-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        padding: 20px 0;
    }
    .option-button {
        padding: 20px 30px;
        font-size: 1.2em;
        font-weight: 600;
        color: #ffffff;
        background-color: #1f77b4;
        border: none;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        min-width: 200px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .option-button:hover {
        background-color: #155a8a;
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    .option-button:active {
        transform: translateY(0);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = script_dir
logo_path = os.path.join(base_dir, "logo.png")
users_json_path = os.path.join(base_dir, "users.json")

def init_users_json():
    """Initialize users.json with a default admin user if it doesn't exist or is invalid."""
    default_users = [
        {
            "Usuario": "admin",
            "Nombre Completo": "Administrador Principal",
            "Cargo": "Ingeniero",
            "Rol": "admin",
            "Licencia": "LIC123",
            "Password": hashlib.sha256("admin123".encode()).hexdigest(),
            "Active": True
        }
    ]
    try:
        if not os.path.exists(users_json_path):
            with open(users_json_path, "w", encoding="utf-8") as f:
                json.dump(default_users, f, indent=4, ensure_ascii=False)
            st.info("Archivo users.json creado con usuario admin por defecto.")
            return default_users

        with open(users_json_path, "r", encoding="utf-8") as f:
            users = json.load(f)

        required_fields = ["Usuario", "Cargo", "Rol", "Licencia", "Password", "Active"]
        for user in users:
            if not all(field in user for field in required_fields):
                raise ValueError(f"Faltan campos requeridos en users.json para usuario: {user.get('Usuario', 'desconocido')}")
            if "Nombre Completo" not in user:
                user["Nombre Completo"] = user["Usuario"]
        return users

    except Exception as e:
        st.error(f"Error al procesar users.json: {str(e)}. Creando archivo por defecto.")
        with open(users_json_path, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users

def save_users_json(users):
    """Save users to users.json."""
    try:
        with open(users_json_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error al guardar users.json: {str(e)}")

def check_credentials(username, password):
    """Check if the provided username and password are valid."""
    users = init_users_json()
    hashed_input_password = hashlib.sha256(password.encode()).hexdigest()
    for user in users:
        if user["Usuario"] == username:
            if user["Active"]:
                return user["Password"] == hashed_input_password
            else:
                st.error("La cuenta no está activa. Contacte al administrador.")
                return False
    st.error("Usuario no encontrado.")
    return False

def register_user():
    """Display the registration interface."""
    st.markdown('<div class="login-title">Registro de Nuevo Usuario</div>', unsafe_allow_html=True)
    with st.form(key="register_form", clear_on_submit=True):
        new_user = st.text_input("Usuario", placeholder="Ingrese su nombre de usuario")
        new_full_name = st.text_input("Nombre Completo", placeholder="Ingrese su nombre completo")
        new_cargo = st.text_input("Cargo", placeholder="Ingrese su cargo")
        new_rol = st.selectbox("Rol", ["user", "Manager"], index=0)
        new_licencia = st.text_input("Licencia", placeholder="Ingrese su licencia")
        new_password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
        confirm_password = st.text_input("Confirmar Contraseña", type="password", placeholder="Confirme su contraseña")
        submit = st.form_submit_button("Registrarse")

        if submit:
            if not all([new_user, new_full_name, new_cargo, new_licencia, new_password, confirm_password]):
                st.error("Por favor, complete todos los campos.")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden.")
            else:
                users = init_users_json()
                if any(user["Usuario"] == new_user for user in users):
                    st.error("El usuario ya existe.")
                else:
                    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                    new_user_data = {
                        "Usuario": new_user,
                        "Nombre Completo": new_full_name,
                        "Cargo": new_cargo,
                        "Rol": new_rol,
                        "Licencia": new_licencia,
                        "Password": hashed_password,
                        "Active": False
                    }
                    users.append(new_user_data)
                    save_users_json(users)
                    st.success("Registro enviado. Espere la aprobación del administrador.")

def login():
    """Display the login landing page."""
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        if os.path.exists(logo_path):
            st.image(logo_path, width=200)
        else:
            st.markdown('<div class="login-logo">Logo no encontrado</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="login-title">Weight & Balance App</div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            with st.form(key="login_form", clear_on_submit=True):
                username = st.text_input("Usuario", placeholder="Ingrese su nombre de usuario", key="login_user")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña", key="login_pass")
                submit = st.form_submit_button("Iniciar Sesión")

                if submit:
                    if check_credentials(username, password):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        users = init_users_json()
                        for user in users:
                            if user["Usuario"] == username:
                                st.session_state["user_role"] = user["Rol"]
                                st.session_state["full_name"] = user["Nombre Completo"]
                                break
                        st.success(f"Bienvenido, {st.session_state['full_name']}!")
                        st.rerun()
        
        with tab2:
            register_user()
        
        st.markdown('</div>', unsafe_allow_html=True)

def start_flask_server():
    flask_script = os.path.join(base_dir, "flask_server.py")
    if not os.path.exists(flask_script):
        st.error("No se encontró flask_server.py en la raíz del proyecto.")
        return None
    try:
        process = subprocess.Popen(["python", flask_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        if process.poll() is not None:
            st.error("No se pudo iniciar el servidor Flask. Verifique flask_server.py y las dependencias.")
            return None
        return process
    except Exception as e:
        st.error(f"Error al iniciar el servidor Flask: {str(e)}")
        return None

def manage_users():
    """User management interface for admins."""
    st.sidebar.markdown("### Gestión de Usuarios")
    users = init_users_json()
    
    with st.sidebar.expander("Aprobar Usuarios Pendientes", expanded=False):
        st.subheader("Usuarios Pendientes")
        pending_users = [u for u in users if not u["Active"]]
        if not pending_users:
            st.write("No hay usuarios pendientes.")
        else:
            for user in pending_users:
                st.write(f"Usuario: {user['Usuario']}, Nombre Completo: {user['Nombre Completo']}, Cargo: {user['Cargo']}, Rol: {user['Rol']}")
                if st.button(f"Aprobar {user['Usuario']}", key=f"approve_{user['Usuario']}"):
                    for u in users:
                        if u["Usuario"] == user["Usuario"]:
                            u["Active"] = True
                            break
                    save_users_json(users)
                    st.sidebar.success(f"Usuario {user['Usuario']} aprobado.")
    
    with st.sidebar.expander("Agregar Nuevo Usuario", expanded=False):
        st.subheader("Agregar Usuario")
        new_user = st.text_input("Usuario", key="new_user")
        new_full_name = st.text_input("Nombre Completo", key="new_full_name")
        new_cargo = st.text_input("Cargo", key="new_cargo")
        new_rol = st.selectbox("Rol", ["admin", "user", "Manager"], key="new_rol")
        new_licencia = st.text_input("Licencia", key="new_licencia")
        new_password = st.text_input("Contraseña", type="password", key="new_password")
        if st.button("Agregar Usuario", key="add_user"):
            if new_user and new_full_name and new_cargo and new_licencia and new_password:
                if any(u["Usuario"] == new_user for u in users):
                    st.sidebar.error("El usuario ya existe.")
                else:
                    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                    new_user_data = {
                        "Usuario": new_user,
                        "Nombre Completo": new_full_name,
                        "Cargo": new_cargo,
                        "Rol": new_rol,
                        "Licencia": new_licencia,
                        "Password": hashed_password,
                        "Active": True
                    }
                    users.append(new_user_data)
                    save_users_json(users)
                    st.sidebar.success(f"Usuario {new_user} agregado.")
            else:
                st.sidebar.error("Por favor, complete todos los campos.")

    with st.sidebar.expander("Editar Usuario", expanded=False):
        st.subheader("Editar Usuario")
        edit_user = st.selectbox("Seleccione usuario", [u["Usuario"] for u in users], key="edit_user_select")
        user_data = next(u for u in users if u["Usuario"] == edit_user)
        edit_full_name = st.text_input("Nombre Completo", value=user_data["Nombre Completo"], key="edit_full_name")
        edit_cargo = st.text_input("Cargo", value=user_data["Cargo"], key="edit_cargo")
        edit_rol = st.selectbox("Rol", ["admin", "user", "Manager"], index=["admin", "user", "Manager"].index(user_data["Rol"]), key="edit_rol")
        edit_licencia = st.text_input("Licencia", value=user_data["Licencia"], key="edit_licencia")
        edit_password = st.text_input("Nueva Contraseña (dejar en blanco para no cambiar)", type="password", key="edit_password")
        edit_active = st.checkbox("Activo", value=user_data["Active"], key="edit_active")
        if st.button("Actualizar Usuario", key="update_user"):
            if edit_user == "admin" and edit_rol != "admin":
                st.sidebar.error("No se puede cambiar el rol del usuario admin.")
            else:
                for u in users:
                    if u["Usuario"] == edit_user:
                        u["Nombre Completo"] = edit_full_name
                        u["Cargo"] = edit_cargo
                        u["Rol"] = edit_rol
                        u["Licencia"] = edit_licencia
                        u["Active"] = edit_active
                        if edit_password:
                            u["Password"] = hashlib.sha256(edit_password.encode()).hexdigest()
                        break
                save_users_json(users)
                st.sidebar.success(f"Usuario {edit_user} actualizado.")

    with st.sidebar.expander("Eliminar Usuario", expanded=False):
        st.subheader("Eliminar Usuario")
        delete_user = st.selectbox("Seleccione usuario", [u["Usuario"] for u in users if u["Usuario"] != "admin"], key="delete_user_select")
        if st.button("Eliminar Usuario", key="delete_user"):
            users = [u for u in users if u["Usuario"] != delete_user]
            save_users_json(users)
            st.sidebar.success(f"Usuario {delete_user} eliminado.")

def home_page():
    """Display a modern home page with system options."""
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.markdown('<div class="welcome-logo">Logo no encontrado</div>', unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div class="welcome-message">¡Bienvenido, {st.session_state.get("full_name", st.session_state["username"])}!</div>
        <div class="welcome-subtext">Selecciona una opción para comenzar</div>
        <div class="options-grid">
        """,
        unsafe_allow_html=True
    )

    all_pages = [
        {"name": "Cálculo de Peso y Balance", "key": "weight_balance"},
        {"name": "Gestión de Restricciones Temporales", "key": "restrictions"},
        {"name": "Gestión de Datos Básicos", "key": "basic_data"},
        {"name": "Adiciones/Remociones", "key": "add_removal"},
        {"name": "Historial de Cálculos", "key": "history"}
    ]

    if st.session_state["user_role"] == "Manager":
        available_pages = all_pages
    else:
        available_pages = [p for p in all_pages if p["name"] != "Gestión de Datos Básicos"]

    # Usar columnas para organizar los botones
    num_columns = 3
    cols = st.columns(num_columns)
    for idx, page in enumerate(available_pages):
        with cols[idx % num_columns]:
            if st.button(page['name'], key=page['key'], use_container_width=True):
                st.session_state.selected_page = page['name']
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

def setup_sidebar():
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=150)
    else:
        st.sidebar.warning("No se encontró el archivo del logo en la ruta especificada.")

    st.sidebar.title(f"Bienvenido, {st.session_state.get('full_name', st.session_state['username'])}")
    
    if st.sidebar.button("Volver a Inicio", key="return_home"):
        st.session_state.selected_page = "Home"
        st.rerun()

    if st.sidebar.button("Cerrar Sesión", key="logout"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["user_role"] = None
        st.session_state["full_name"] = None
        if 'flask_process' in st.session_state and st.session_state.flask_process:
            st.session_state.flask_process.terminate()
            del st.session_state.flask_process
        st.rerun()

    if st.session_state["user_role"] == "admin":
        manage_users()

    # Sidebar navigation only shown when not on home page
    if st.session_state.get("selected_page") != "Home":
        all_pages = [
            "Cálculo de Peso y Balance",
            "Gestión de Restricciones Temporales",
            "Gestión de Datos Básicos",
            "Adiciones/Remociones",
            "Historial de Cálculos"
        ]
        if st.session_state["user_role"] == "Manager":
            available_pages = all_pages
        else:
            available_pages = [p for p in all_pages if p != "Gestión de Datos Básicos"]

        st.sidebar.title("Navegación")
        page = st.sidebar.selectbox("Seleccione una página", available_pages, index=available_pages.index(st.session_state.get("selected_page", available_pages[0])))
        
        if page == "Cálculo de Peso y Balance":
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
            
            if st.sidebar.button("Desasignar Todas las Posiciones", key="deassign_all"):
                if "calculation_state" in st.session_state and st.session_state.calculation_state.df is not None:
                    preserved_flight_data = {
                        "operador_manual": st.session_state.get("operador_manual"),
                        "numero_vuelo_manual": st.session_state.get("numero_vuelo_manual"),
                        "matricula_manual": st.session_state.get("matricula_manual"),
                        "fecha_vuelo_manual": st.session_state.get("fecha_vuelo_manual"),
                        "hora_vuelo_manual": st.session_state.get("hora_vuelo_manual"),
                        "ruta_vuelo_manual": st.session_state.get("ruta_vuelo_manual"),
                        "revision_manual": st.session_state.get("revision_manual"),
                        "destino_inicial": st.session_state.get("destino_inicial"),
                        "normal_fuel": st.session_state.get("normal_fuel"),
                        "ballast_fuel": st.session_state.get("ballast_fuel"),
                        "trip_fuel": st.session_state.get("trip_fuel"),
                        "taxi_fuel": st.session_state.get("taxi_fuel"),
                        "fuel_mode": st.session_state.get("fuel_mode"),
                        "tipo_carga": st.session_state.get("tipo_carga"),
                        "takeoff_runway": st.session_state.get("takeoff_runway"),
                        "rwy_condition": st.session_state.get("rwy_condition"),
                        "flaps_conf": st.session_state.get("flaps_conf"),
                        "temperature": st.session_state.get("temperature"),
                        "air_condition": st.session_state.get("air_condition"),
                        "anti_ice": st.session_state.get("anti_ice"),
                        "qnh": st.session_state.get("qnh"),
                        "performance_tow": st.session_state.get("performance_tow"),
                        "performance_lw": st.session_state.get("performance_lw"),
                        "passengers_cockpit": st.session_state.get("passengers_cockpit"),
                        "passengers_supernumerary": st.session_state.get("passengers_supernumerary"),
                        "selected_tail": st.session_state.get("selected_tail")
                    }
                    
                    st.session_state.calculation_state.df["Posición Asignada"] = ""
                    st.session_state.calculation_state.df["X-arm"] = None
                    st.session_state.calculation_state.df["Y-arm"] = None
                    st.session_state.calculation_state.df["Momento X"] = None
                    st.session_state.calculation_state.df["Momento Y"] = None
                    st.session_state.calculation_state.df["Bodega"] = None
                    st.session_state.calculation_state.df["Rotated"] = False
                    st.session_state.calculation_state.posiciones_usadas.clear()
                    st.session_state.calculation_state.rotaciones.clear()
                    
                    for key, value in preserved_flight_data.items():
                        if value is not None:
                            st.session_state[key] = value
                    
                    st.sidebar.success("Todas las posiciones han sido desasignadas.")
                    st.rerun()
                else:
                    st.sidebar.warning("No hay un manifiesto cargado para desasignar.")
            
            if st.sidebar.button("Borrar y Reiniciar Cálculo", key="reset_calculation_left"):
                preserved_tail = st.session_state.get("selected_tail")
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
                
                if preserved_tail:
                    st.session_state.selected_tail = preserved_tail
                
                st.sidebar.success("Cálculo reiniciado. Por favor, cargue un nuevo manifiesto.")
            st.sidebar.markdown("---")
            with st.sidebar.expander("Calculadora Dynamic MZFW", expanded=False):
                st.subheader("Calcular Dynamic MZFW a partir de MTOW")
                mtowd_input = st.number_input(
                    "Ingrese MTOWD (kg)",
                    min_value=0.0,
                    value=227000.0,
                    step=1000.0,
                    format="%.1f"
                )
                if mtowd_input > 0:
                    mzfwd_result = (440600 - mtowd_input) / 1.2
                    st.write(f"**Dynamic MZFW Calculado:** {mzfwd_result:,.1f} kg")
                else:
                    st.write("Por favor, ingrese un valor válido para MTOWD.")

            st.sidebar.markdown("---")
            st.sidebar.markdown("### Accesos Rápidos")
            sections = [
                ("Carga de Datos Iniciales", "carga_datos_iniciales_section"),
                ("Restricciones Temporales Activas", "restrictions_section"),
                ("Información del Vuelo", "flight_info_section"),
                ("Carga del Manifiesto", "manifest_section"),
                ("Datos del Vuelo (Manifiesto Manual)", "manifest_flight_info_section"),
                ("Datos del Manifiesto", "manifest_data_section"),
                ("Modo de Cálculo", "calculation_mode_section"),
                ("Asignación Manual de Posiciones", "manual_assignment_section"),
                ("Validación de Pesos Acumulativos", "validation_section"),
                ("Resumen de Carga Asignada", "results_section"),
                ("Resumen Final de Peso y Balance", "summary_section"),
                ("Envelope", "envelope_section"),
                ("LIR", "main_deck_distribution_section"),
                ("Exportación", "export_section")
            ]
            for label, anchor in sections:
                st.sidebar.markdown(f'<a href="#{anchor}" style="text-decoration: none;">{label}</a>', unsafe_allow_html=True)
                
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Importar Cálculo Previo (Opcional)")
            json_file = st.sidebar.file_uploader("Seleccione el archivo JSON", type="json", key="json_import")
            if json_file and "json_imported" not in st.session_state:
                st.session_state.json_imported = json_file
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("Creado por Julian Londoño")
        st.sidebar.markdown("En colaboración con: Sabrina Agudelo, Mauricio Betancur, Efrain Chinchilla," \
        " Sergio Rua, Jose Gómez y Alejandro Tapias")
        st.sidebar.markdown("---")
        st.sidebar.markdown("Versión 0.8")
        st.sidebar.markdown("---")
        st.sidebar.markdown("Avianca Cargo")
        st.sidebar.markdown("Mayo 2025")
        
        return page
    return None

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["user_role"] = None
        st.session_state["full_name"] = None
        st.session_state["selected_page"] = "Home"

    if not st.session_state["authenticated"]:
        login()
        return

    if st.session_state.get("selected_page", "Home") == "Home":
        home_page()
    else:
        page = setup_sidebar()
        if page:
            st.session_state.selected_page = page
        else:
            st.session_state.selected_page = "Home"
            home_page()
            return

        if page == "Cálculo de Peso y Balance":
            if 'flask_process' in st.session_state:
                st.session_state.flask_process = start_flask_server()
            weight_balance_calculation()
        elif page == "Gestión de Restricciones Temporales":
            manage_temporary_restrictions()
        elif page == "Gestión de Datos Básicos":
            manage_basic_data()
        elif page == "Adiciones/Remociones":
            manage_add_removal()
        elif page == "Historial de Cálculos":
            manage_calculation_history()

if __name__ == "__main__":
    main()