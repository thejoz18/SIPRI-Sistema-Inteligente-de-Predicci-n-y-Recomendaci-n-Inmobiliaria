"""Módulo 09: concentrador de gráficas y resultados principales."""

import matplotlib.pyplot as plt
import pandas as pd
from importlib import import_module

datos_comunes = import_module("02_Datos_Comunes")
CARPETA_GRAFICAS = datos_comunes.CARPETA_GRAFICAS
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
cargar_dataset = datos_comunes.cargar_dataset


# 1. CARGAR DATASET Y RESULTADOS DE MÓDULOS ANTERIORES
df = cargar_dataset()
archivo_knn = CARPETA_METRICAS / "04_knn_resultados.csv"
archivo_comparacion = CARPETA_METRICAS / "08_comparacion_modelos.csv"

if not archivo_knn.exists() or not archivo_comparacion.exists():
    raise FileNotFoundError(
        "Ejecuta primero 04_KNN_Clasificacion.py y 08_Comparacion_Modelos.py."
    )

knn = pd.read_csv(archivo_knn)
comparacion = pd.read_csv(archivo_comparacion)
CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)

# 2. DISTRIBUCIÓN DE CLASES
clases = df["Tipo_Mensaje"].fillna("SIN_DATO").value_counts()
plt.figure(figsize=(9, 6))
plt.bar(clases.index, clases.values, color="steelblue")
plt.xlabel("Tipo de mensaje")
plt.ylabel("Número de publicaciones")
plt.title("Distribución de clases del dataset")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "09_distribucion_clases.png", dpi=150)
plt.show()

# 3. CONCENTRAR LAS CURVAS KNN EN UNA SOLA FIGURA
figura, ejes = plt.subplots(1, 2, figsize=(14, 5))
ejes[0].plot(knn["K"], knn["Accuracy_entrenamiento"], "o-", label="Entrenamiento")
ejes[0].plot(knn["K"], knn["Accuracy_prueba"], "o-", label="Prueba")
ejes[0].set_title("Accuracy de KNN")
ejes[0].set_xlabel("K")
ejes[0].set_ylabel("Accuracy")
ejes[0].set_ylim(0, 1.05)
ejes[0].grid(alpha=0.3)
ejes[0].legend()

ejes[1].plot(knn["K"], knn["Error_entrenamiento"], "o--", label="Error entrenamiento")
ejes[1].plot(knn["K"], knn["Error_prueba"], "o--", label="Error prueba")
ejes[1].plot(knn["K"], knn["Gap"], "o-", label="Gap")
ejes[1].axhline(0, color="black", alpha=0.3)
ejes[1].set_title("Errores y gap de KNN")
ejes[1].set_xlabel("K")
ejes[1].set_ylabel("Error / Gap")
ejes[1].grid(alpha=0.3)
ejes[1].legend()

plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "09_resumen_knn.png", dpi=150)
plt.show()

# 4. COMPARACIÓN DE MÉTRICAS DE PRECIO
metricas_error = comparacion[comparacion["Métrica"] != "R² Score"]
plt.figure(figsize=(10, 6))
posiciones = range(len(metricas_error))
plt.bar([p - 0.2 for p in posiciones], metricas_error["Regresión Lineal"], width=0.4, label="Regresión Lineal")
plt.bar([p + 0.2 for p in posiciones], metricas_error["Árbol de Decisión"], width=0.4, label="Árbol de Decisión")
plt.xticks(list(posiciones), metricas_error["Métrica"])
plt.ylabel("Error en pesos")
plt.title("Comparación de errores de modelos de precio")
plt.legend()
plt.tight_layout()
plt.savefig(CARPETA_GRAFICAS / "09_comparacion_metricas.png", dpi=150)
plt.show()

print("=" * 80)
print("MÓDULO 09 - GRÁFICAS PRINCIPALES")
print("=" * 80)
print("Gráficas guardadas en resultados/graficas/")
print("\nTabla de comparación:")
print(comparacion.round(4).to_string(index=False))
