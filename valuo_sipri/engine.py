"""Motor inicial explicable: comparables cercanos + ajustes transparentes.

No es un avalúo ni sustituye la revisión profesional. Cuando existan datos suficientes,
el artefacto entrenado y validado se añadirá como una segunda estimación versionada.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Iterable

from .database import Amenity, Comparable

MODEL_VERSION = "savi-homologacion-v0.2"
CONDITIONS = {"MALO": 0, "REGULAR": 1, "BUENO": 2, "MUY_BUENO": 3, "EXCELENTE": 4}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia geográfica en kilómetros entre dos coordenadas."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(value))


def closest_amenities(latitude: float, longitude: float, amenities: Iterable[Amenity]) -> dict[str, float]:
    nearest: dict[str, float] = {}
    for amenity in amenities:
        distance = haversine_km(latitude, longitude, amenity.latitude, amenity.longitude)
        if amenity.category not in nearest or distance < nearest[amenity.category]:
            nearest[amenity.category] = distance
    return nearest


def ross_heidecke_depreciation(age_years: float, condition: str, useful_life: float = 60) -> float:
    """Depreciación técnica simplificada, configurable y visible; no sustituye tabla pericial."""
    age_ratio = min(max(age_years, 0) / useful_life, 0.95)
    state_multiplier = {"EXCELENTE": 0.75, "MUY_BUENO": 0.88, "BUENO": 1.0, "REGULAR": 1.18, "MALO": 1.35}
    return min(age_ratio * (1 + age_ratio) / 2 * state_multiplier.get(condition, 1.0), 0.85)


def iqr_active(comparables: list[Comparable]) -> list[Comparable]:
    """Excluye extremos por $/m² solo cuando el segmento tiene muestra suficiente."""
    if len(comparables) < 10:
        return comparables
    unit_values = sorted(c.price / max(c.construction_m2 or c.land_m2, 1) for c in comparables)
    q1, q3 = unit_values[len(unit_values) // 4], unit_values[(len(unit_values) * 3) // 4]
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [c for c in comparables if lower <= c.price / max(c.construction_m2 or c.land_m2, 1) <= upper]


def estimate_opinion(data: dict, comparables: list[Comparable], amenities: list[Amenity]) -> dict:
    """Obtiene K comparables por similitud y estima valor con precio por m2 ponderado."""
    operation, property_type = data["operation"], data["property_type"]
    target_area = data["construction_m2"] or data["land_m2"]
    candidates = [c for c in comparables if getattr(c, "is_active", True) and c.operation == operation and c.property_type == property_type]
    if not candidates:
        candidates = [c for c in comparables if getattr(c, "is_active", True) and c.operation == operation]
    if not candidates:
        raise ValueError("No existen comparables de prueba para la operación seleccionada.")
    cleaned = iqr_active(candidates)
    compatible_area = [c for c in cleaned if abs(target_area - (c.construction_m2 or c.land_m2)) / max(target_area, 1) <= 0.20]
    candidates = compatible_area or cleaned

    ranked = []
    for comparable in candidates:
        geo = haversine_km(data["latitude"], data["longitude"], comparable.latitude, comparable.longitude)
        comparable_area = comparable.construction_m2 or comparable.land_m2
        area_gap = abs(target_area - comparable_area) / max(target_area, 1)
        bedroom_gap = abs(data["bedrooms"] - comparable.bedrooms)
        # KNN explicable: menor distancia = comparable más compatible.
        score = geo * 1.8 + area_gap * 2.0 + bedroom_gap * 0.35
        original_ppsqm = comparable.price / max(comparable_area, 1)
        f_negotiation = 0.95
        f_surface = (target_area / max(comparable_area, 1)) ** 0.12
        comparable_condition = getattr(comparable, "condition", "BUENO")
        f_condition = 1 + (CONDITIONS.get(data.get("condition", "BUENO"), 2) - CONDITIONS.get(comparable_condition, 2)) * 0.05
        subject_remaining = 1 - ross_heidecke_depreciation(data.get("age_years", 0), data.get("condition", "BUENO"))
        comparable_remaining = 1 - ross_heidecke_depreciation(getattr(comparable, "age_years", 0), comparable_condition)
        f_age = subject_remaining / max(comparable_remaining, 0.15)
        total_factor = f_negotiation * f_surface * f_condition * f_age
        if not 0.80 <= total_factor <= 1.20:
            continue
        ranked.append({"item": comparable, "score": score, "geo": geo, "ppsqm": original_ppsqm * total_factor,
                       "factors": {"negociacion": f_negotiation, "superficie": f_surface, "conservacion": f_condition, "edad": f_age, "total": total_factor}})
    if not ranked:
        raise ValueError("No hay comparables técnicamente homologables dentro del límite de factores.")
    ranked.sort(key=lambda row: row["score"])
    nearest = ranked[: min(6, len(ranked))]

    weights = [1 / max(row["score"], 0.10) for row in nearest]
    weighted_ppsqm = sum(row["ppsqm"] * weight for row, weight in zip(nearest, weights)) / sum(weights)
    quality_factor = {"BASICA": 0.92, "MEDIA": 1.00, "BUENA": 1.07, "ALTA": 1.15}[data.get("quality", "MEDIA")]
    amenity_factor = min(len(data.get("amenities", [])) * 0.004, 0.04)
    estimate = weighted_ppsqm * target_area * quality_factor * (1 + amenity_factor)

    all_verified = all(row["item"].verified for row in nearest)
    confidence = "Preliminar - datos demostrativos" if not all_verified else "Media - revisión pendiente"
    margin = 0.10 if not all_verified else 0.05
    amenity_distances = closest_amenities(data["latitude"], data["longitude"], amenities)
    return {
        "estimate": round(estimate, 2), "lower": round(estimate * (1 - margin), 2), "upper": round(estimate * (1 + margin), 2),
        "confidence": confidence, "margin": margin, "model_version": MODEL_VERSION,
        "comparables": nearest, "amenity_distances": amenity_distances,
        "weighted_ppsqm": weighted_ppsqm,
        "formula": "$/m² homologado = $/m² comparable × Fnegociación × Fsuperficie × Fconservación × Fedad; media KNN ponderada × superficie",
    }


def estimate_both_markets(data: dict, comparables: list[Comparable], amenities: list[Amenity]) -> dict[str, dict]:
    """Calcula referencias independientes para venta y renta con sus propios comparables."""
    return {
        operation: estimate_opinion({**data, "operation": operation}, comparables, amenities)
        for operation in ("VENTA", "RENTA")
    }
