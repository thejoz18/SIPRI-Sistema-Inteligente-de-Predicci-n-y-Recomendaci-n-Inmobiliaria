# ============================================================
# AIVRI
# Algoritmo de IA para el sector inmobiliario
#
# MODULO 1
# LIMPIEZA Y PREPARACION DE DATOS
# ============================================================

import pandas as pd
import numpy as np
import re

import tkinter as tk
from tkinter import filedialog, messagebox


# ============================================================
# 1. CREAR VENTANA
# ============================================================

root = tk.Tk()
root.withdraw()


# ============================================================
# 2. SELECCIONAR ARCHIVO
# ============================================================

archivo_entrada = filedialog.askopenfilename(
    title="AIVRI - Selecciona la base inmobiliaria",
    filetypes=[
        ("Archivos Excel", "*.xlsx *.xls"),
        ("Archivos CSV", "*.csv"),
        ("Todos los archivos", "*.*")
    ]
)

if not archivo_entrada:

    messagebox.showwarning(
        "AIVRI",
        "No seleccionaste ningún archivo."
    )

    root.destroy()
    exit()


print("\n==========================================")
print("AIVRI - ARCHIVO SELECCIONADO")
print("==========================================")

print(archivo_entrada)


# ============================================================
# 3. CARGAR ARCHIVO
# ============================================================

try:

    if archivo_entrada.lower().endswith(".csv"):

        df = pd.read_csv(
            archivo_entrada,
            encoding="utf-8-sig"
        )

    else:

        df = pd.read_excel(
            archivo_entrada
        )

except Exception as error:

    messagebox.showerror(
        "Error al cargar",
        f"No se pudo abrir el archivo:\n\n{error}"
    )

    root.destroy()
    exit()


print("\nBase cargada correctamente.")
print("Registros:", len(df))
print("Columnas:", len(df.columns))


# ============================================================
# 4. NORMALIZAR NOMBRES DE COLUMNAS
# ============================================================

df.columns = (
    df.columns
    .str.strip()
)


# ============================================================
# 5. CREAR TEXTO COMPLETO
# ============================================================

df["Texto_Original"] = (
    df["Texto_Original"]
    .fillna("")
    .astype(str)
)

df["encabezado"] = (
    df["encabezado"]
    .fillna("")
    .astype(str)
)

df["cuerpo"] = (
    df["cuerpo"]
    .fillna("")
    .astype(str)
)


df["texto_completo"] = (
    df["Texto_Original"]
    + " "
    + df["encabezado"]
    + " "
    + df["cuerpo"]
)


# ============================================================
# 6. LIMPIAR TEXTO
# ============================================================

