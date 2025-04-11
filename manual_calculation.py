# manual_calculation.py
import streamlit as st
import matplotlib.pyplot as plt

def update_position_values(df, idx, new_position, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
    row = df.loc[idx]
    restric = restricciones_df[restricciones_df["Position"] == new_position]
    
    if restric.empty:
        st.error(f"Posición {new_position} inválida.")
        return False
    
    temp_restr_sym = restric["Temp_Restriction_Symmetric"].values[0]
    temp_restr_asym = restric["Temp_Restriction_Asymmetric"].values[0]
    if tipo_carga == "simetrico":
        peso_max = temp_restr_sym if temp_restr_sym != 0 else restric["Symmetric_Max_Weight_(kg)_5%"].values[0]
    else:
        peso_max = temp_restr_asym if temp_restr_asym != 0 else restric["Asymmetric_Max_Weight_(kg)_5%"].values[0]
    
    if new_position in exclusiones_df.columns:
        excluded_positions = exclusiones_df.index[exclusiones_df[new_position] == 0].tolist()
        if any(pos in posiciones_usadas for pos in excluded_positions):
            st.error(f"La posición {new_position} está excluida por posiciones ya asignadas: {excluded_positions}")
            return False
    
    if row["Weight (KGS)"] > peso_max:
        st.error(f"El peso {row['Weight (KGS)']} kg excede el máximo permitido de {peso_max} kg para la posición {new_position}.")
        return False
        
    x_arm = restric["Average_X-Arm_(m)"].values[0]
    y_arm = restric["Average_Y-Arm_(m)"].values[0]
    
    df.at[idx, "X-arm"] = x_arm
    df.at[idx, "Y-arm"] = y_arm
    df.at[idx, "Momento X"] = round(x_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Momento Y"] = round(y_arm * row["Weight (KGS)"], 3)
    df.at[idx, "Posición Asignada"] = new_position
    df.at[idx, "Bodega"] = restric["Bodega"].values[0]
    
    return True

def manual_assignment(df, restricciones_df, tipo_carga, exclusiones_df, posiciones_usadas, rotaciones, tab_prefix=""):
    """
    Realiza la asignación manual de posiciones a los ULDs, permite desasignar pallets y muestra una gráfica por bodega.
    
    Args:
        df (pd.DataFrame): DataFrame con los datos del manifiesto.
        restricciones_df (pd.DataFrame): DataFrame con las restricciones.
        tipo_carga (str): Tipo de carga ("simetrico" o "asimetrico").
        exclusiones_df (pd.DataFrame): DataFrame con las exclusiones.
        posiciones_usadas (set): Conjunto de posiciones ya asignadas.
        rotaciones (dict): Diccionario de rotaciones.
        tab_prefix (str): Prefijo para las claves de los widgets, para evitar conflictos entre pestañas.
    """
    st.write("### Asignación Manual de Posiciones")
    st.write("Asigne posiciones manualmente a cada ULD.")

    # Filtrar ULDs pendientes de asignar
    ulds_pendientes = df[df["Posición Asignada"] == ""].copy()
    
    if ulds_pendientes.empty:
        st.success("Todos los ULDs han sido asignados.")
    else:
        st.write(f"ULDs pendientes de asignar: {len(ulds_pendientes)}")
        
        # Mostrar los ULDs pendientes como tarjetas, 4 por línea
        for i in range(0, len(ulds_pendientes), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(ulds_pendientes):
                    row = ulds_pendientes.iloc[i + j]
                    idx = row.name
                    uld = row["Number ULD"]
                    with cols[j]:
                        # Crear una tarjeta para cada ULD
                        st.markdown(
                            f"""
                            <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #f9f9f9;'>
                                <h4>{uld}</h4>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']} kg</p>
                                <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                <p><strong>Contour:</strong> {row['Contour']}</p>
                                <p><strong>Notas:</strong> {row['Notes']}</p>
                                <p><strong>Posiciones Sugeridas:</strong> {', '.join(row['Posiciones Sugeridas'])}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        # Campo de entrada y botón para asignar posición
                        new_pos = st.text_input(f"Ingrese la posición para {uld}", key=f"{tab_prefix}_pos_{uld}_{idx}")
                        if st.button("Asignar Posición", key=f"{tab_prefix}_assign_{uld}_{idx}"):
                            if new_pos:
                                if new_pos in posiciones_usadas:
                                    st.error("La posición ya está asignada a otro ULD.")
                                else:
                                    if update_position_values(df, idx, new_pos, restricciones_df, tipo_carga, posiciones_usadas, exclusiones_df):
                                        posiciones_usadas.add(new_pos)
                                        rotaciones[uld] = False
                                        df.at[idx, "Rotated"] = False
                                        st.success(f"{uld} asignado a {new_pos}")
                                        st.rerun()  # Refrescar la interfaz
                            else:
                                st.warning("Por favor, ingrese una posición válida.")

    # Añadir un botón de "Actualizar" fuera del bloque condicional
    st.write("### Actualizar Lista de Pallets")
    if st.button("Actualizar", key=f"{tab_prefix}_update"):
        st.rerun()  # Refrescar la interfaz para descontar los pallets asignados

    # Sección para desasignar pallets
    st.write("### Desasignar Pallets")
    st.write("Seleccione un pallet para desasignar su posición.")
    
    # Filtrar ULDs que ya tienen una posición asignada
    ulds_asignados = df[df["Posición Asignada"] != ""].copy()
    
    if ulds_asignados.empty:
        st.info("No hay ULDs asignados para desasignar.")
    else:
        st.write(f"ULDs asignados: {len(ulds_asignados)}")
        
        # Mostrar los ULDs asignados como tarjetas, 4 por línea
        for i in range(0, len(ulds_asignados), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(ulds_asignados):
                    row = ulds_asignados.iloc[i + j]
                    idx = row.name
                    uld = row["Number ULD"]
                    with cols[j]:
                        # Crear una tarjeta para cada ULD asignado
                        st.markdown(
                            f"""
                            <div style='border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: #e6f3ff;'>
                                <h4>{uld}</h4>
                                <p><strong>Posición Asignada:</strong> {row['Posición Asignada']}</p>
                                <p><strong>Peso:</strong> {row['Weight (KGS)']} kg</p>
                                <p><strong>Destino:</strong> {row['ULD Final Destination']}</p>
                                <p><strong>Contour:</strong> {row['Contour']}</p>
                                <p><strong>Notas:</strong> {row['Notes']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        # Botón para desasignar
                        if st.button("Desasignar", key=f"{tab_prefix}_deassign_{uld}_{idx}"):
                            # Eliminar la posición asignada y los valores asociados
                            position_to_remove = df.at[idx, "Posición Asignada"]
                            df.at[idx, "Posición Asignada"] = ""
                            df.at[idx, "X-arm"] = None
                            df.at[idx, "Y-arm"] = None
                            df.at[idx, "Momento X"] = None
                            df.at[idx, "Momento Y"] = None
                            df.at[idx, "Bodega"] = None
                            df.at[idx, "Rotated"] = False
                            # Eliminar la posición del conjunto posiciones_usadas
                            if position_to_remove in posiciones_usadas:
                                posiciones_usadas.remove(position_to_remove)
                            # Eliminar la entrada del diccionario rotaciones
                            if uld in rotaciones:
                                del rotaciones[uld]
                            st.success(f"Posición de {uld} desasignada.")
                            st.rerun()  # Refrescar la interfaz

    # Nueva sección para mostrar las gráficas por bodega
    st.write("### Distribución de Pallets por Bodega")
    st.write("Gráficas que muestran la ubicación de los pallets asignados en cada bodega.")

    # Filtrar pallets asignados (que tienen una bodega asignada)
    pallets_asignados = df[df["Posición Asignada"] != ""].copy()
    
    if pallets_asignados.empty:
        st.info("No hay pallets asignados para mostrar en las bodegas.")
    else:
        # Obtener las bodegas únicas
        bodegas = pallets_asignados["Bodega"].unique()
        
        # Primera fila: LDF, LDA, Bulk
        col1, col2, col3 = st.columns(3)
        
        # Función para generar la gráfica de una bodega
        def plot_bodega(bodega, pallets_bodega):
            fig, ax = plt.subplots(figsize=(5, 3))  # Tamaño más pequeño para que quepan en las columnas
            
            # Colores para los pallets (cíclicos)
            colors = plt.cm.tab20.colors  # Usar una paleta de colores predefinida
            
            for idx, row in pallets_bodega.iterrows():
                uld = row["Number ULD"]
                x_arm = row["X-arm"]
                y_arm = row["Y-arm"]
                
                # Obtener las dimensiones del baseplate (en pulgadas) y convertirlas a metros
                base_size = row["Pallet Base Size"]  # Ejemplo: "96x125"
                if base_size:
                    try:
                        width_inch, length_inch = map(float, base_size.split("x"))
                        # Convertir de pulgadas a metros (1 pulgada = 0.0254 metros)
                        width_m = width_inch * 0.0254
                        length_m = length_inch * 0.0254
                    except:
                        width_m, length_m = 1.0, 1.0  # Valores por defecto si no se pueden parsear
                else:
                    width_m, length_m = 1.0, 1.0  # Valores por defecto si no hay base_size
                
                # Calcular las coordenadas del rectángulo (centrado en X-arm, Y-arm)
                x_min = x_arm - (width_m / 2)
                y_min = y_arm - (length_m / 2)
                
                # Dibujar el rectángulo
                color = colors[idx % len(colors)]  # Seleccionar un color cíclico
                rect = plt.Rectangle((x_min, y_min), width_m, length_m, edgecolor='black', facecolor=color, alpha=0.6)
                ax.add_patch(rect)
                
                # Añadir el texto con el Number ULD en el centro del rectángulo
                ax.text(x_arm, y_arm, uld, ha='center', va='center', fontsize=8, color='black', weight='bold')
            
            # Configurar los ejes
            ax.set_xlabel("X-arm (metros)")
            ax.set_ylabel("Y-arm (metros)")
            ax.set_title(f"Bodega {bodega}")
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Ajustar los límites de los ejes para que todos los pallets sean visibles
            if not pallets_bodega.empty:
                x_min = pallets_bodega["X-arm"].min() - 2
                x_max = pallets_bodega["X-arm"].max() + 2
                y_min = pallets_bodega["Y-arm"].min() - 2
                y_max = pallets_bodega["Y-arm"].max() + 2
                # Asegurar que los rangos de los ejes sean simétricos para mantener la misma escala
                max_range = max(x_max - x_min, y_max - y_min)
                x_center = (x_max + x_min) / 2
                y_center = (y_max + y_min) / 2
                ax.set_xlim(x_center - max_range / 2, x_center + max_range / 2)
                ax.set_ylim(y_center - max_range / 2, y_center + max_range / 2)
            
            # Forzar la misma escala horizontal y vertical
            ax.set_aspect('equal', adjustable='box')
            
            return fig

        # Mostrar LDF (Lower Deck Forward) en la primera columna
        with col1:
            if "LDF" in bodegas:
                pallets_ldf = pallets_asignados[pallets_asignados["Bodega"] == "LDF"]
                fig_ldf = plot_bodega("LDF", pallets_ldf)
                st.pyplot(fig_ldf)
            else:
                st.write("#### Bodega: LDF")
                st.info("No hay pallets asignados en LDF.")

        # Mostrar LDA (Lower Deck Aft) en la segunda columna
        with col2:
            if "LDA" in bodegas:
                pallets_lda = pallets_asignados[pallets_asignados["Bodega"] == "LDA"]
                fig_lda = plot_bodega("LDA", pallets_lda)
                st.pyplot(fig_lda)
            else:
                st.write("#### Bodega: LDA")
                st.info("No hay pallets asignados en LDA.")

        # Mostrar Bulk en la tercera columna
        with col3:
            if "BULK" in bodegas:
                pallets_bulk = pallets_asignados[pallets_asignados["Bodega"] == "BULK"]
                fig_bulk = plot_bodega("BULK", pallets_bulk)
                st.pyplot(fig_bulk)
            else:
                st.write("#### Bodega: BULK")
                st.info("No hay pallets asignados en BULK.")

        # Mostrar MD (Main Deck) en una fila separada debajo
        if "MD" in bodegas:
            st.write("#### Bodega: MD")
            pallets_md = pallets_asignados[pallets_asignados["Bodega"] == "MD"]
            fig_md = plot_bodega("MD", pallets_md)
            st.pyplot(fig_md)
        else:
            st.write("#### Bodega: MD")
            st.info("No hay pallets asignados en MD.")