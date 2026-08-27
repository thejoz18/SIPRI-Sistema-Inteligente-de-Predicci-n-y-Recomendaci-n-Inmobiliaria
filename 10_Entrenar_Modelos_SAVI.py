"""Entrena modelos académicos de venta y renta para VALUO SIPRI.

Usa exclusivamente Regresión Lineal y Árbol de Decisión, como los módulos 06 y 07.
Ejecutar: .venv\\Scripts\\python.exe 10_Entrenar_Modelos_SAVI.py
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

SOURCE = Path("datos/dataset_ajustado.xlsx")
OUT_DIR = Path("valuo_sipri/ia_models")
FEATURES = [
    "metros_validado_ajustado", "habitaciones_validado_ajustado", "banos_validado_ajustado",
    "estacionamientos_validado_ajustado", "alberca_validado", "vigilancia_validado", "jardin_validado",
    "terraza_validado", "balcon_validado", "amueblado_validado", "aire_acondicionado_validado",
    "cocina_integral_validado", "gimnasio_validado", "elevador_validado", "bodega_validado",
    "roof_garden_validado", "cuarto_servicio_validado", "estudio_validado",
]
TARGETS = {"VENTA": "precio_venta_validado_analisis", "RENTA": "precio_renta_validado_analisis"}


def metrics(y_true, prediction) -> dict[str, float]:
    return {
        "mae": round(float(mean_absolute_error(y_true, prediction)), 2),
        "rmse": round(float(mean_squared_error(y_true, prediction) ** 0.5), 2),
        "r2": round(float(r2_score(y_true, prediction)), 4),
    }


def train_market(data: pd.DataFrame, market: str, target: str) -> dict:
    frame = data[FEATURES + [target]].copy()
    frame[target] = pd.to_numeric(frame[target], errors="coerce")
    frame = frame[frame[target] > 0]
    frame[FEATURES] = frame[FEATURES].apply(pd.to_numeric, errors="coerce").fillna(0)
    # La renta contiene anuncios extremos; se limpia con IQR antes de entrenar.
    if market == "RENTA":
        q1, q3 = frame[target].quantile(0.25), frame[target].quantile(0.75)
        iqr = q3 - q1
        frame = frame[frame[target].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)]
    x_train, x_test, y_train, y_test = train_test_split(frame[FEATURES], frame[target], test_size=0.20, random_state=42)
    candidates = {
        "Regresión lineal": LinearRegression(),
        "Árbol de decisión": DecisionTreeRegressor(max_depth=4, min_samples_leaf=5, random_state=42),
    }
    evaluated = {}
    for name, model in candidates.items():
        use_log = market == "RENTA"
        model.fit(x_train, y_train.map(math.log1p) if use_log else y_train)
        prediction = model.predict(x_test)
        evaluated[name] = {"model": model, "metrics": metrics(y_test, [math.expm1(value) for value in prediction] if use_log else prediction)}
    selected_name = min(evaluated, key=lambda name: evaluated[name]["metrics"]["mae"])
    bundle = {
        "market": market, "model": evaluated[selected_name]["model"], "selected_model": selected_name,
        "metrics": evaluated[selected_name]["metrics"],
        "all_metrics": {name: result["metrics"] for name, result in evaluated.items()},
        "feature_names": FEATURES, "training_rows": len(frame), "test_rows": len(x_test),
        "trained_at": datetime.now(timezone.utc).isoformat(), "source": str(SOURCE), "target_transform": "log1p" if market == "RENTA" else "none", "version": "savi-ia-v1",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, OUT_DIR / f"{market.lower()}.joblib")
    return bundle


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"No existe la base de entrenamiento: {SOURCE}")
    data = pd.read_excel(SOURCE, sheet_name="DATOS_AJUSTADOS")
    summary = {}
    for market, target in TARGETS.items():
        bundle = train_market(data, market, target)
        summary[market] = {key: value for key, value in bundle.items() if key != "model"}
        print(f"{market}: {bundle['selected_model']} | MAE {bundle['metrics']['mae']:,.2f} | R² {bundle['metrics']['r2']}")
    (OUT_DIR / "model_card.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
