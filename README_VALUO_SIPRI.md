# VALUO SIPRI

MVP web de SIPCO para elaborar Opiniones de Valor preliminares, con captura de inmueble, fotografías, zonas, equipamiento y comparables.

## Ejecutar localmente

```powershell
.\.venv\Scripts\python.exe -m uvicorn valuo_sipri.app:app --reload
```

Abrir `http://127.0.0.1:8000`. La base SQLite y los archivos generados se guardan en `valuo_sipri/runtime_data/` y no deben subirse a Git.

## Método de esta versión

El motor `sipri-explicable-v0.1-demo` selecciona hasta tres comparables por cercanía geográfica, superficie y recámaras. Pondera su precio por m2 y aplica ajustes explícitos por calidad, amenidades y antigüedad. El resultado siempre lleva un rango y un estado de confianza.

Los datos iniciales de SLP son **demostrativos**. No son registros de mercado verificados ni deben utilizarse para emitir una opinión comercial sin revisión.

## Modelo entrenado y Render

La aplicación no reentrena al atender solicitudes. El flujo recomendado es:

1. La actualización de datos y el entrenamiento se ejecutan en una rama/proceso controlado.
2. Solo se publica un modelo si sus métricas superan criterios definidos.
3. Se etiqueta el artefacto con una versión y se configura la aplicación para cargar esa versión.
4. El PDF conserva la versión para mantener trazabilidad y permitir reversión.

La configuración actual usa Render Free: la base PostgreSQL gratuita conserva las opiniones durante su periodo gratuito, pero los archivos locales (fotografías y PDFs) se eliminan al reiniciar, redeplegar o suspender el servicio. Antes de uso comercial se debe incorporar almacenamiento de objetos para fotos/PDFs y un plan persistente.

## Despliegue

1. Crear un repositorio privado en GitHub y subir el proyecto, excluyendo `.venv`, `runtime_data`, bases SQLite y archivos de usuario.
2. En Render seleccionar **New > Blueprint**, conectar el repositorio y aprobar el `render.yaml`. Seleccionar las instancias Free.
3. Verificar la URL `/health` y realizar una opinión de prueba.
4. Configurar protección de rama para que Render despliegue después del trabajo `Quality and deploy gate`.

## Límites importantes

- No se presenta como avalúo formal.
- La aprobación y firma profesional son pasos separados del cálculo.
- Los comparables demostrativos deben reemplazarse por datos verificables y con fuente/fecha.
- Las coordenadas de zonas y equipamientos deben revisarse y versionarse antes de producción.