df["texto_limpio"] = (
    df["texto_completo"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)


# ============================================================
# 7. NORMALIZAR TIPO DE MENSAJE
# ============================================================

df["Tipo_Mensaje"] = (
    df["Tipo_Mensaje"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.strip()
)


# ============================================================
# 8. NORMALIZAR TIPO DE PROPIEDAD
# ============================================================

df["Tipo_Propiedad"] = (
    df["Tipo_Propiedad"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.strip()
)


# ============================================================
# 9. DETECTAR OPERACION
# ============================================================

def detectar_operacion(texto):

    texto = texto.lower()

    patrones_renta = [
        "renta",
        "rentar",
        "rentando",
        "alquiler",
        "en renta",
        "se renta"
    ]

    patrones_venta = [
        "venta",
        "vender",
        "vende",
        "vendemos",
        "en venta",
        "se vende"
    ]

    tiene_renta = any(
        palabra in texto
        for palabra in patrones_renta
    )

    tiene_venta = any(
        palabra in texto
        for palabra in patrones_venta
    )

    if tiene_renta and not tiene_venta:
        return "RENTA"

    if tiene_venta and not tiene_renta:
        return "VENTA"

    if tiene_renta and tiene_venta:
        return "AMBAS"

    return "NO_DEFINIDO"


df["Operacion_Texto"] = (
    df["texto_limpio"]
    .apply(detectar_operacion)
)


# ============================================================
# 10. DETECTAR OFERTA / SOLICITUD
# ============================================================

def detectar_naturaleza(texto):

    texto = texto.lower()

    patrones_solicitud = [
        "busco",
        "buscamos",
        "buscando",
        "solicito",
        "solicitamos",
        "necesito",
        "necesitamos",
        "quiero",
        "queremos",
        "requiero",
        "requiere"
    ]

    patrones_oferta = [
        "vendo",
        "vendemos",
        "se vende",
        "venta de",
        "rento",
        "rentamos",
        "se renta",
        "en renta",
        "en venta"
    ]

    tiene_solicitud = any(
        palabra in texto
        for palabra in patrones_solicitud
    )

    tiene_oferta = any(
        palabra in texto
        for palabra in patrones_oferta
    )

    if tiene_solicitud and not tiene_oferta:
        return "SOLICITUD"

    if tiene_oferta and not tiene_solicitud:
        return "OFERTA"

    if tiene_solicitud and tiene_oferta:
        return "AMBIGUO"

    return "NO_DEFINIDO"


df["Naturaleza_Texto"] = (
    df["texto_limpio"]
    .apply(detectar_naturaleza)
)


# ============================================================
# 11. CREAR CLASIFICACION FINAL
# ============================================================

def clasificar_mensaje(row):

    naturaleza = row["Naturaleza_Texto"]
    operacion = row["Operacion_Texto"]

    if naturaleza == "OFERTA" and operacion == "RENTA":
        return "OFERTA_RENTA"

    if naturaleza == "OFERTA" and operacion == "VENTA":
        return "OFERTA_VENTA"

    if naturaleza == "SOLICITUD" and operacion == "RENTA":
        return "SOLICITUD_RENTA"

    if naturaleza == "SOLICITUD" and operacion == "VENTA":
        return "SOLICITUD_VENTA"

    # Si el texto no permite determinarlo,
    # conservamos la clasificación original.

    original = row["Tipo_Mensaje"]

    if original in [
        "OFERTA_RENTA",
        "OFERTA_VENTA",
        "SOLICITUD"
    ]:
        return original

    return "NO_CLASIFICADO"


df["Tipo_Mensaje_Final"] = df.apply(
    clasificar_mensaje,
    axis=1
)


# ============================================================
# 12. EXTRAER HABITACIONES
# ============================================================

def extraer_habitaciones(texto):

    patrones = [

        r"(\d+)\s*habitaciones?",
        r"(\d+)\s*rec[aá]maras?",
        r"(\d+)\s*dormitorios?"

    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if resultado:

            return int(
                resultado.group(1)
            )

    return np.nan


df["Habitaciones"] = (
    df["texto_limpio"]
    .apply(extraer_habitaciones)
)


# ============================================================
# 13. EXTRAER BAÑOS
# ============================================================

def extraer_banos(texto):

    patrones = [

        r"(\d+)\s*baños?",
        r"(\d+)\s*wc"
    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if resultado:

            return int(
                resultado.group(1)
            )

    return np.nan


df["Banos"] = (
    df["texto_limpio"]
    .apply(extraer_banos)
)


# ============================================================
# 14. EXTRAER METROS CUADRADOS
# ============================================================

def extraer_metros(texto):

    patrones = [

        r"(\d+(?:[.,]\d+)?)\s*m²",
        r"(\d+(?:[.,]\d+)?)\s*m2",
        r"(\d+(?:[.,]\d+)?)\s*metros cuadrados"

    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if resultado:

            valor = (
                resultado.group(1)
                .replace(",", ".")
            )

            return float(valor)

    return np.nan


df["Metros_Cuadrados"] = (
    df["texto_limpio"]
    .apply(extraer_metros)
)


# ============================================================
# 15. LIMPIAR PRECIOS
# ============================================================

def limpiar_precio(valor):

    if pd.isna(valor):
        return np.nan

    texto = str(valor)

    texto = (
        texto
        .replace("$", "")
        .replace(",", "")
        .replace(" ", "")
    )

    try:

        return float(texto)

    except:

        return np.nan


df["precio_renta"] = (
    df["precio_renta"]
    .apply(limpiar_precio)
)


df["precio_venta"] = (
    df["precio_venta"]
    .apply(limpiar_precio)
)


# ============================================================
# 16. MARCAR REGISTROS SIN TEXTO
# ============================================================

df["Texto_Valido"] = (
    df["texto_limpio"]
    .str.len()
    > 10
)


# ============================================================
# 17. NO ELIMINAMOS DUPLICADOS TODAVIA
# ============================================================
#
# Los marcamos para revisarlos posteriormente.
#
# Esto es importante porque dos publicaciones
# pueden tener textos iguales pero representar
# propiedades diferentes.
# ============================================================

df["Posible_Duplicado"] = (
    df.duplicated(
        subset=["texto_limpio"],
        keep=False
    )
)


# ============================================================
# 18. RESUMEN
# ============================================================

print("\n")
print("==========================================")
print("RESUMEN DE LIMPIEZA")
print("==========================================")

print(
    "\nRegistros:",
    len(df)
)


print("\nClasificación original:")

print(
    df["Tipo_Mensaje"]
    .value_counts(
        dropna=False
    )
)


print("\nClasificación generada:")

print(
    df["Tipo_Mensaje_Final"]
    .value_counts(
        dropna=False
    )
)


print("\nTipo de propiedad:")

print(
    df["Tipo_Propiedad"]
    .value_counts(
        dropna=False
    ).head(15)
)


print("\nCaracterísticas encontradas:")

print(
    "Habitaciones:",
    df["Habitaciones"].notna().sum()
)

print(
    "Baños:",
    df["Banos"].notna().sum()
)

print(
    "Metros cuadrados:",
    df["Metros_Cuadrados"].notna().sum()
)

print(
    "Precio renta:",
    df["precio_renta"].notna().sum()
)

print(
    "Precio venta:",
    df["precio_venta"].notna().sum()
)

print(
    "Posibles duplicados:",
    df["Posible_Duplicado"].sum()
)


# ============================================================
# 19. MOSTRAR EJEMPLOS DE CADA CLASIFICACION
# ============================================================

print("\n")
print("==========================================")
print("EJEMPLOS DE CLASIFICACION")
print("==========================================")


categorias = [
    "OFERTA_RENTA",
    "OFERTA_VENTA",
    "SOLICITUD_RENTA",
    "SOLICITUD_VENTA",
    "NO_CLASIFICADO"
]


for categoria in categorias:

    ejemplo = df[
        df["Tipo_Mensaje_Final"] == categoria
    ]

    if len(ejemplo) > 0:

        print("\n---", categoria, "---")

        print(
            ejemplo[
                [
                    "Tipo_Mensaje",
                    "Tipo_Mensaje_Final",
                    "Tipo_Propiedad",
                    "precio_renta",
                    "precio_venta"
                ]
            ].head(3).to_string(index=False)
        )


# ============================================================
# 20. SELECCIONAR DONDE GUARDAR
# ============================================================

archivo_salida = filedialog.asksaveasfilename(

    title="AIVRI - ¿Dónde quieres guardar la base limpia?",

    defaultextension=".xlsx",

    initialfile="inmobiliaria_limpia.xlsx",

    filetypes=[
        ("Archivo Excel", "*.xlsx"),
        ("Archivo CSV", "*.csv")
    ]
)


# ============================================================
# 21. CANCELAR GUARDADO
# ============================================================

if not archivo_salida:

    messagebox.showwarning(
        "AIVRI",
        "El proceso terminó, pero no seleccionaste dónde guardar."
    )

    root.destroy()
    exit()


# ============================================================
# 22. GUARDAR
# ============================================================

try:

    if archivo_salida.lower().endswith(".csv"):

        df.to_csv(
            archivo_salida,
            index=False,
            encoding="utf-8-sig"
        )

    else:

        df.to_excel(
            archivo_salida,
            index=False
        )

except Exception as error:

    messagebox.showerror(
        "Error al guardar",
        f"No se pudo guardar el archivo:\n\n{error}"
    )

    root.destroy()
    exit()


# ============================================================
# 23. FINAL
# ============================================================

print("\n")
print("==========================================")
print("AIVRI - PROCESO TERMINADO")
print("==========================================")

print(
    "\nArchivo guardado en:"
)

print(
    archivo_salida
)


messagebox.showinfo(
    "AIVRI - Listo",
    "La base inmobiliaria fue limpiada y guardada correctamente."
)


root.destroy()