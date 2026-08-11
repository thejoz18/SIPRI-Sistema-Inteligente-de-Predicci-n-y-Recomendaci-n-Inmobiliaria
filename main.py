"""Ejecuta, en orden, los módulos 03 al 09 del proyecto inmobiliario."""

from pathlib import Path
import runpy


CARPETA_PROYECTO = Path(__file__).resolve().parent
MODULOS = [
    ("03_TFIDF.py", "Vectoriza los textos inmobiliarios con TF-IDF."),
    ("04_KNN_Clasificacion.py", "Entrena KNN para clasificar el tipo de mensaje."),
    ("05_Similitud_Coseno.py", "Busca publicaciones similares a una petición de texto."),
    ("06_Regresion_Lineal.py", "Entrena regresión lineal para estimar precio de renta."),
    ("07_Arbol_Decision.py", "Entrena árbol de decisión para estimar precio de renta."),
    ("08_Comparacion_Modelos.py", "Compara las métricas de regresión lineal y árbol."),
    ("09_Graficas_Resultados.py", "Genera las gráficas finales del proyecto."),
]

print("=" * 80)
print("EJECUCIÓN COMPLETA DEL PROYECTO INMOBILIARIO")
print("=" * 80)
print("Cada módulo muestra sus resultados y guarda archivos en resultados/.")

for archivo, explicacion in MODULOS:
    print("\n" + "-" * 80)
    print(f"EJECUTANDO {archivo}")
    print(f"¿Qué sucede?: {explicacion}")
    print("-" * 80)
    runpy.run_path(str(CARPETA_PROYECTO / archivo), run_name="__main__")

print("\n" + "=" * 80)
print("PROCESO TERMINADO")
print("Los modelos entrenados quedaron en resultados/modelos_guardados/.")
print("Para hacer predicciones, ejecuta 10_Interfaz_Predicciones.py.")
print("=" * 80)
