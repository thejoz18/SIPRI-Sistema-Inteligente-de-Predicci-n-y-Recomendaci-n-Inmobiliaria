"""Servidor web de VALUO SIPRI para Render."""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .database import Amenity, Comparable, Opinion, SessionLocal, Zone, create_database
from .engine import estimate_both_markets
from .ml_models import predict_ml
from .seed import seed_database

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "runtime_data"))
FREE_MODE = os.getenv("FREE_MODE", "false").lower() == "true"
UPLOAD_DIR = DATA_DIR / "uploads"
PDF_DIR = DATA_DIR / "pdf"
for folder in (UPLOAD_DIR, PDF_DIR):
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="VALUO SIPRI", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
logger = logging.getLogger("valuo_sipri")


@app.on_event("startup")
def startup() -> None:
    create_database()
    seed_database()


def number(value: str | float | int, field: str, allow_negative: bool = False) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, f"{field} debe ser numérico.") from exc
    if parsed < 0 and not allow_negative:
        raise HTTPException(422, f"{field} no puede ser negativo.")
    return parsed


def make_folio() -> str:
    return f"SIPRI-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:5].upper()}"


def currency(value: float) -> str:
    return f"${value:,.0f} MXN"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "VALUO SIPRI"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    session = SessionLocal()
    try:
        zones = session.query(Zone).order_by(Zone.name).all()
        opinions = session.query(Opinion).order_by(Opinion.created_at.desc()).limit(8).all()
        return templates.TemplateResponse(request, "index.html", {"zones": zones, "opinions": opinions, "free_mode": FREE_MODE})
    finally:
        session.close()


@app.post("/opinions")
async def create_opinion(
    client_name: str = Form(...), address: str = Form(...), operation: str = Form(...), property_type: str = Form(...),
    zone_name: str = Form(...), latitude: str = Form(...), longitude: str = Form(...), land_m2: str = Form("0"),
    construction_m2: str = Form("0"), bedrooms: str = Form("0"), bathrooms: str = Form("0"),
    parking_spaces: str = Form("0"), age_years: str = Form("0"), quality: str = Form("MEDIA"), condition: str = Form("BUENO"),
    amenities: list[str] = Form(default=[]), photos: list[UploadFile] = File(default=[]),
):
    operation, property_type, quality, condition = operation.upper(), property_type.upper(), quality.upper(), condition.upper()
    if operation not in {"VENTA", "RENTA"} or property_type not in {"CASA", "DEPARTAMENTO", "BODEGA", "TERRENO"}:
        raise HTTPException(422, "Operación o tipo de inmueble no permitido.")
    if quality not in {"BASICA", "MEDIA", "BUENA", "ALTA"}:
        raise HTTPException(422, "Calidad no permitida.")
    if condition not in {"MALO", "REGULAR", "BUENO", "MUY_BUENO", "EXCELENTE"}:
        raise HTTPException(422, "Estado de conservación no permitido.")
    values = {
        "client_name": client_name.strip(), "address": address.strip(), "operation": operation, "property_type": property_type,
        "zone_name": zone_name, "latitude": number(latitude, "Latitud", allow_negative=True), "longitude": number(longitude, "Longitud", allow_negative=True),
        "land_m2": number(land_m2, "Terreno"), "construction_m2": number(construction_m2, "Construcción"),
        "bedrooms": int(number(bedrooms, "Recámaras")), "bathrooms": number(bathrooms, "Baños"),
        "parking_spaces": int(number(parking_spaces, "Estacionamientos")), "age_years": int(number(age_years, "Antigüedad")),
        "quality": quality, "condition": condition, "amenities": amenities,
    }
    if not -90 <= values["latitude"] <= 90 or not -180 <= values["longitude"] <= 180:
        raise HTTPException(422, "Las coordenadas están fuera de rango.")
    if values["land_m2"] <= 0 and values["construction_m2"] <= 0:
        raise HTTPException(422, "Capture al menos m2 de terreno o construcción.")

    session = SessionLocal()
    try:
        results = estimate_both_markets(values, session.query(Comparable).all(), session.query(Amenity).all())
        result = results[operation]
        folio = make_folio()
        photo_paths: list[str] = []
        safe_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        for photo in photos[:6]:
            suffix = Path(photo.filename or "").suffix.lower()
            if suffix not in safe_extensions:
                continue
            destination = UPLOAD_DIR / f"{folio}_{uuid.uuid4().hex[:8]}{suffix}"
            with destination.open("wb") as file:
                shutil.copyfileobj(photo.file, file)
            photo_paths.append(str(destination))
        valuation_summary = {}
        comparable_summary = {}
        for market, market_result in results.items():
            market_comparables = [
                {"referencia": row["item"].reference, "precio": row["item"].price, "distancia_km": round(row["geo"], 2), "verificado": row["item"].verified, "factores": row["factors"]}
                for row in market_result["comparables"]
            ]
            comparable_summary[market] = market_comparables
            valuation_summary[market] = {
                "estimate": market_result["estimate"], "lower": market_result["lower"], "upper": market_result["upper"],
                "confidence": market_result["confidence"], "model_version": market_result["model_version"],
                "ia": predict_ml(market, values),
            }
        opinion = Opinion(
            folio=folio, image_paths=json.dumps(photo_paths), amenities_text=", ".join(amenities),
            comparable_summary=json.dumps(comparable_summary, ensure_ascii=False), valuation_summary=json.dumps(valuation_summary, ensure_ascii=False),
            estimate=result["estimate"], lower_value=result["lower"], upper_value=result["upper"], confidence=result["confidence"],
            model_version=result["model_version"], **{key: value for key, value in values.items() if key != "amenities"},
        )
        session.add(opinion)
        session.commit()
        return RedirectResponse(f"/opinions/{opinion.id}", status_code=303)
    except Exception as exc:
        session.rollback()
        logger.exception("No fue posible guardar la opinión de valor")
        # El detalle queda en los registros de Render; al usuario se le muestra un mensaje seguro.
        raise HTTPException(500, "No fue posible guardar la opinión. Revise que el despliegue tenga la base de datos configurada.") from exc
    finally:
        session.close()


