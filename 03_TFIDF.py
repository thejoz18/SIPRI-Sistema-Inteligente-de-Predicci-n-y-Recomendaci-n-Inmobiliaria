"""Módulo 03: vectorización TF-IDF de publicaciones inmobiliarias."""

import pandas as pd
import joblib
from importlib import import_module
from sklearn.feature_extraction.text import TfidfVectorizer

datos_comunes = import_module("02_Datos_Comunes")
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
CARPETA_MODELOS = datos_comunes.CARPETA_MODELOS
cargar_dataset = datos_comunes.cargar_dataset


# 1. CARGAR DOCUMENTOS
df = cargar_dataset()
df["texto_busqueda"] = df["texto_limpio"].fillna("").astype(str)
if "direccion_validada" in df.columns:
    df["texto_busqueda"] = df["texto_busqueda"] + " " + df["direccion_validada"].fillna("").astype(str)
documentos = df["texto_busqueda"]
documentos = documentos[documentos.str.strip() != ""]

# 2. VECTORIZAR COMO EN EL NOTEBOOK DE CLASE
stop_words_espanol = ["de", "la", "el", "en", "y", "a", "un", "con", "para", "las", "los"]
vectorizador = TfidfVectorizer(ngram_range=(1, 2), stop_words=stop_words_espanol)
matriz_tfidf = vectorizador.fit_transform(documentos)

# 3. MOSTRAR RESULTADOS
print("=" * 80)
print("MÓDULO 03 - VECTORIZACIÓN TF-IDF")
print("=" * 80)
print(f"Número de documentos: {matriz_tfidf.shape[0]}")
print(f"Número de características: {matriz_tfidf.shape[1]}")
print(f"Tamaño de la matriz: {matriz_tfidf.shape}")

ejemplo_matriz = pd.DataFrame(
    matriz_tfidf[:5].toarray(), columns=vectorizador.get_feature_names_out()
).iloc[:, :20]
print("\nEjemplo de las primeras 5 filas y 20 características:")
print(ejemplo_matriz.round(3).to_string(index=False))

# 4. GUARDAR RESUMEN
CARPETA_METRICAS.mkdir(parents=True, exist_ok=True)
CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)
pd.DataFrame({
    "documentos": [matriz_tfidf.shape[0]],
    "caracteristicas": [matriz_tfidf.shape[1]],
    "ngramas": ["unigramas y bigramas"],
}).to_csv(CARPETA_METRICAS / "03_tfidf_resumen.csv", index=False)
joblib.dump(
    {"vectorizador": vectorizador, "matriz": matriz_tfidf, "publicaciones": df.loc[documentos.index].copy()},
    CARPETA_MODELOS / "03_tfidf_similitud.pkl",
)
print("\nResumen guardado en resultados/metricas/03_tfidf_resumen.csv")
print("Modelo TF-IDF guardado en resultados/modelos_guardados/03_tfidf_similitud.pkl")
