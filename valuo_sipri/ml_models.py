"""Carga de modelos supervisados versionados para la predicción de VALUO SIPRI."""

from __future__ import annotations

from functools import lru_cache
from math import expm1
from pathlib import Path

import joblib
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / "ia_models"
AMENITY_FEATURES = {
    "Alberca": "alberca_validado", "Vigilancia": "vigilancia_validado", "Jardín": "jardin_validado",
    "Terraza": "terraza_validado", "Balcón": "balcon_validado", "Amueblado": "amueblado_validado",
    "Aire acondicionado": "aire_acondicionado_validado", "Cocina integral": "cocina_integral_validado",
    "Gimnasio": "gimnasio_validado", "Elevador": "elevador_validado", "Bodega": "bodega_validado",
    "Roof garden": "roof_garden_validado", "Cuarto de servicio": "cuarto_servicio_validado", "Estudio": "estudio_validado",
}


@lru_cache(maxsize=2)
def load_bundle(market: str) -> dict | None:
    path = MODEL_DIR / f"{market.lower()}.joblib"
    return joblib.load(path) if path.exists() else None


def predict_ml(market: str, data: dict) -> dict | None:
    bundle = load_bundle(market)
    if not bundle:
        return None
    row = {name: 0.0 for name in bundle["feature_names"]}
    row["metros_validado_ajustado"] = float(data.get("construction_m2") or data.get("land_m2") or 0)
    row["habitaciones_validado_ajustado"] = float(data.get("bedrooms", 0))
    row["banos_validado_ajustado"] = float(data.get("bathrooms", 0))
    row["estacionamientos_validado_ajustado"] = float(data.get("parking_spaces", 0))
    for amenity in data.get("amenities", []):
        if amenity in AMENITY_FEATURES:
            row[AMENITY_FEATURES[amenity]] = 1.0
    matrix = pd.DataFrame([[row[name] for name in bundle["feature_names"]]], columns=bundle["feature_names"])
    raw_value = float(bundle["model"].predict(matrix)[0])
    value = expm1(raw_value) if bundle.get("target_transform") == "log1p" else raw_value
    return {"estimate": round(max(value, 0), 2), "model": bundle["selected_model"], "metrics": bundle["metrics"],
            "training_rows": bundle["training_rows"], "trained_at": bundle["trained_at"], "version": bundle["version"]}