@app.get("/opinions/{opinion_id}", response_class=HTMLResponse)
def view_opinion(request: Request, opinion_id: int):
    session = SessionLocal()
    try:
        opinion = session.get(Opinion, opinion_id)
        if not opinion:
            raise HTTPException(404, "Opinión no encontrada.")
        valuations = json.loads(opinion.valuation_summary or "{}")
        comparable_data = json.loads(opinion.comparable_summary)
        if not valuations:  # Compatibilidad con opiniones creadas antes de la doble estimación.
            valuations = {opinion.operation: {"estimate": opinion.estimate, "lower": opinion.lower_value, "upper": opinion.upper_value, "confidence": opinion.confidence, "model_version": opinion.model_version}}
        if isinstance(comparable_data, list):
            comparable_data = {opinion.operation: comparable_data}
        amenity_distances = closest_distances(opinion)
        return templates.TemplateResponse(request, "opinion.html", {
            "opinion": opinion, "valuations": valuations, "comparables": comparable_data, "amenity_distances": amenity_distances, "currency": currency,
        })
    finally:
        session.close()


def closest_distances(opinion: Opinion) -> dict[str, float]:
    session = SessionLocal()
    try:
        from .engine import closest_amenities
        return closest_amenities(opinion.latitude, opinion.longitude, session.query(Amenity).all())
    finally:
        session.close()


@app.get("/opinions/{opinion_id}/pdf")
def opinion_pdf(opinion_id: int):
    session = SessionLocal()
    try:
        opinion = session.get(Opinion, opinion_id)
        if not opinion:
            raise HTTPException(404, "Opinión no encontrada.")
        destination = PDF_DIR / f"{opinion.folio}.pdf"
        build_pdf(opinion, destination)
        return FileResponse(destination, media_type="application/pdf", filename=f"Opinion_de_Valor_{opinion.folio}.pdf")
    finally:
        session.close()


