"""Módulo 05: búsqueda de publicaciones similares con TF-IDF y coseno."""

import matplotlib.pyplot as plt
import pandas as pd
from importlib import import_module
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

datos_comunes = import_module("02_Datos_Comunes")
CARPETA_GRAFICAS = datos_comunes.CARPETA_GRAFICAS
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
cargar_dataset = datos_comunes.cargar_dataset
filtrar_por_intencion = datos_comunes.filtrar_por_intencion


# 1. PETICIÓN QUE PUEDE MODIFICARSE PARA HACER OTRA BÚSQUEDA
peticion_usuario = ["busco departamento de dos recámaras en renta"]
ubicacion_usuario = ""

# 2. VECTORIZAR BASE Y PETICIÓN
df = cargar_dataset().copy()
df = df[df["texto_limpio"].notna()].copy()
df = df.reset_index(drop=True)
df["texto_busqueda"] = df["texto_limpio"].fillna("").astype(str)
if "direccion_validada" in df.columns:
    df["texto_busqueda"] = df["texto_busqueda"] + " " + df["direccion_validada"].fillna("").astype(str)
documentos = df["texto_busqueda"]
stop_words_espanol = ["de", "la", "el", "en", "y", "a", "un", "con", "para", "las", "los"]
vectorizador = TfidfVectorizer(ngram_range=(1, 2), stop_words=stop_words_espanol)
matriz_publicaciones = vectorizador.fit_transform(documentos)
vector_usuario = vectorizador.transform(peticion_usuario)

# 3. FILTRAR POR INTENCIÓN EXPLÍCITA Y CALCULAR SIMILITUD
candidatos, filtros_aplicados = filtrar_por_intencion(df, peticion_usuario[0], ubicacion_usuario)
consulta = [peticion_usuario[0] + " " + ubicacion_usuario]
vector_usuario = vectorizador.transform(consulta)
puntajes = cosine_similarity(vector_usuario, matriz_publicaciones[candidatos.index])[0]
candidatos = candidatos.copy()
candidatos["similitud_coseno"] = puntajes
columnas_mostrar = ["id_post", "texto_limpio", "operacion_validada", "tipo_propiedad_validado", "similitud_coseno"]
columnas_mostrar = [c for c in columnas_mostrar if c in candidatos.columns]
top_similares = candidatos.sort_values("similitud_coseno", ascending=False).head(10)[columnas_mostrar]

print("=" * 80)
print("MÓDULO 05 - SIMILITUD DE COSENO")
print("=" * 80)
print(f"Petición: {peticion_usuario[0]}")
print(f"Filtros aplicados: {filtros_aplicados}")
print("\nPublicaciones más similares:")
print(top_similares.to_string(index=False))

# 4. GUARDAR RESULTADOS Y GRÁFICA
CARPETA_METRICAS.mkdir(parents=True, exist_ok=True)
CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
top_similares.to_csv(CARPETA_METRICAS / "05_similitud_coseno.csv", index=False)

plt.figure(figsize=(10, 6))
etiquetas = top_similares["id_post"].astype(str) if "id_post" in top_similares else top_similares.index.astype(str)
plt.barh(etiquetas[::-1], top_similares["similitud_coseno"].iloc[::-1])
plt.xlabel("Puntaje de similitud coseno")
plt.title("10 publicaciones más similares a la petición")
plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "05_similitud_coseno.png", dpi=150)
plt.show()
