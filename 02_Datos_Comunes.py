"""Datos y rutas compartidos por los módulos de modelos."""

from pathlib import Path

import pandas as pd


CARPETA_PROYECTO = Path(__file__).resolve().parent
ARCHIVO_DATASET = CARPETA_PROYECTO / "datos" / "dataset_modelos.xlsx"
CARPETA_GRAFICAS = CARPETA_PROYECTO / "resultados" / "graficas"
CARPETA_METRICAS = CARPETA_PROYECTO / "resultados" / "metricas"
CARPETA_MODELOS = CARPETA_PROYECTO / "resultados" / "modelos_guardados"

AMENIDADES = [
    "alberca_validado", "vigilancia_validado", "jardin_validado",
    "terraza_validado", "balcon_validado", "amueblado_validado",
    "aire_acondicionado_validado", "cocina_integral_validado",
    "gimnasio_validado", "elevador_validado", "bodega_validado",
    "roof_garden_validado", "cuarto_servicio_validado", "estudio_validado",
]


def cargar_dataset():
    if not ARCHIVO_DATASET.exists():
        raise FileNotFoundError(
            "No se encontró datos/dataset_modelos.xlsx. Ejecuta primero 02_Dataset_Modelos.py."
        )
    return pd.read_excel(ARCHIVO_DATASET, sheet_name="DATASET_MODELOS")


def preparar_datos_precio(operacion="RENTA"):
    """Devuelve X, y y las filas completas sin llenar valores faltantes."""
    df = cargar_dataset()
    operacion = operacion.upper()

    if operacion == "RENTA":
        columna_precio = "precio_renta_validado"
    elif operacion == "VENTA":
        columna_precio = "precio_venta_validado"
    else:
        raise ValueError("La operación debe ser RENTA o VENTA.")

    caracteristicas = ["habitaciones_validado"] + AMENIDADES
    columnas_necesarias = ["operacion_validada", columna_precio] + caracteristicas
    datos = df.loc[df["operacion_validada"] == operacion, columnas_necesarias].copy()
    datos = datos[datos[columna_precio] > 0].dropna()

    if len(datos) < 10:
        raise ValueError(
            f"No hay suficientes registros completos para estimar precio de {operacion}."
        )

    return datos[caracteristicas], datos[columna_precio], caracteristicas, columna_precio


def filtrar_por_intencion(publicaciones, texto, ubicacion="", naturaleza_objetivo=None):
    """Filtra por operación, propiedad y ubicación cuando el usuario las escribió claramente."""
    texto = texto.lower()
    candidatos = publicaciones.copy()
    filtros = []

    if naturaleza_objetivo and "naturaleza_validada" in candidatos.columns:
        candidatos = candidatos[candidatos["naturaleza_validada"] == naturaleza_objetivo]
        filtros.append(f"contraparte: {naturaleza_objetivo}")

    if any(palabra in texto for palabra in ["venta", "vendo", "vender", "comprar", "compro"]):
        candidatos = candidatos[candidatos["operacion_validada"] == "VENTA"]
        filtros.append("operación: VENTA")
    elif any(palabra in texto for palabra in ["renta", "rento", "alquilo", "alquiler"]):
        candidatos = candidatos[candidatos["operacion_validada"] == "RENTA"]
        filtros.append("operación: RENTA")

    propiedades = {
        "departamento": "DEPARTAMENTO",
        "casa": "CASA",
        "terreno": "TERRENO",
        "local": "LOCAL",
        "bodega": "BODEGA",
        "cuarto": "CUARTO",
        "penthouse": "PENTHOUSE",
    }
    for palabra, categoria in propiedades.items():
        if palabra in texto:
            candidatos = candidatos[candidatos["tipo_propiedad_validado"] == categoria]
            filtros.append(f"propiedad: {categoria}")
            break

    ubicacion = ubicacion.strip().lower()
    if ubicacion:
        columnas_ubicacion = candidatos["texto_limpio"].fillna("").astype(str)
        if "direccion_validada" in candidatos.columns:
            columnas_ubicacion = columnas_ubicacion + " " + candidatos["direccion_validada"].fillna("").astype(str)

        coincidencia_ubicacion = columnas_ubicacion.str.lower().str.contains(
            ubicacion, regex=False, na=False
        )
        if coincidencia_ubicacion.any():
            candidatos = candidatos[coincidencia_ubicacion]
            filtros.append(f"ubicación: {ubicacion.upper()}")
        else:
            filtros.append(f"ubicación sin coincidencia exacta: {ubicacion.upper()}")

    if candidatos.empty:
        return publicaciones.copy(), "sin filtro aplicable; se usó la base completa"

    if not filtros:
        return candidatos, "sin filtros explícitos"
    return candidatos, ", ".join(filtros)