def build_pdf(opinion: Opinion, destination: Path) -> None:
    """Genera el informe estático de la opinión; el dictamen profesional sigue siendo obligatorio."""
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=1.4 * cm, leftMargin=1.4 * cm, topMargin=1.25 * cm, bottomMargin=1.25 * cm)
    story = [
        Paragraph("SIPCO", styles["Title"]),
        Paragraph("VALUO SIPRI | OPINIÓN DE VALOR", styles["Heading1"]),
        Paragraph(f"Folio: {opinion.folio} | Fecha: {opinion.created_at:%d/%m/%Y}", styles["Normal"]), Spacer(1, 12),
        Paragraph("Referencias preliminares de valor", styles["Heading2"]),
        Paragraph("Ficha de la propiedad", styles["Heading2"]),
    ]
    valuations = json.loads(opinion.valuation_summary or "{}")
    if not valuations:
        valuations = {opinion.operation: {"estimate": opinion.estimate, "lower": opinion.lower_value, "upper": opinion.upper_value, "confidence": opinion.confidence, "model_version": opinion.model_version}}
    value_rows = [["Mercado", "Valor central", "Rango"]]
    for market in ("VENTA", "RENTA"):
        value = valuations.get(market)
        if value:
            value_rows.append([market, currency(value["estimate"]), f"{currency(value['lower'])} a {currency(value['upper'])}"])
    values_table = Table(value_rows, colWidths=[3.2 * cm, 5.0 * cm, 8.8 * cm])
    values_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B5ED7")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7DEE2")), ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [values_table, Spacer(1, 12), Paragraph("Ficha de la propiedad", styles["Heading2"])]
    rows = [["Cliente", opinion.client_name], ["Mercado de interés", opinion.operation], ["Tipo", opinion.property_type], ["Ubicación", opinion.address], ["Zona", opinion.zone_name], ["Terreno", f"{opinion.land_m2:,.1f} m2"], ["Construcción", f"{opinion.construction_m2:,.1f} m2"], ["Recámaras / Baños / Cajones", f"{opinion.bedrooms} / {opinion.bathrooms} / {opinion.parking_spaces}"], ["Antigüedad / Calidad", f"{opinion.age_years} años / {opinion.quality}"], ["Amenidades", opinion.amenities_text or "No capturadas"]]
    table = Table(rows, colWidths=[5 * cm, 12 * cm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#123047")), ("TEXTCOLOR", (0, 0), (0, -1), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7DEE2")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [table, Spacer(1, 12), Paragraph("Comparables considerados", styles["Heading2"])]
    comparison_data = json.loads(opinion.comparable_summary)
    if isinstance(comparison_data, list):
        comparison_data = {opinion.operation: comparison_data}
    comparisons = [["Mercado", "Referencia", "Precio", "Distancia", "Estado"]]
    for market, items in comparison_data.items():
        for item in items:
            comparisons.append([market, item["referencia"], currency(item["precio"]), f"{item['distancia_km']} km", "Verificado" if item["verificado"] else "Demostrativo"])
    comparison_table = Table(comparisons, colWidths=[2.1 * cm, 4.7 * cm, 3.8 * cm, 2.6 * cm, 3.8 * cm])
    comparison_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C89A3B")), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7DEE2")), ("PADDING", (0, 0), (-1, -1), 6)]))
    story += [comparison_table, Spacer(1, 12)]
    image_paths = json.loads(opinion.image_paths)
    valid_images = [Path(path) for path in image_paths if Path(path).exists()]
    if valid_images:
        story.append(Paragraph("Registro fotográfico", styles["Heading2"]))
        for image_path in valid_images[:4]:
            image = Image(str(image_path), width=15 * cm, height=8 * cm, kind="proportional")
            story += [image, Spacer(1, 6)]
    story += [
        Spacer(1, 8), Paragraph("Nota metodológica", styles["Heading2"]),
        Paragraph("La estimación combina precio por m2 de comparables seleccionados por cercanía geográfica y similitud de superficie/recámaras, con ajustes explícitos de calidad, amenidades y antigüedad.", styles["Normal"]),
        Spacer(1, 8), Paragraph("Esta Opinión de Valor es un resultado preliminar de apoyo y no constituye un avalúo formal. Debe ser revisada, complementada con comparables verificados y autorizada por el profesional responsable antes de su uso comercial.", styles["Normal"]),
        Spacer(1, 20), Paragraph("ARQ. JOSE RAMON TORRES MURILLO", styles["Heading3"]), Paragraph("Responsable de revisión | VALUO SIPRI", styles["Normal"]),
    ]
    document.build(story)
