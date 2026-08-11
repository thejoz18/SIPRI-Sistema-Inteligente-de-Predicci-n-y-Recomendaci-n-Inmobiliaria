"""Módulo 07: estimación de precio de renta y venta con árbol de decisión."""

from importlib import import_module

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, plot_tree


datos_comunes = import_module("02_Datos_Comunes")
CARPETA_GRAFICAS = datos_comunes.CARPETA_GRAFICAS
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
CARPETA_MODELOS = datos_comunes.CARPETA_MODELOS
preparar_datos_precio = datos_comunes.preparar_datos_precio


OPERACIONES = ["RENTA", "VENTA"]
resumen_metricas = []
CARPETA_METRICAS.mkdir(parents=True, exist_ok=True)
CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

for OPERACION in OPERACIONES:
    # 1. PREPARAR DATOS SIN RELLENAR VALORES FALTANTES
    X, y, caracteristicas, columna_precio = preparar_datos_precio(OPERACION)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    # 2. ENTRENAR ÁRBOL COMO EN EL NOTEBOOK DE CLASE
    modelo = DecisionTreeRegressor(max_depth=3, random_state=42)
    modelo.fit(X_train, y_train)
    predicciones = modelo.predict(X_test)

    # 3. MEDIR RESULTADOS
    r2 = r2_score(y_test, predicciones)
    mae = mean_absolute_error(y_test, predicciones)
    mse = mean_squared_error(y_test, predicciones)
    rmse = np.sqrt(mse)
    resumen_metricas.append([OPERACION, r2, mae, mse, rmse, len(X)])

    print("=" * 80)
    print(f"MÓDULO 07 - ÁRBOL DE DECISIÓN PARA PRECIO DE {OPERACION}")
    print("=" * 80)
    print(f"Registros completos usados: {len(X)}")
    print(f"Variable objetivo: {columna_precio}")
    print(f"Profundidad: {modelo.get_depth()} | Hojas: {modelo.get_n_leaves()}")
    print(f"R² de prueba: {r2:.4f} | MAE: {mae:.2f} | RMSE: {rmse:.2f}")

    # 4. GUARDAR MODELO Y PREDICCIONES
    nombre = OPERACION.lower()
    joblib.dump(
        {"modelo": modelo, "caracteristicas": caracteristicas, "operacion": OPERACION},
        CARPETA_MODELOS / f"07_arbol_decision_{nombre}.pkl",
    )
    pd.DataFrame({"precio_real": y_test.values, "precio_predicho": predicciones}).to_csv(
        CARPETA_METRICAS / f"07_predicciones_arbol_decision_{nombre}.csv", index=False
    )

    # 5. GRAFICAR PREDICCIONES Y ESTRUCTURA DEL ÁRBOL
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, predicciones, alpha=0.7, color="darkorange", label="Predicciones")
    limite_minimo = min(y_test.min(), predicciones.min())
    limite_maximo = max(y_test.max(), predicciones.max())
    plt.plot([limite_minimo, limite_maximo], [limite_minimo, limite_maximo], "r--", label="Predicción perfecta")
    plt.xlabel("Precio real")
    plt.ylabel("Precio predicho")
    plt.title(f"Árbol: precio real vs predicho ({OPERACION})")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(CARPETA_GRAFICAS / f"07_arbol_real_vs_predicho_{nombre}.png", dpi=150)
    plt.show()

    plt.figure(figsize=(24, 10))
    plot_tree(modelo, feature_names=caracteristicas, filled=True, rounded=True, fontsize=8)
    plt.title(f"Árbol de decisión para precio de {OPERACION}")
    plt.tight_layout()
    plt.savefig(CARPETA_GRAFICAS / f"07_arbol_decision_{nombre}.png", dpi=150)
    plt.show()

pd.DataFrame(
    resumen_metricas, columns=["Operación", "R2", "MAE", "MSE", "RMSE", "Registros"]
).to_csv(CARPETA_METRICAS / "07_metricas_arbol_decision.csv", index=False)
