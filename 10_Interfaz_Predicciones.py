"""Interfaz de predicciones inmobiliarias basada en texto libre."""

import re
import unicodedata
import tkinter as tk
from importlib import import_module
from pathlib import Path
from tkinter import messagebox, scrolledtext

import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


CARPETA_PROYECTO = Path(__file__).resolve().parent
CARPETA_MODELOS = CARPETA_PROYECTO / "resultados" / "modelos_guardados"
AMENIDADES = [
    "alberca_validado", "vigilancia_validado", "jardin_validado", "terraza_validado",
    "balcon_validado", "amueblado_validado", "aire_acondicionado_validado",
    "cocina_integral_validado", "gimnasio_validado", "elevador_validado",
    "bodega_validado", "roof_garden_validado", "cuarto_servicio_validado", "estudio_validado",
]
datos_comunes = import_module("02_Datos_Comunes")


class InterfazPredicciones:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Predicciones inmobiliarias")
        self.ventana.geometry("1000x700")
        self.ventana.minsize(850, 600)
        self._cargar_modelos()
        self._crear_componentes()

    def _cargar_modelos(self):
        archivos = {
            "tfidf": "03_tfidf_similitud.pkl", "knn": "04_knn_tipo_mensaje.pkl",
            "lineal_renta": "06_regresion_lineal_renta.pkl", "lineal_venta": "06_regresion_lineal_venta.pkl",
            "arbol_renta": "07_arbol_decision_renta.pkl", "arbol_venta": "07_arbol_decision_venta.pkl",
        }
        faltantes = [nombre for nombre in archivos.values() if not (CARPETA_MODELOS / nombre).exists()]
        if faltantes:
            raise FileNotFoundError("Faltan modelos entrenados. Ejecuta primero main.py.\n" + "\n".join(faltantes))
        self.modelo_tfidf = joblib.load(CARPETA_MODELOS / archivos["tfidf"])
        self.modelo_knn = joblib.load(CARPETA_MODELOS / archivos["knn"])
        self.modelos_lineales = {
            "RENTA": joblib.load(CARPETA_MODELOS / archivos["lineal_renta"]),
            "VENTA": joblib.load(CARPETA_MODELOS / archivos["lineal_venta"]),
        }
        self.modelos_arbol = {
            "RENTA": joblib.load(CARPETA_MODELOS / archivos["arbol_renta"]),
            "VENTA": joblib.load(CARPETA_MODELOS / archivos["arbol_venta"]),
        }

    def _crear_componentes(self):
        marco = tk.Frame(self.ventana, padx=15, pady=15)
        marco.pack(fill=tk.BOTH, expand=True)
        tk.Label(marco, text="Sistema académico inmobiliario", font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(marco, text="Describe la propiedad o solicitud; el sistema identifica renta/venta, zona, habitaciones y amenidades.").pack(anchor="w")
        tk.Label(marco, text="Ejemplo: Busco casa en renta en Lomas con 3 recámaras, jardín, alberca y vigilancia.", fg="gray").pack(anchor="w")
        self.texto = scrolledtext.ScrolledText(marco, height=7, wrap=tk.WORD)
        self.texto.pack(fill=tk.X, pady=(4, 8))

        botones = tk.Frame(marco)
        botones.pack(fill=tk.X)
        tk.Button(botones, text="Buscar propiedades compatibles", command=self.buscar_similares).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(botones, text="Clasificar tipo de mensaje (KNN)", command=self.clasificar_mensaje).pack(side=tk.LEFT)
        tk.Label(marco, text="Una solicitud busca ofertas; una oferta busca solicitudes compatibles.", fg="gray").pack(anchor="w", pady=(4, 8))

        tk.Label(marco, text="Estimación de precio desde el texto", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(marco, text="Si faltan habitaciones se usan 2 como estándar, excepto para local o bodega.").pack(anchor="w")
        botones_precio = tk.Frame(marco, pady=8)
        botones_precio.pack(fill=tk.X)
        tk.Button(botones_precio, text="Estimar precio (Regresión Lineal)", command=self.predecir_lineal).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(botones_precio, text="Estimar precio (Árbol de Decisión)", command=self.predecir_arbol).pack(side=tk.LEFT)

        tk.Label(marco, text="Resultado", font=("Arial", 12, "bold")).pack(anchor="w")
        self.resultado = scrolledtext.ScrolledText(marco, height=17, wrap=tk.WORD, state=tk.DISABLED)
        self.resultado.pack(fill=tk.BOTH, expand=True)

    def _obtener_texto(self):
        texto = self.texto.get("1.0", tk.END).strip()
        if not texto:
            raise ValueError("Escribe primero una publicación o solicitud.")
        return texto

    @staticmethod
    def _normalizar(texto):
        return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")

    def _extraer_datos(self, texto):
        limpio = self._normalizar(texto)
        es_comercial = bool(re.search(r"\b(local|bodega)\b", limpio))
        habitaciones = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:recamaras?|habitaciones?|cuartos?|dormitorios?)\b", limpio)
        numero_habitaciones = float(habitaciones.group(1).replace(",", ".")) if habitaciones else (0.0 if es_comercial else 2.0)
        datos = {"habitaciones_validado": numero_habitaciones}
        sinonimos = {
            "alberca_validado": ("alberca", "piscina"), "vigilancia_validado": ("vigilancia", "seguridad", "caseta"),
            "jardin_validado": ("jardin",), "terraza_validado": ("terraza",), "balcon_validado": ("balcon",),
            "amueblado_validado": ("amueblado", "amueblada"), "aire_acondicionado_validado": ("aire acondicionado", "minisplit", "mini split"),
            "cocina_integral_validado": ("cocina integral",), "gimnasio_validado": ("gimnasio", "gym"),
            "elevador_validado": ("elevador",), "bodega_validado": ("bodega",), "roof_garden_validado": ("roof garden", "rooftop"),
            "cuarto_servicio_validado": ("cuarto de servicio",), "estudio_validado": ("estudio",),
        }
        for amenidad in AMENIDADES:
            datos[amenidad] = int(any(palabra in limpio for palabra in sinonimos[amenidad]))
        operacion = "VENTA" if re.search(r"\b(venta|vendo|vender|comprar|compro)\b", limpio) else "RENTA"
        zona = re.search(r"\b(?:en|zona|colonia|fracc\.?|fraccionamiento)\s+([a-z0-9][a-z0-9 .'-]{2,40})(?=,|\.|;|\n|$)", limpio)
        zona = re.split(r"\b(?:con|de|y|para)\b", zona.group(1))[0].strip() if zona else ""
        superficie = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:m2|m²|metros cuadrados?)\b", limpio)
        metros = float(superficie.group(1).replace(",", ".")) if superficie else None
        categoria = "Pendiente de superficie"
        if metros is not None:
            categoria = "Residencia" if metros >= 200 else "Casa estándar" if metros >= 90 else "Casa económica" if metros >= 60 else "Propiedad compacta"
        naturaleza = "SOLICITUD" if re.search(r"\b(busco|solicito|necesito|quiero)\b", limpio) else "OFERTA" if re.search(r"\b(rento|vendo|ofrezco|disponible)\b", limpio) else None
        return pd.DataFrame([datos]), operacion, zona, datos, metros, categoria, naturaleza

    def _mostrar_resultado(self, texto):
        self.resultado.configure(state=tk.NORMAL)
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, texto)
        self.resultado.configure(state=tk.DISABLED)

    def buscar_similares(self):
        try:
            texto = self._obtener_texto()
            _, _, zona, _, _, _, naturaleza = self._extraer_datos(texto)
            contraparte = {"OFERTA": "SOLICITUD", "SOLICITUD": "OFERTA"}.get(naturaleza)
            publicaciones = self.modelo_tfidf["publicaciones"].copy().reset_index(drop=True)
            candidatos, filtros = datos_comunes.filtrar_por_intencion(publicaciones, texto, zona, contraparte)
            vector = self.modelo_tfidf["vectorizador"].transform([texto])
            candidatos = candidatos.assign(similitud=cosine_similarity(vector, self.modelo_tfidf["matriz"][candidatos.index])[0])
            respuesta = "PROPIEDADES COMPATIBLES\n"
            respuesta += f"Tu mensaje: {naturaleza or 'sin definir'} | Se buscan: {contraparte or 'compatibles'}\nFiltros: {filtros}\n\n"
            for _, fila in candidatos.sort_values("similitud", ascending=False).head(5).iterrows():
                respuesta += f"Similitud: {fila['similitud']:.4f}\nTipo: {fila.get('tipo_propiedad_validado', '')} | Operación: {fila.get('operacion_validada', '')}\nTexto: {fila['texto_limpio'][:350]}\n\n"
            self._mostrar_resultado(respuesta)
        except ValueError as error:
            messagebox.showwarning("Dato faltante", str(error))

    def clasificar_mensaje(self):
        try:
            texto = self._obtener_texto()
            clase = self.modelo_knn.predict([texto])[0]
            probabilidades = self.modelo_knn.predict_proba([texto])[0]
            clases = self.modelo_knn.named_steps["knn"].classes_
            self._mostrar_resultado("TIPO PREDICHO: " + str(clase) + "\n\n" + "\n".join(f"- {clase}: {prob * 100:.2f}%" for clase, prob in zip(clases, probabilidades)))
        except ValueError as error:
            messagebox.showwarning("Dato faltante", str(error))

    def predecir_lineal(self):
        self._predecir_precio("lineal")

    def predecir_arbol(self):
        self._predecir_precio("arbol")

    def _predecir_precio(self, tipo):
        try:
            datos, operacion, zona, valores, metros, categoria, _ = self._extraer_datos(self._obtener_texto())
            guardado = (self.modelos_lineales if tipo == "lineal" else self.modelos_arbol)[operacion]
            modelo, caracteristicas = guardado["modelo"], guardado["caracteristicas"]
            precio = modelo.predict(datos[caracteristicas])[0]
            if tipo == "lineal":
                aportes = [f"- {n.replace('_validado', '').replace('_', ' ')}: {coef * datos.iloc[0][n]:+,.2f}" for n, coef in zip(caracteristicas, modelo.coef_) if datos.iloc[0][n] != 0]
                explicacion = f"Precio base aprendido: ${modelo.intercept_:,.2f}\nAportes detectados:\n" + "\n".join(aportes)
                nombre = "REGRESIÓN LINEAL"
            else:
                nodo, reglas = 0, []
                while modelo.tree_.children_left[nodo] != modelo.tree_.children_right[nodo]:
                    indice, limite = modelo.tree_.feature[nodo], modelo.tree_.threshold[nodo]
                    izquierda = datos.iloc[0][caracteristicas[indice]] <= limite
                    reglas.append(f"- {caracteristicas[indice].replace('_validado', '')} {'≤' if izquierda else '>'} {limite:.2f}")
                    nodo = modelo.tree_.children_left[nodo] if izquierda else modelo.tree_.children_right[nodo]
                explicacion = "Reglas seguidas por el árbol:\n" + "\n".join(reglas) + f"\nHoja con {modelo.tree_.n_node_samples[nodo]} ejemplos similares."
                nombre = "ÁRBOL DE DECISIÓN"
            amenidades = ", ".join(n.replace("_validado", "").replace("_", " ") for n in AMENIDADES if valores[n]) or "ninguna detectada"
            habitacion = f"{int(valores['habitaciones_validado'])}" + (" (estándar)" if valores["habitaciones_validado"] == 2 else "")
            superficie = f"{metros:g} m²" if metros is not None else "no detectada"
            self._mostrar_resultado(f"{nombre} ({operacion})\n\nEstimación: ${precio:,.2f} MXN\n\nDatos detectados: {habitacion} habitaciones | Zona: {zona or 'no detectada'} | Amenidades: {amenidades}\nSuperficie: {superficie} | Tipo orientativo: {categoria}\n\n{explicacion}\n\nLa categoría por m² es una sugerencia mientras falten datos; el precio lo calcula el modelo entrenado.")
        except ValueError as error:
            messagebox.showwarning("Dato faltante", str(error))


if __name__ == "__main__":
    raiz = tk.Tk()
    InterfazPredicciones(raiz)
    raiz.mainloop()
