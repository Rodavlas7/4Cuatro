"""
Índice / landing de la API de Servicios.

Vista pública (no DRF, sin autenticación) que se sirve en la raíz del backend
para que quien consuma la API pueda ver, desde el mismo host, todos los
endpoints ya establecidos con una descripción corta de cada uno.
"""
from django.shortcuts import render


# Inventario de endpoints agrupados por módulo (base = prefijo del include en urls.py).
# Cada endpoint: metodos, ruta (relativa a la base del módulo) y descripción corta.
API_MODULES = [
    {
        "nombre": "Usuarios y autenticación",
        "base": "/api/usuarios/",
        "descripcion": "Inicio de sesión y gestión de empleados y cuentas de usuario.",
        "endpoints": [
            {"metodos": ["POST"], "ruta": "login/", "desc": "Autentica usuario y contraseña; devuelve el token de acceso."},
            {"metodos": ["POST"], "ruta": "Empleado/Registrar/", "desc": "Registra un nuevo empleado."},
            {"metodos": ["GET"], "ruta": "Empleado/Listar/", "desc": "Lista todos los empleados."},
            {"metodos": ["GET"], "ruta": "Empleado/Detalle/<numero>/", "desc": "Detalle de un empleado por su número."},
            {"metodos": ["PUT", "PATCH"], "ruta": "Empleado/Actualizar/<numero>/", "desc": "Actualiza los datos de un empleado."},
            {"metodos": ["PATCH"], "ruta": "Empleado/Desactivar/<numero>/", "desc": "Da de baja (desactiva) a un empleado."},
            {"metodos": ["POST"], "ruta": "Usuario/Registrar/", "desc": "Crea una cuenta de usuario para un empleado."},
            {"metodos": ["GET"], "ruta": "Usuario/Listar/", "desc": "Lista todas las cuentas de usuario."},
            {"metodos": ["GET"], "ruta": "Usuario/Detalle/<numero>/", "desc": "Detalle de una cuenta de usuario."},
            {"metodos": ["PUT"], "ruta": "Usuario/Actualizar/<numero>/", "desc": "Actualiza una cuenta de usuario."},
            {"metodos": ["PATCH"], "ruta": "Usuario/Desactivar/<numero>/", "desc": "Desactiva una cuenta de usuario."},
            {"metodos": ["PATCH"], "ruta": "Usuario/Reactivar/<numero>/", "desc": "Reactiva una cuenta de usuario dada de baja."},
        ],
    },
    {
        "nombre": "Líneas y estaciones",
        "base": "/api/lineas/",
        "descripcion": "Líneas de producción, sus estados y las estaciones que las componen.",
        "endpoints": [
            {"metodos": ["GET", "POST"], "ruta": "", "desc": "Consulta general de líneas (vista SQL) y alta de una nueva línea."},
            {"metodos": ["GET"], "ruta": "estados/", "desc": "Catálogo de estados de línea."},
            {"metodos": ["GET", "POST"], "ruta": "estaciones/", "desc": "Consulta general de estaciones y alta de una nueva."},
            {"metodos": ["GET"], "ruta": "estaciones/<codigo>/", "desc": "Detalle de una estación."},
            {"metodos": ["PUT", "DELETE"], "ruta": "estaciones/mod/<codigo>/", "desc": "Modifica una estación; DELETE la desactiva."},
            {"metodos": ["GET"], "ruta": "<codigo>/", "desc": "Detalle de una línea con sus estaciones anidadas."},
            {"metodos": ["PUT", "DELETE"], "ruta": "mod/<codigo>/", "desc": "Modifica una línea; DELETE la desactiva."},
        ],
    },
    {
        "nombre": "Producción",
        "base": "/api/produccion/",
        "descripcion": "Órdenes de producción, modelos, lotes, laptops, ensamblaje y paros.",
        "endpoints": [
            {"metodos": ["GET", "POST"], "ruta": "", "desc": "Consulta general de órdenes de producción y alta de una nueva."},
            {"metodos": ["GET"], "ruta": "<folio>/", "desc": "Detalle de una orden de producción."},
            {"metodos": ["PUT", "DELETE"], "ruta": "mod/<folio>/", "desc": "Modifica una orden; DELETE la cancela (estado CANC)."},
            {"metodos": ["GET"], "ruta": "estados/", "desc": "Catálogo de estados de producción."},
            {"metodos": ["GET"], "ruta": "modelos/", "desc": "Lista de modelos de laptop."},
            {"metodos": ["GET"], "ruta": "modelos/<codigo>/", "desc": "Detalle de un modelo con su lista de materiales (BOM)."},
            {"metodos": ["GET"], "ruta": "estados-laptop/", "desc": "Catálogo de estados de laptop."},
            {"metodos": ["GET"], "ruta": "lotes/", "desc": "Lista de lotes de laptop."},
            {"metodos": ["GET"], "ruta": "lotes/<codigo>/", "desc": "Detalle de un lote de laptop."},
            {"metodos": ["GET", "POST"], "ruta": "laptops/", "desc": "Consulta de laptops y registro de una nueva."},
            {"metodos": ["GET"], "ruta": "laptops/<numero>/", "desc": "Detalle de una laptop."},
            {"metodos": ["PUT", "DELETE"], "ruta": "laptops/mod/<numero>/", "desc": "Modifica o elimina una laptop."},
            {"metodos": ["GET", "POST"], "ruta": "registros-ensamblaje/", "desc": "Consulta y alta de registros de ensamblaje."},
            {"metodos": ["GET"], "ruta": "registros-ensamblaje/<numero>/", "desc": "Detalle de un registro de ensamblaje."},
            {"metodos": ["PUT", "DELETE"], "ruta": "registros-ensamblaje/mod/<numero>/", "desc": "Modifica o elimina un registro de ensamblaje."},
            {"metodos": ["GET", "POST"], "ruta": "paros/", "desc": "Consulta de paros de línea y registro de uno nuevo."},
            {"metodos": ["GET"], "ruta": "paros/<numero>/", "desc": "Detalle de un paro."},
            {"metodos": ["PUT", "DELETE"], "ruta": "paros/mod/<numero>/", "desc": "Modifica o elimina un paro."},
        ],
    },
    {
        "nombre": "Componentes y materiales",
        "base": "/api/componentes/",
        "descripcion": "Componentes, lotes, modelos, compatibilidad (BOM) y órdenes de material.",
        "endpoints": [
            {"metodos": ["GET", "POST"], "ruta": "", "desc": "Consulta general de componentes y registro de uno nuevo."},
            {"metodos": ["GET"], "ruta": "<numero>/", "desc": "Detalle de un componente."},
            {"metodos": ["PUT", "DELETE"], "ruta": "mod/<numero>/", "desc": "Modifica un componente; DELETE lo marca como mermado."},
            {"metodos": ["GET"], "ruta": "tipos/", "desc": "Catálogo de tipos de componente."},
            {"metodos": ["GET"], "ruta": "estados/", "desc": "Catálogo de estados de componente."},
            {"metodos": ["GET", "POST"], "ruta": "lotes/", "desc": "Consulta y alta de lotes de componente."},
            {"metodos": ["GET"], "ruta": "lotes/<codigo>/", "desc": "Detalle de un lote de componente."},
            {"metodos": ["PUT", "DELETE"], "ruta": "lotes/mod/<codigo>/", "desc": "Modifica o elimina un lote de componente."},
            {"metodos": ["GET", "POST"], "ruta": "modelos/", "desc": "Consulta y alta de modelos de componente."},
            {"metodos": ["GET"], "ruta": "modelos/<codigo>/", "desc": "Detalle de un modelo de componente."},
            {"metodos": ["PUT", "DELETE"], "ruta": "modelos/mod/<codigo>/", "desc": "Modifica o elimina un modelo de componente."},
            {"metodos": ["GET", "POST"], "ruta": "compatibilidad/", "desc": "Lista de materiales (BOM): qué componentes lleva cada modelo de laptop."},
            {"metodos": ["PUT", "DELETE"], "ruta": "compatibilidad/mod/<modelo_laptop>/<modelo_componente>/", "desc": "Modifica o elimina un renglón del BOM."},
            {"metodos": ["GET", "POST"], "ruta": "ordenes/", "desc": "Consulta y alta de órdenes de material."},
            {"metodos": ["GET"], "ruta": "ordenes/<numero>/", "desc": "Detalle de una orden de material con sus renglones."},
            {"metodos": ["PUT", "DELETE"], "ruta": "ordenes/mod/<numero>/", "desc": "Modifica o elimina una orden de material."},
            {"metodos": ["GET", "POST"], "ruta": "detalles/", "desc": "Renglones de material; alta de un renglón en una orden."},
            {"metodos": ["PUT", "DELETE"], "ruta": "detalles/mod/<orden>/<modelo>/", "desc": "Modifica la cantidad o elimina un renglón de material."},
        ],
    },
]


def _render_index(request, *, status=200, not_found=False):
    """Renderiza el índice de endpoints. Reutilizado por la raíz y por el 404."""
    total_endpoints = sum(len(m["endpoints"]) for m in API_MODULES)
    return render(
        request,
        'api_index.html',
        {
            "base_url": request.build_absolute_uri('/').rstrip('/'),
            "modules": API_MODULES,
            "total_modules": len(API_MODULES),
            "total_endpoints": total_endpoints,
            "not_found": not_found,
            "attempted_path": request.path,
        },
        status=status,
    )


def api_index(request):
    """Índice de endpoints de la API, servido en la raíz del backend."""
    return _render_index(request)


def not_found(request, unknown=None):
    """Cualquier URL inexistente muestra el índice con un aviso (estado 404)."""
    return _render_index(request, status=404, not_found=True)
