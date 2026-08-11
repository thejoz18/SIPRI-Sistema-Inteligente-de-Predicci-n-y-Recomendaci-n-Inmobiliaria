"""Módulo 02: preparación del dataset para los modelos inmobiliarios.

Este módulo no entrena modelos ni completa valores faltantes. Conserva únicamente
los registros aprobados manualmente (decision_humana = SI) y mantiene el texto
original disponible en la columna texto_limpio para los módulos de TF-IDF.
"""

from pathlib import Path

import pandas as pd


# ============================================
# 1. RUTAS DEL PROYECTO
# ============================================
CARPETA_PROYECTO = Path(__file__).resolve().parent
ARCHIVO_ENTRADA = CARPETA_PROYECTO / "datos" / "base_validada.xlsx"
ARCHIVO_SALIDA = CARPETA_PROYECTO / "datos" / "dataset_modelos.xlsx"


# ============================================
# 2. CARGAR LA BASE VALIDADA
# ============================================
if not ARCHIVO_ENTRADA.exists():
    raise FileNotFoundError(
        "No se encontró datos/base_validada.xlsx. "
        "Coloca ahí la base validada antes de ejecutar este módulo."
    )

archivo_excel = pd.ExcelFile(ARCHIVO_ENTRADA)

if "REVISION" not in archivo_excel.sheet_names:
    raise ValueError(
        "No se encontró la hoja REVISION. "
        f"Hojas disponibles: {archivo_excel.sheet_names}"
    )

df = pd.read_excel(ARCHIVO_ENTRADA, sheet_name="REVISION")

print("=" * 80)
print("MÓDULO 02 - DATASET PARA MODELOS")
print("=" * 80)
print(f"Registros originales: {len(df)}")
print(f"Número de columnas: {len(df.columns)}")
print("\nColumnas reales de la base:")
for columna in df.columns:
    print(f"- {columna}")


# ============================================
# 3. VALIDAR LA COLUMNA DE REVISIÓN HUMANA
# ============================================
COLUMNA_DECISION = "decision_humana"

if COLUMNA_DECISION not in df.columns:
    raise ValueError(
        f"La columna obligatoria '{COLUMNA_DECISION}' no existe en la base."
    )

decision_normalizada = df[COLUMNA_DECISION].fillna("").astype(str).str.strip().str.upper()

print("\nDistribución de decision_humana:")
print(decision_normalizada.value_counts().to_string())


# ============================================
# 4. CONSERVAR SOLO REGISTROS MARCADOS COMO SI
# ============================================
# Los registros NO no se modifican en la base_validada.xlsx.
# Solo se excluyen del archivo específico que usarán los modelos.
dataset_modelos = df.loc[decision_normalizada == "SI"].copy()

if dataset_modelos.empty:
    raise ValueError("No existen registros con decision_humana = SI.")

print(f"\nRegistros para entrenamiento (SI): {len(dataset_modelos)}")
print(f"Registros excluidos (NO u otro valor): {len(df) - len(dataset_modelos)}")


# ============================================
# 5. REVISAR CAMPOS ÚTILES PARA LOS SIGUIENTES MÓDULOS
# ============================================
campos_modelos = [
    "texto_limpio",
    "Tipo_Mensaje",
    "operacion_validada",
    "tipo_propiedad_validado",
    "precio_renta_validado",
    "precio_venta_validado",
    "metros_validado",
    "habitaciones_validado",
    "banos_validado",
    "estacionamientos_validado",
    "alberca_validado",
    "vigilancia_validado",
    "jardin_validado",
    "terraza_validado",
    "balcon_validado",
    "amueblado_validado",
    "aire_acondicionado_validado",
    "cocina_integral_validado",
    "gimnasio_validado",
    "elevador_validado",
    "bodega_validado",
    "roof_garden_validado",
    "cuarto_servicio_validado",
    "estudio_validado",
]

print("\nDisponibilidad de campos para modelos:")
for campo in campos_modelos:
    if campo in dataset_modelos.columns:
        disponibles = dataset_modelos[campo].notna().sum()
        print(f"- {campo}: {disponibles} de {len(dataset_modelos)} valores disponibles")
    else:
        print(f"- {campo}: NO EXISTE EN LA BASE")

print("\nClases disponibles para futuras clasificaciones:")
for campo in ["Tipo_Mensaje", "operacion_validada", "tipo_propiedad_validado"]:
    if campo in dataset_modelos.columns:
        print(f"\n{campo}:")
        print(dataset_modelos[campo].fillna("SIN_DATO").value_counts().to_string())


# ============================================
# 6. GUARDAR EL DATASET SIN IMPUTAR NI INVENTAR VALORES
# ============================================
ARCHIVO_SALIDA.parent.mkdir(parents=True, exist_ok=True)
dataset_modelos.to_excel(ARCHIVO_SALIDA, sheet_name="DATASET_MODELOS", index=False)

print("\n" + "=" * 80)
print("DATASET CREADO CORRECTAMENTE")
print(f"Archivo: {ARCHIVO_SALIDA}")
print(f"Filas guardadas: {len(dataset_modelos)}")
print("El texto y todas las columnas originales se conservaron para reproducibilidad.")
print("=" * 80)
