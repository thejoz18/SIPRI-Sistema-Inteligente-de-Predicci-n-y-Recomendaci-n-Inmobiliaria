import re
import pandas as pd
import tkinter as tk
from tkinter import filedialog


def seleccionar_archivo():
    """Abre una ventana emergente para que el usuario seleccione el archivo de WhatsApp."""
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal de Tkinter

    print("📂 Abriendo ventana para seleccionar archivo...")
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona el archivo de chat de WhatsApp",
        filetypes=[("Archivos de texto (*.txt)", "*.txt"), ("Todos los archivos", "*.*")]
    )
    return ruta_archivo


def parsear_chat_whatsapp(ruta_archivo):
    """
    Lee un archivo de exportación de WhatsApp, separa cada mensaje,
    agrega un id_coment y separa los precios de renta y venta.
    """
    print(f"📖 Leyendo y procesando: {ruta_archivo}...")

    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Patrón estándar de WhatsApp para separar fecha/hora y remitente de los mensajes
    patron_mensaje = re.compile(
        r'(\d{2}/\d{2}/\d{2},?\s\d{1,2}:\d{2}\s?[ap]?\.?\s?m?\.?)\s?-\s([^:]+):\s(.*?)(?=\d{2}/\d{2}/\d{2},?\s\d{1,2}:\d{2}\s?[ap]?\.?\s?m?\.?\s?-\s|$)',
        re.DOTALL
    )

    coincidencias = patron_mensaje.findall(contenido)
    print(f"💬 Total de mensajes detectados en bruto: {len(coincidencias)}")

    datos_estructurados = []
    contador_id = 1  # Inicializador para el identificador único de cada comentario

    for fecha_str, remitente, texto in coincidencias:
        texto_limpio = texto.strip()

        # Omitir mensajes vacíos o multimedia genérica
        if not texto_limpio or "<Multimedia omitido>" in texto_limpio:
            continue

        texto_lower = texto_limpio.lower()

        # 1. Clasificar Tipo de Transacción
        if any(w in texto_lower for w in ["busco", "solicito", "requiero", "cliente busca"]):
            tipo_mensaje = "SOLICITUD"
        elif "renta" in texto_lower or "rentas" in texto_lower:
            tipo_mensaje = "OFERTA_RENTA"
        elif "venta" in texto_lower or "vende" in texto_lower or "se vende" in texto_lower:
            tipo_mensaje = "OFERTA_VENTA"
        else:
            tipo_mensaje = "OTRO"

        # 2. Clasificar Tipo de Propiedad
        if any(w in texto_lower for w in ["terreno", "lote", "ejido", "tpv"]):
            tipo_propiedad = "Terreno"
        elif any(w in texto_lower for w in ["departamento", "depa"]):
            tipo_propiedad = "Departamento"
        elif any(w in texto_lower for w in ["bodega", "nave", "local", "oficina", "comercial"]):
            tipo_propiedad = "Comercial/Industrial"
        elif any(w in texto_lower for w in ["casa", "residencial", "coto", "townhouse"]):
            tipo_propiedad = "Casa"
        else:
            tipo_propiedad = "No especificado"

        # 3. Extracción de Precios y Separación Renta / Venta
        match_precio = re.search(r'\$\s*([\d,\.]+)', texto_limpio)
        precio_encontrado = match_precio.group(1) if match_precio else "No especificado"

        precio_renta = "No especificado"
        precio_venta = "No especificado"

        if precio_encontrado != "No especificado":
            if "renta" in tipo_mensaje.lower() or "renta" in texto_lower:
                precio_renta = precio_encontrado
            elif "venta" in tipo_mensaje.lower() or "venta" in texto_lower or "vende" in texto_lower:
                precio_venta = precio_encontrado
            else:
                # Heurística: si no se especifica explícitamente, se separa por monto
                try:
                    precio_limpio_num = float(precio_encontrado.replace(",", ""))
                    if precio_limpio_num < 50000:
                        precio_renta = precio_encontrado
                    else:
                        precio_venta = precio_encontrado
                except ValueError:
                    pass

        # 4. Extracción aproximada de Zona
        match_zona = re.search(r'(?:📍|zona[:\s]*|colonia[:\s]*)([^\n\r,]+)', texto_limpio, re.IGNORECASE)
        zona_extraida = match_zona.group(1).strip() if match_zona else "No especificada"

        datos_estructurados.append({
            "id_coment": contador_id,
            "Fecha": fecha_str,
            "Tipo_Mensaje": tipo_mensaje,
            "Tipo_Propiedad": tipo_propiedad,
            "Precio de Renta": precio_renta,
            "Precio de Venta": precio_venta,
            "Zona_Detectada": zona_extraida,
            "Texto_Original": texto_limpio.replace("\n", " ")
        })

        contador_id += 1

    df = pd.DataFrame(datos_estructurados)
    return df


if __name__ == "__main__":
    archivo_entrada = seleccionar_archivo()

    if not archivo_entrada:
        print("❌ Operación cancelada. No se seleccionó ningún archivo.")
    else:
        try:
            df_resultado = parsear_chat_whatsapp(archivo_entrada)

            archivo_salida = "inventario_whatsapp_procesado.csv"
            df_resultado.to_csv(archivo_salida, index=False, encoding="utf-8-sig")

            print(f"\n✅ ¡Proceso exitoso!")
            print(f"📊 Se estructuraron {len(df_resultado)} registros útiles con ID.")
            print(f"💾 Archivo guardado como: {archivo_salida}")
            print("\nPrimeras filas del resultado:")
            print(df_resultado.head(3))

        except Exception as e:
            print(f"❌ Ocurrió un error al procesar el archivo: {e}")