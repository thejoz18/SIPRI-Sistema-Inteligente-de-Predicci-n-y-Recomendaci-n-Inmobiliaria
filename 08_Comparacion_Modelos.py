"""Módulo 08: comparación de regresión lineal y árbol de decisión."""

import numpy as np
import pandas as pd
from importlib import import_module
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

datos_comunes = import_module("02_Datos_Comunes")
CARPETA_METRICAS = datos_comunes.CARPETA_METRICAS
preparar_datos_precio = datos_comunes.preparar_datos_precio


# 1. USAR LA MISMA OPERACIÓN, VARIABLES Y SEPARACIÓN EN AMBOS MODELOS
OPERACION = "RENTA"
X, y, caracteristicas, columna_precio = preparar_datos_precio(OPERACION)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# 2. ENTRENAR LOS DOS MODELOS VISTOS EN CLASE
regresion_lineal = LinearRegression()
regresion_lineal.fit(X_train, y_train)
pred_lr = regresion_lineal.predict(X_test)

arbol = DecisionTreeRegressor(max_depth=3, random_state=42)
arbol.fit(X_train, y_train)
pred_arbol = arbol.predict(X_test)

# 3. CALCULAR EXACTAMENTE LAS MÉTRICAS DEL NOTEBOOK
tabla_metricas = pd.DataFrame({
    "Métrica": ["R² Score", "MAE", "MSE", "RMSE"],
    "Regresión Lineal": [
        r2_score(y_test, pred_lr),
        mean_absolute_error(y_test, pred_lr),
        mean_squared_error(y_test, pred_lr),
        np.sqrt(mean_squared_error(y_test, pred_lr)),
    ],
    "Árbol de Decisión": [
        r2_score(y_test, pred_arbol),
        mean_absolute_error(y_test, pred_arbol),
        mean_squared_error(y_test, pred_arbol),
        np.sqrt(mean_squared_error(y_test, pred_arbol)),
    ],
})

print("=" * 80)
print(f"MÓDULO 08 - COMPARACIÓN DE MODELOS PARA {OPERACION}")
print("=" * 80)
print(f"Variable objetivo: {columna_precio}")
print(f"Características: {', '.join(caracteristicas)}")
print("\n" + tabla_metricas.round(4).to_string(index=False))
print("\nInterpretación: R² más alto ayuda a explicar variación; MAE y RMSE más bajos")
print("representan menor error en pesos. La elección no se basa sólo en R².")

# 4. GUARDAR TABLA PARA EL MÓDULO DE GRÁFICAS
CARPETA_METRICAS.mkdir(parents=True, exist_ok=True)
tabla_metricas.to_csv(CARPETA_METRICAS / "08_comparacion_modelos.csv", index=False)
print("\nTabla guardada en resultados/metricas/08_comparacion_modelos.csv")
