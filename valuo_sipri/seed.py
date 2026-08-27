"""Datos de arranque claramente marcados como demostrativos; no son comparables certificados."""

from .database import Amenity, Comparable, SessionLocal, Zone


def seed_database() -> None:
    session = SessionLocal()
    try:
        if session.query(Zone).count() == 0:
            session.add_all([
                Zone(name="Lomas del Tecnologico", latitude=22.1508, longitude=-100.9842),
                Zone(name="Tangamanga", latitude=22.1440, longitude=-100.9970),
                Zone(name="Pozos", municipality="Villa de Pozos", latitude=22.1010, longitude=-100.7480),
                Zone(name="Centro", latitude=22.1511, longitude=-100.9767),
            ])
        if session.query(Amenity).count() == 0:
            session.add_all([
                Amenity(category="Parque", name="Parque Tangamanga I", latitude=22.1430, longitude=-101.0000),
                Amenity(category="Hospital", name="Hospital demostrativo SLP", latitude=22.1420, longitude=-100.9850),
                Amenity(category="Escuela", name="Centro educativo demostrativo SLP", latitude=22.1540, longitude=-100.9830),
                Amenity(category="Vialidad", name="Acceso vial demostrativo SLP", latitude=22.1490, longitude=-100.9760),
            ])
        if session.query(Comparable).count() == 0:
            # Valores de prueba, no fuente de mercado ni recomendación comercial.
            session.add_all([
                Comparable(reference="Demo Lomas 01", operation="VENTA", property_type="CASA", zone_name="Lomas del Tecnologico", latitude=22.1510, longitude=-100.9840, construction_m2=180, land_m2=160, bedrooms=3, price=3900000),
                Comparable(reference="Demo Lomas 02", operation="VENTA", property_type="CASA", zone_name="Lomas del Tecnologico", latitude=22.1499, longitude=-100.9829, construction_m2=210, land_m2=180, bedrooms=3, price=4650000),
                Comparable(reference="Demo Tangamanga 01", operation="VENTA", property_type="CASA", zone_name="Tangamanga", latitude=22.1450, longitude=-100.9960, construction_m2=160, land_m2=145, bedrooms=3, price=3200000),
                Comparable(reference="Demo Pozos 01", operation="VENTA", property_type="CASA", zone_name="Pozos", latitude=22.1020, longitude=-100.7490, construction_m2=140, land_m2=150, bedrooms=3, price=2450000),
                Comparable(reference="Demo Lomas Renta 01", operation="RENTA", property_type="CASA", zone_name="Lomas del Tecnologico", latitude=22.1500, longitude=-100.9850, construction_m2=175, land_m2=160, bedrooms=3, price=22000),
                Comparable(reference="Demo Tangamanga Renta 01", operation="RENTA", property_type="CASA", zone_name="Tangamanga", latitude=22.1435, longitude=-100.9980, construction_m2=150, land_m2=145, bedrooms=3, price=17500),
            ])
        session.commit()
    finally:
        session.close()
