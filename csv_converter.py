import pandas as pd
import os

def convertir_excel_a_csv_tabular(filepath):
    # Cargar el archivo sin encabezado
    df_raw = pd.read_excel(filepath, header=None)

    # Buscar la fila que contiene los encabezados
    header_row = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains("Contour", case=False).any():
            header_row = i
            break

    if header_row is None:
        raise ValueError("No se encontró la fila con encabezados tipo 'Contour'.")

    # Extraer los encabezados y el contenido desde esa fila hacia abajo
    df_clean = pd.read_excel(filepath, header=header_row)

    # Filtrar solo las columnas que nos interesan (puede adaptarse si cambia el orden)
    columnas_objetivo = [
        "Contour",
        "Number ULD",
        "ULD Final Destination",
        "Weight (KGS)",
        "Pieces",
        "Notes"
    ]
    columnas_presentes = [col for col in columnas_objetivo if col in df_clean.columns]
    df_final = df_clean[columnas_presentes].dropna(how="all")

    # Guardar como CSV con formato requerido
    nombre_salida = os.path.splitext(filepath)[0] + "_estandarizado.csv"
    df_final.to_csv(nombre_salida, sep=";", index=False, encoding="latin1")
    print(f"✅ Archivo convertido y guardado como: {nombre_salida}")

# Ejemplo de uso:
# convertir_excel_a_csv_tabular("LCS QT-4045 _AGT-SCL_ 29MARZO2025.xlsx")
