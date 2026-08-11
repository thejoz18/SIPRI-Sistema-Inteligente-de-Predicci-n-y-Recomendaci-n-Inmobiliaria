"""Módulo 04: clasificación de Tipo_Mensaje con KNN."""

import matplotlib.pyplot as plt
import joblib
import pandas as pd
from importlib import import_module
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

datos_comunes = import_module("02_Datos_Comunes")
CARPETA_GRAFICAS = datos_comunes.CARPETA_GRAFICAS
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
CARPETA_MODELOS = datos_comunes.CARPETA_MODELOS
cargar_dataset = datos_comunes.cargar_dataset


# 1. CARGAR Y PREPARAR DATOS
df = cargar_dataset()
datos = df[["texto_limpio", "Tipo_Mensaje"]].dropna().copy()
datos = datos[datos["texto_limpio"].astype(str).str.strip() != ""]
X = datos["texto_limpio"].astype(str)
y = datos["Tipo_Mensaje"]

print("=" * 80)
print("MÓDULO 04 - KNN PARA CLASIFICAR TIPO DE MENSAJE")
print("=" * 80)
print(f"Registros completos usados: {len(datos)}")
print("\nDistribución de clases:")
print(y.value_counts().to_string())

# 2. SEPARAR ENTRENAMIENTO Y PRUEBA
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=0
)

# 3. PROBAR DIFERENTES VALORES DE K
k_values = [1, 3, 5, 7, 9, 11, 13, 15, 25, 35]
resultados = []

for k in k_values:
    clf = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=["de", "la", "el", "en", "y", "a", "un", "con", "para", "las", "los"],
        )),
        ("knn", KNeighborsClassifier(n_neighbors=k)),
    ])
    clf.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))
    train_error = 1 - train_acc
    test_error = 1 - test_acc
    gap = train_error - test_error

    resultados.append([k, train_acc, test_acc, train_error, test_error, gap])

tabla_resultados = pd.DataFrame(
    resultados,
    columns=["K", "Accuracy_entrenamiento", "Accuracy_prueba", "Error_entrenamiento", "Error_prueba", "Gap"],
)
mejor_resultado = tabla_resultados.sort_values(
    ["Accuracy_prueba", "K"], ascending=[False, True]
).iloc[0]

print("\nCOMPARACIÓN DE K")
print(tabla_resultados.round(4).to_string(index=False))
print(f"\nMejor K según accuracy de prueba: {int(mejor_resultado['K'])}")

# 4. ENTRENAR Y GUARDAR EL MEJOR MODELO PARA LA INTERFAZ
mejor_k = int(mejor_resultado["K"])
modelo_final = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words=["de", "la", "el", "en", "y", "a", "un", "con", "para", "las", "los"],
    )),
    ("knn", KNeighborsClassifier(n_neighbors=mejor_k)),
])
modelo_final.fit(X_train, y_train)

# 5. GUARDAR TABLA, MODELO Y GRÁFICAS
CARPETA_METRICAS.mkdir(parents=True, exist_ok=True)
CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)
tabla_resultados.to_csv(CARPETA_METRICAS / "04_knn_resultados.csv", index=False)
joblib.dump(modelo_final, CARPETA_MODELOS / "04_knn_tipo_mensaje.pkl")
print("Modelo KNN guardado en resultados/modelos_guardados/04_knn_tipo_mensaje.pkl")

plt.figure(figsize=(10, 6))
plt.plot(k_values, tabla_resultados["Accuracy_entrenamiento"], "o-", label="Entrenamiento")
plt.plot(k_values, tabla_resultados["Accuracy_prueba"], "o-", label="Prueba")
plt.xlabel("Número de vecinos (K)")
plt.ylabel("Accuracy")
plt.title("Accuracy de KNN por valor de K")
plt.ylim(0, 1.05)
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "04_knn_accuracy.png", dpi=150)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(k_values, tabla_resultados["Error_entrenamiento"], "o--", label="Error entrenamiento")
plt.plot(k_values, tabla_resultados["Error_prueba"], "o--", label="Error prueba")
plt.plot(k_values, tabla_resultados["Gap"], "o-", label="Gap")
plt.axhline(0, color="black", alpha=0.3)
plt.xlabel("Número de vecinos (K)")
plt.ylabel("Error / Gap")
plt.title("Error y gap de KNN por valor de K")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "04_knn_error_gap.png", dpi=150)
plt.show()
