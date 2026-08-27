"""Persistencia de opiniones, zonas y comparables para VALUO SIPRI."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./valuo_sipri.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    municipality: Mapped[str] = mapped_column(String(120), default="San Luis Potosi")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_m: Mapped[int] = mapped_column(Integer, default=2000)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(160))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(200), default="Semilla demostrativa")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Comparable(Base):
    __tablename__ = "comparables"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(120))
    operation: Mapped[str] = mapped_column(String(20))
    property_type: Mapped[str] = mapped_column(String(40))
    zone_name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    construction_m2: Mapped[float] = mapped_column(Float)
    land_m2: Mapped[float] = mapped_column(Float)
    bedrooms: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(200), default="Muestra demostrativa")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    observed_at: Mapped[str] = mapped_column(String(20), default="2026-08")


class Opinion(Base):
    __tablename__ = "opinions"

    id: Mapped[int] = mapped_column(primary_key=True)
    folio: Mapped[str] = mapped_column(String(50), unique=True)
    client_name: Mapped[str] = mapped_column(String(160))
    operation: Mapped[str] = mapped_column(String(20))
    property_type: Mapped[str] = mapped_column(String(40))
    address: Mapped[str] = mapped_column(Text)
    zone_name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    land_m2: Mapped[float] = mapped_column(Float)
    construction_m2: Mapped[float] = mapped_column(Float)
    bedrooms: Mapped[int] = mapped_column(Integer)
    bathrooms: Mapped[float] = mapped_column(Float)
    parking_spaces: Mapped[int] = mapped_column(Integer)
    age_years: Mapped[int] = mapped_column(Integer)
    quality: Mapped[str] = mapped_column(String(30))
    amenities_text: Mapped[str] = mapped_column(Text, default="")
    estimate: Mapped[float] = mapped_column(Float)
    lower_value: Mapped[float] = mapped_column(Float)
    upper_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(40))
    comparable_summary: Mapped[str] = mapped_column(Text)
    valuation_summary: Mapped[str] = mapped_column(Text, default="{}")
    image_paths: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def create_database() -> None:
    Base.metadata.create_all(bind=engine)
    # Migraciones mínimas para instalaciones creadas por versiones anteriores.
    columns = {column["name"] for column in inspect(engine).get_columns("opinions")}
    if "valuation_summary" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE opinions ADD COLUMN valuation_summary TEXT DEFAULT '{}'"))
    # La confianza descriptiva puede superar 30 caracteres; PostgreSQL conserva el límite
    # de una tabla creada por la primera versión hasta que se migra explícitamente.
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE opinions ALTER COLUMN confidence TYPE VARCHAR(80)"))
