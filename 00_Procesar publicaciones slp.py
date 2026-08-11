import re
import os
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog


def seleccionar_archivo_popup():
    """Abre la ventana emergente de Windows para elegir el archivo .txt"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    print("🗔 Selecciona tu archivo .txt de Facebook...")
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona el archivo PUBLICACIONES_AISLADAS_SLP.txt",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    return ruta_archivo


def limpiar_y_unificar_texto(elementos_soup):
    texto_acumulado = []
    for el in elementos_soup:
        txt = el.get_text(separator=" ", strip=True)
        if txt:
            texto_acumulado.append(txt)
    resultado = " ".join(texto_acumulado).replace('\n', ' ').replace('\r', ' ').strip()
    return re.sub(r'\s+', ' ', resultado)


def extraer_bloques_con_id(contenido_completo):
    """Divide el archivo en (id_post, html_bloque) sin perder el ID."""
    partes = re.split(r'\[ID_POST_(\d+)\]', contenido_completo)
    # partes[0] = basura antes del primer marcador (se ignora)
    bloques = []
    i = 1
    while i < len(partes) - 1:
        id_post = partes[i]
        html_bloque = partes[i + 1].strip()
        if html_bloque:
            bloques.append((id_post, html_bloque))
        i += 2
    return bloques


def extraer_precio_direccion_marketplace(soup):
    """
    Busca la tarjeta nativa de Marketplace (<a href="/commerce/listing/...">).
    No depende de nombres de clase (Facebook los cambia entre sesiones de scraping):
    usa únicamente el href y el ORDEN de los fragmentos de texto dentro del enlace.
    Devuelve (precio_float, direccion_str, cuerpo_str) o (None, None, "") si no existe.
    """
    a_listing = soup.find("a", href=re.compile(r'/commerce/listing/'))
    if not a_listing:
        return None, None, ""

    # Quitar el botón "Enviar mensaje" para que no contamine el texto
    boton = a_listing.find(attrs={"aria-label": "Enviar mensaje"})
    if boton:
        boton.decompose()

    # stripped_strings ya filtra nodos de solo espacios/():&nbsp;, así que
    # nos da limpio: ["$6,000", "·", "Soledad de Graciano Sánchez, SLP",
    #                 "1 habitación · 1 baño · Casa adosada o townhouse"]
    piezas = [p for p in a_listing.stripped_strings]
    if not piezas:
        return None, None, ""

    precio = None
    direccion = None
    idx_precio = None

    for i, p in enumerate(piezas):
        if '$' in p:
            idx_precio = i
            break

    resto = piezas
    precio_txt = None
    if idx_precio is not None:
        precio_txt = piezas[idx_precio]
        m = re.search(r'\$\s*([\d,]+(?:[.,]\s?\d{3})*(?:\.\d{2})?)', precio_txt)
        if m:
            try:
                precio = float(re.sub(r'[,\s]', '', m.group(1)))
            except ValueError:
                precio = None

        j = idx_precio + 1
        # saltar un posible separador suelto "·"
        if j < len(piezas) and piezas[j].strip(' ·') == '':
            j += 1
        if j < len(piezas):
            direccion = piezas[j]
            j += 1
        resto = piezas[j:]

    cuerpo_partes = []
    if precio_txt and direccion:
        cuerpo_partes.append(f"{precio_txt} · {direccion}")
    elif precio_txt:
        cuerpo_partes.append(precio_txt)
    cuerpo_partes.extend(resto)
    cuerpo = " | ".join(c for c in cuerpo_partes if c)

    return precio, direccion, cuerpo


def extraer_precio_detalle_metabloque(soup):
    """
    Fallback cuando NO hay ancla nativa /commerce/listing/. Facebook también
    reutiliza un bloque de vista previa de enlace con atributos ESTABLES
    (no dependen de hashes de CSS): data-ad-rendering-role="description"
    trae el precio, data-ad-rendering-role="title" trae recámaras/baños/tipo.
    No trae dirección (solo el dominio del link), así que direccion queda None.
    """
    precio = None
    detalle = None

    nodo_desc = soup.find(attrs={"data-ad-rendering-role": "description"})
    if nodo_desc:
        txt = nodo_desc.get_text(" ", strip=True)
        m = re.search(r'\$\s*([\d,]+(?:[.,]\s?\d{3})*(?:\.\d{2})?)', txt)
        if m:
            try:
                precio = float(re.sub(r'[,\s]', '', m.group(1)))
            except ValueError:
                precio = None

    nodo_titulo = soup.find(attrs={"data-ad-rendering-role": "title"})
    if nodo_titulo:
        detalle = nodo_titulo.get_text(" ", strip=True)

    cuerpo_partes = []
    if nodo_desc:
        cuerpo_partes.append(nodo_desc.get_text(" ", strip=True))
    if detalle:
        cuerpo_partes.append(detalle)
    cuerpo = " | ".join(c for c in cuerpo_partes if c)

    return precio, None, cuerpo


def clasificar_operacion(texto_minus):
    """Devuelve set con 'renta' y/o 'venta' según palabras clave presentes."""
    ops = set()
    if any(x in texto_minus for x in ["renta", "alquiler", "por mes", " mes ", "mensual"]):
        ops.add("renta")
    if any(x in texto_minus for x in ["venta", "vendo", "vende", "se vende"]):
        ops.add("venta")
    return ops


def procesar_lote_crudo_txt(ruta_txt_entrada, ruta_csv_salida):
    with open(ruta_txt_entrada, "r", encoding="utf-8") as f:
        contenido_completo = f.read()

    bloques = extraer_bloques_con_id(contenido_completo)
    print(f"📦 Se detectaron {len(bloques)} bloques crudos en el archivo.")

    registro_final = []
    errores = 0

    for id_post, html_post in bloques:
        if len(html_post) < 100:
            continue
        try:
            soup = BeautifulSoup(html_post, "html.parser")

            # ---- Autor ----
            autor = "Autor Oculto"
            svg_perfil = soup.find("svg", attrs={"role": "img", "aria-label": True})
            if svg_perfil:
                autor = svg_perfil["aria-label"].strip()
            else:
                h2_nombre = soup.find("h2")
                if h2_nombre:
                    autor = h2_nombre.get_text().strip()

            # ---- Texto de la historia (para encabezado) ----
            bloque_historia = soup.find_all("div", {"data-ad-comet-preview": "message"})
            texto_historia = limpiar_y_unificar_texto(bloque_historia)
            if not texto_historia:
                bloques_textarea = soup.find_all("div", {"data-mcomponent": "TextArea"})
                texto_historia = limpiar_y_unificar_texto(bloques_textarea)

            encabezado_final = f"{autor} | {texto_historia}".strip(" |")

            # ---- Precio / dirección / cuerpo desde tarjeta de Marketplace ----
            precio_mkt, direccion_mkt, cuerpo_final = extraer_precio_direccion_marketplace(soup)

            # Si no hay ancla nativa de Marketplace, usar el bloque de vista
            # previa de enlace (atributos data-ad-rendering-role, estables)
            if precio_mkt is None and not cuerpo_final:
                precio_mkt, direccion_mkt, cuerpo_final = extraer_precio_detalle_metabloque(soup)

            texto_completo = f"{texto_historia} {cuerpo_final}"
            texto_minus = texto_completo.lower()

            # ---- Precio fallback (post normal sin tarjeta de marketplace) ----
            precio_detectado = precio_mkt
            if precio_detectado is None:
                precios_encontrados = re.findall(r'\$\s*(\d{1,3}(?:[,\s]\s?\d{3})*(?:\.\d{2})?)', texto_completo)
                for p_str in precios_encontrados:
                    try:
                        valor = float(re.sub(r'[,\s]', '', p_str))
                        if valor >= 500:
                            precio_detectado = valor
                            break
                    except ValueError:
                        continue

            # ---- Clasificar renta / venta ----
            precio_renta = None
            precio_venta = None
            ops = clasificar_operacion(texto_minus)

            if precio_detectado is not None:
                if "renta" in ops:
                    precio_renta = precio_detectado
                if "venta" in ops:
                    precio_venta = precio_detectado
                if not ops:
                    # Sin palabra clave: heurística por magnitud
                    if precio_detectado >= 250000:
                        precio_venta = precio_detectado
                    else:
                        precio_renta = precio_detectado

            # ---- Dirección (fallback a zonas conocidas si no hubo tarjeta) ----
            direccion_final = direccion_mkt
            if not direccion_final:
                zonas_slp = ["loma alta", "lomas", "tequis", "avanzada", "pozos", "tangamanga",
                             "monterra", "saucito", "agua azul", "forestal", "cactus", "soledad"]
                for zona in zonas_slp:
                    if zona in texto_minus:
                        direccion_final = zona.title()
                        break
            if not direccion_final:
                direccion_final = "No especificada"

            registro_final.append({
                "id_post": id_post,
                "fecha_registro": datetime.now().strftime("%Y-%m-%d"),
                "precio_renta": precio_renta,
                "precio_venta": precio_venta,
                "direccion": direccion_final,
                "encabezado": encabezado_final,
                "cuerpo": cuerpo_final,
            })

        except Exception as e:
            errores += 1
            print(f"⚠️ Error en bloque ID_POST_{id_post}: {e}")
            continue

    if registro_final:
        df_final = pd.DataFrame(registro_final)
        columnas_ordenadas = ['id_post', 'fecha_registro', 'precio_renta', 'precio_venta',
                               'direccion', 'encabezado', 'cuerpo']
        df_final = df_final.reindex(columns=columnas_ordenadas)
        df_final.to_csv(ruta_csv_salida, index=False, encoding='utf-8-sig')
        print(f"\n✅ Procesamiento completado. {len(df_final)} publicaciones, {errores} errores.")
        print(f"Matriz guardada en: '{ruta_csv_salida}'")
        return df_final
    else:
        print("❌ No se pudieron extraer registros del archivo de texto seleccionado.")
        return None


if __name__ == "__main__":
    archivo_seleccionado = seleccionar_archivo_popup()
    if not archivo_seleccionado:
        print("❌ No seleccionaste ningún archivo. Proceso cancelado.")
    else:
        procesar_lote_crudo_txt(archivo_seleccionado, "inventario_slp_final.csv")