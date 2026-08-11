# ============================================================
# AIVRI
# MODULO 1 - VERSIÓN FINAL CON UMBRAL DE 100 CARACTERES
# Y DECISIÓN HUMANA SIMPLIFICADA (SI / NO)
# ============================================================

import pandas as pd
import numpy as np
import re
import os

import tkinter as tk
from tkinter import filedialog, messagebox


# ============================================================
# 1. VENTANA
# ============================================================

root = tk.Tk()
root.withdraw()


# ============================================================
# 2. SELECCIONAR ARCHIVO
# ============================================================

archivo_entrada = filedialog.askopenfilename(
    title="AIVRI - Selecciona la base inmobiliaria",
    filetypes=[
        ("Excel", "*.xlsx *.xls"),
        ("CSV", "*.csv"),
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


# ============================================================
# 3. CARGAR
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
        "AIVRI",
        f"No se pudo cargar el archivo:\n\n{error}"
    )

    root.destroy()
    exit()


print("\n==========================================")
print("AIVRI - BASE CARGADA")
print("==========================================")

print("Registros:", len(df))
print("Columnas:", len(df.columns))


# ============================================================
# 4. ASEGURAR COLUMNAS
# ============================================================

columnas = [
    "Texto_Original",
    "Tipo_Mensaje",
    "Tipo_Propiedad",
    "precio_renta",
    "precio_venta",
    "direccion",
    "encabezado",
    "cuerpo"
]

for columna in columnas:

    if columna not in df.columns:

        df[columna] = ""


# ============================================================
# 5. ID DEL REGISTRO
# ============================================================

df.insert(
    0,
    "ID_Registro",
    range(1, len(df) + 1)
)


# ============================================================
# 6. TEXTO COMPLETO
# ============================================================

for columna in [
    "Texto_Original",
    "encabezado",
    "cuerpo",
    "direccion"
]:

    df[columna] = (
        df[columna]
        .fillna("")
        .astype(str)
    )


df["texto_completo"] = (
    df["Texto_Original"]
    + " "
    + df["encabezado"]
    + " "
    + df["cuerpo"]
    + " "
    + df["direccion"]
)


# ============================================================
# 7. TEXTO LIMPIO (FILTRANDO EMOJIS Y SÍMBOLOS EXCEPTO $)
# ============================================================

def limpiar_texto(texto):
    texto = texto.lower()
    # Permitir letras (incluyendo acentos y ñ), números, espacios y el signo $
    texto = re.sub(r"[^a-záéíóúñ0-9\s\$]", " ", texto)
    # Reducir espacios múltiples
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


df["texto_limpio"] = (
    df["texto_completo"]
    .apply(limpiar_texto)
)


# ============================================================
# 8. CONTADOR DE CARACTERES (TEXTO LIMPIO)
# ============================================================

df["longitud_texto_limpio"] = (
    df["texto_limpio"]
    .str.len()
)


# ============================================================
# 9. FUNCION NUMERICA
# ============================================================

def numero(valor):

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


# ============================================================
# 10. HABITACIONES
# ============================================================

def extraer_habitaciones(texto):

    patrones = [
        r"(\d+)\s*habitaciones?",
        r"(\d+)\s*rec[aá]maras?",
        r"(\d+)\s*dormitorios?",
        r"(\d+)\s*rec\."
    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if resultado:
            return int(resultado.group(1))

    return np.nan


df["habitaciones_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_habitaciones)
)


# ============================================================
# 11. BAÑOS
# ============================================================

def extraer_banos(texto):

    patrones = [
        r"(\d+(?:\.\d+)?)\s*baños?",
        r"(\d+(?:\.\d+)?)\s*wc"
    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if resultado:
            return float(
                resultado.group(1)
            )

    return np.nan


df["banos_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_banos)
)


# ============================================================
# 12. METROS CUADRADOS
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


df["metros_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_metros)
)


# ============================================================
# 13. ESTACIONAMIENTOS
# ============================================================

def extraer_estacionamientos(texto):

    patrones = [
        r"(\d+)\s*estacionamientos?",
        r"(\d+)\s*cocheras?",
        r"cochera\s*para\s*(\d+)",
        r"garage\s*para\s*(\d+)"
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


df["estacionamientos_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_estacionamientos)
)


# ============================================================
# 14. TIPO DE PROPIEDAD
# ============================================================

def extraer_tipo_propiedad(texto):
    if "casa" in texto:
        return "CASA"
    elif "departamento" in texto or "depa" in texto:
        return "DEPARTAMENTO"
    elif "terreno" in texto or "lote" in texto:
        return "TERRENO"
    elif "local" in texto or "comercial" in texto:
        return "LOCAL"
    elif "cuarto" in texto or "habitacion" in texto:
        return "CUARTO"
    elif "bodega" in texto or "nave" in texto:
        return "BODEGA"
    return "OTRO"

df["tipo_propiedad_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_tipo_propiedad)
)


# ============================================================
# 15. UBICACIÓN PREDICHA
# ============================================================

def extraer_ubicacion(texto):
    patrones = [
        r"colonia\s+([a-z0-9\s]+?)(?=\s+(?:cerca|precio|renta|venta|habitaciones|recamaras|baños|m2|metros)|\Z)",
        r"col\.\s+([a-z0-9\s]+?)(?=\s+(?:cerca|precio|renta|venta|habitaciones|recamaras|baños|m2|metros)|\Z)",
        r"fraccionamiento\s+([a-z0-9\s]+?)(?=\s+(?:cerca|precio|renta|venta|habitaciones|recamaras|baños|m2|metros)|\Z)",
        r"fracc\.\s+([a-z0-9\s]+?)(?=\s+(?:cerca|precio|renta|venta|habitaciones|recamaras|baños|m2|metros)|\Z)",
        r"zona\s+([a-z0-9\s]+?)(?=\s+(?:cerca|precio|renta|venta|habitaciones|recamaras|baños|m2|metros)|\Z)"
    ]

    for patron in patrones:
        resultado = re.search(patron, texto, re.IGNORECASE)
        if resultado:
            ubicacion_encontrada = resultado.group(1).strip()
            if len(ubicacion_encontrada) > 2:
                return ubicacion_encontrada.title()

    if df["direccion"].any() and str(df["direccion"].iloc[0]).strip() != "":
        return str(df["direccion"].iloc[0])

    return np.nan

df["ubicacion_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_ubicacion)
)


# ============================================================
# 16. PRECIO DEL TEXTO
# ============================================================

def extraer_precio(texto):

    resultado = re.search(
        r"\$?\s*(\d+(?:[.,]\d+)?)\s*millones?",
        texto,
        re.IGNORECASE
    )
    if resultado:
        numero_texto = resultado.group(1).replace(",", ".")
        return float(numero_texto) * 1_000_000

    resultado = re.search(
        r"\$?\s*(\d+(?:[.,]\d+)?)\s*mil\b",
        texto,
        re.IGNORECASE
    )
    if resultado:
        numero_texto = resultado.group(1).replace(",", ".")
        return float(numero_texto) * 1_000

    resultados = re.findall(
        r"\$\s*([\d,]+(?:\.\d+)?)",
        texto
    )

    valores = []
    for valor in resultados:
        try:
            val_num = float(valor.replace(",", ""))
            if val_num < 1000 and ("mil" in texto or "k" in texto):
                val_num *= 1000
            valores.append(val_num)
        except:
            pass

    if valores:
        return max(valores)

    return np.nan


df["precio_predicho"] = (
    df["texto_limpio"]
    .apply(extraer_precio)
)


# ============================================================
# 17. PRECIOS ORIGINALES NORMALIZADOS
# ============================================================

df["precio_renta_original"] = (
    df["precio_renta"]
    .apply(numero)
)

df["precio_venta_original"] = (
    df["precio_venta"]
    .apply(numero)
)


# ============================================================
# 18. OPERACION PREDICHA
# ============================================================

def detectar_operacion(texto):

    renta = any(
        palabra in texto
        for palabra in [
            "renta",
            "rentar",
            "rentando",
            "alquiler",
            "en renta",
            "se renta"
        ]
    )

    venta = any(
        palabra in texto
        for palabra in [
            "venta",
            "vender",
            "vende",
            "vendemos",
            "en venta",
            "se vende"
        ]
    )

    if renta and not venta:
        return "RENTA"

    if venta and not renta:
        return "VENTA"

    if renta and venta:
        return "AMBAS"

    return "NO_DEFINIDO"


df["operacion_predicha"] = (
    df["texto_limpio"]
    .apply(detectar_operacion)
)


# ============================================================
# 19. OFERTA / SOLICITUD
# ============================================================

def detectar_naturaleza(texto):

    solicitud = any(
        palabra in texto
        for palabra in [
            "busco",
            "buscamos",
            "buscando",
            "solicito",
            "solicitamos",
            "necesito",
            "necesitamos",
            "quiero",
            "queremos",
            "requiero"
        ]
    )

    oferta = any(
        palabra in texto
        for palabra in [
            "vendo",
            "vendemos",
            "se vende",
            "rento",
            "rentamos",
            "se renta",
            "en venta",
            "en renta"
        ]
    )

    if solicitud and not oferta:
        return "SOLICITUD"

    if oferta and not solicitud:
        return "OFERTA"

    if solicitud and oferta:
        return "AMBIGUO"

    return "NO_DEFINIDO"


df["naturaleza_predicha"] = (
    df["texto_limpio"]
    .apply(detectar_naturaleza)
)


# ============================================================
# 20. AMENIDADES
# ============================================================

amenidades = {

    "alberca": [
        "alberca",
        "piscina"
    ],

    "vigilancia": [
        "vigilancia",
        "seguridad privada",
        "seguridad 24",
        "caseta de vigilancia"
    ],

    "jardin": [
        "jardín",
        "jardin"
    ],

    "terraza": [
        "terraza"
    ],

    "balcon": [
        "balcón",
        "balcon"
    ],

    "amueblado": [
        "amueblado",
        "amueblada"
    ],

    "aire_acondicionado": [
        "aire acondicionado",
        "minisplit",
        "mini split"
    ],

    "cocina_integral": [
        "cocina integral"
    ],

    "gimnasio": [
        "gimnasio"
    ],

    "elevador": [
        "elevador",
        "ascensor"
    ],

    "bodega": [
        "bodega"
    ],

    "roof_garden": [
        "roof garden",
        "roofgarden"
    ],

    "cuarto_servicio": [
        "cuarto de servicio"
    ],

    "estudio": [
        "estudio"
    ]
}


for nombre, palabras in amenidades.items():

    def buscar_amenidad(
        texto,
        palabras=palabras
    ):

        for palabra in palabras:

            if palabra in texto:
                return 1

        return 0


    df[f"{nombre}_predicho"] = (
        df["texto_limpio"]
        .apply(buscar_amenidad)
    )


# ============================================================
# 21. TEXTO VALIDO (MÍNIMO 100 CARACTERES)
# ============================================================

df["texto_valido_predicho"] = (
    df["longitud_texto_limpio"]
    >= 100
)


# ============================================================
# 22. DUPLICADOS
# ============================================================

df["posible_duplicado"] = (
    df.duplicated(
        subset=["texto_limpio"],
        keep=False
    )
)


# ============================================================
# 23. CONFIANZA
# ============================================================

def confianza(row):

    encontrados = 0

    if not pd.isna(
        row["habitaciones_predicho"]
    ):
        encontrados += 1

    if not pd.isna(
        row["banos_predicho"]
    ):
        encontrados += 1

    if not pd.isna(
        row["metros_predicho"]
    ):
        encontrados += 1

    if not pd.isna(
        row["precio_predicho"]
    ):
        encontrados += 1

    if not pd.isna(
        row["ubicacion_predicho"]
    ):
        encontrados += 1

    if encontrados >= 4:
        return "ALTA"

    if encontrados >= 2:
        return "MEDIA"

    return "BAJA"


df["confianza_prediccion"] = df.apply(
    confianza,
    axis=1
)


# ============================================================
# 24. COLUMNAS PARA VALIDACION HUMANA (REORGANIZADAS CON CONTADOR)
# ============================================================

df["decision_humana"] = ""
df["longitud_texto_limpio"] = df["longitud_texto_limpio"]  # Ya creada en paso 8, se mantiene visible para revisión

df["operacion_validada"] = ""
df["naturaleza_validada"] = ""
df["tipo_propiedad_validado"] = ""
df["direccion_validada"] = ""
df["precio_renta_validado"] = np.nan
df["precio_venta_validado"] = np.nan
df["metros_validado"] = np.nan
df["habitaciones_validado"] = np.nan
df["banos_validado"] = np.nan
df["estacionamientos_validado"] = np.nan


# ============================================================
# 25. VALIDACION DE AMENIDADES
# ============================================================

for nombre in amenidades:
    df[f"{nombre}_validado"] = ""


# ============================================================
# 26. OBSERVACIONES
# ============================================================

df["observaciones_humanas"] = ""


# ============================================================
# 27. RESUMEN
# ============================================================

resumen = pd.DataFrame({

    "Indicador": [
        "Registros originales",
        "Textos considerados válidos (>= 100 carac.)",
        "Textos para revisar (< 100 carac.)",
        "Posibles duplicados",
        "Precios encontrados",
        "Metros encontrados",
        "Habitaciones encontradas",
        "Baños encontrados",
        "Estacionamientos encontrados",
        "Ubicaciones encontradas"
    ],

    "Cantidad": [
        len(df),
        df["texto_valido_predicho"].sum(),
        (~df["texto_valido_predicho"]).sum(),
        df["posible_duplicado"].sum(),
        df["precio_predicho"].notna().sum(),
        df["metros_predicho"].notna().sum(),
        df["habitaciones_predicho"].notna().sum(),
        df["banos_predicho"].notna().sum(),
        df["estacionamientos_predicho"].notna().sum(),
        df["ubicacion_predicho"].notna().sum()
    ]

})


# ============================================================
# 28. SELECCIONAR CARPETA
# ============================================================

carpeta = filedialog.askdirectory(
    title="AIVRI - Selecciona dónde guardar el archivo"
)

if not carpeta:
    messagebox.showwarning(
        "AIVRI",
        "No seleccionaste una carpeta."
    )
    root.destroy()
    exit()


# ============================================================
# 29. NOMBRE DEL ARCHIVO Y GUARDADO
# ============================================================

archivo_salida = os.path.join(
    carpeta,
    "inmobiliaria_procesada.xlsx"
)

try:

    with pd.ExcelWriter(
        archivo_salida,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="BASE_PROCESADA",
            index=False
        )

        revision = df[
            (~df["texto_valido_predicho"])
            | (df["posible_duplicado"])
            | (df["confianza_prediccion"] == "BAJA")
        ].copy()

        revision.to_excel(
            writer,
            sheet_name="REVISION",
            index=False
        )

        resumen.to_excel(
            writer,
            sheet_name="RESUMEN",
            index=False
        )

except Exception as error:

    messagebox.showerror(
        "AIVRI",
        f"No se pudo guardar el archivo:\n\n{error}"
    )

    root.destroy()
    exit()


# ============================================================
# 30. FINAL
# ============================================================

print("\n==========================================")
print("AIVRI - PROCESO TERMINADO")
print("==========================================")

print("\nArchivo creado:")
print(archivo_salida)

print("\nHojas:")
print("1. BASE_PROCESADA")
print("2. REVISION")
print("3. RESUMEN")

messagebox.showinfo(
    "AIVRI - Listo",
    "Proceso terminado correctamente.\n\n"
    "Se creó un único archivo Excel con:\n\n"
    "• BASE_PROCESADA\n"
    "• REVISION\n"
    "• RESUMEN\n\n"
    "Las columnas de validación humana están listas."
)

root.destroy()