"""
Índice / landing de la API de Servicios.

Flujo web:
  - url /            -> formulario de login (copiado del cliente).
  - al iniciar sesión guarda el token en una cookie y redirige al índice.
  - url /index/      -> índice de endpoints (requiere haber iniciado sesión).
El token vive en una cookie de host (TOKEN_COOKIE) en vez de en la sesión de
Django: como las cookies no distinguen puerto, la que pone el cliente en :8001
llega hasta la API en :8000, así que iniciar sesión en el cliente basta para
navegar la API sin pegar el Bearer a mano (ver usuarios/authentication.py).
"""
import requests
from django.shortcuts import render, redirect
from django.utils import timezone

from usuarios.authentication import TOKEN_COOKIE
from usuarios.models import Sesion

# El token dura 10 horas (ver LoginAPIView); la cookie vence a la par.
TOKEN_COOKIE_MAX_AGE = 10 * 60 * 60


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
            {"metodos": ["GET"], "ruta": "Empleado/Buscar/", "desc": "Busca empleados con ?buscar=<texto>."},
            {"metodos": ["GET"], "ruta": "Usuario/Buscar/", "desc": "Busca cuentas de usuario con ?buscar=<texto>."},
            {"metodos": ["GET"], "ruta": "Empleado/Linea/Buscar/", "desc": "Busca empleados por línea asignada."},
            {"metodos": ["GET"], "ruta": "Empleado/Estacion/Buscar/", "desc": "Busca empleados por estación asignada."},
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
    {
        "nombre": "Calidad",
        "base": "/api/calidad/",
        "descripcion": "Inspecciones de calidad de las laptops.",
        "endpoints": [
            {"metodos": ["POST"], "ruta": "Inspeccion/Registrar/", "desc": "Registra una nueva inspección de calidad."},
            {"metodos": ["GET"], "ruta": "Inspeccion/Listar/", "desc": "Lista todas las inspecciones (vista SQL)."},
            {"metodos": ["GET"], "ruta": "Inspeccion/Detalle/<numero>/", "desc": "Detalle de una inspección."},
            {"metodos": ["PUT", "PATCH"], "ruta": "Inspeccion/Actualizar/<numero>/", "desc": "Actualiza una inspección."},
            {"metodos": ["DELETE"], "ruta": "Inspeccion/Eliminar/<numero>/", "desc": "Elimina una inspección."},
            {"metodos": ["GET"], "ruta": "Inspeccion/Buscar/", "desc": "Busca inspecciones con ?buscar=<texto>."},
        ],
    },
    {
        "nombre": "Embalaje",
        "base": "/api/embalaje/",
        "descripcion": "Registros de embalaje de las laptops terminadas.",
        "endpoints": [
            {"metodos": ["POST"], "ruta": "Embalaje/Registrar/", "desc": "Registra un nuevo embalaje."},
            {"metodos": ["GET"], "ruta": "Embalaje/Listar/", "desc": "Lista todos los registros de embalaje (vista SQL)."},
            {"metodos": ["GET"], "ruta": "Embalaje/Detalle/<numero>/", "desc": "Detalle de un registro de embalaje."},
            {"metodos": ["PUT", "PATCH"], "ruta": "Embalaje/Actualizar/<numero>/", "desc": "Actualiza un registro de embalaje."},
            {"metodos": ["DELETE"], "ruta": "Embalaje/Eliminar/<numero>/", "desc": "Elimina un registro de embalaje."},
            {"metodos": ["GET"], "ruta": "Embalaje/Buscar/", "desc": "Busca registros de embalaje con ?buscar=<texto>."},
        ],
    },
]


def _sesion_activa(request):
    """Sesión (fila de la tabla sesion) que corresponde al token de la cookie,
    o None si no hay cookie, el token no existe o ya venció. Sirve tanto para
    el login hecho aquí como para el hecho en el cliente."""
    token = request.COOKIES.get(TOKEN_COOKIE)
    if not token:
        return None

    sesion = Sesion.objects.filter(token=token).first()
    if sesion is None or sesion.fecha_expiracion < timezone.now():
        return None

    return sesion


def login_view(request):
    """Formulario de login en la raíz (/). Copiado del cliente: envía las
    credenciales al endpoint de login de la API, guarda el token en la cookie
    compartida y redirige al índice."""
    # Si ya hay sesión iniciada (aquí o en el cliente), directo al índice.
    if _sesion_activa(request):
        return redirect("api-index")

    if request.method == "POST":
        usuario = request.POST.get("usuario")
        contrasena = request.POST.get("contrasena")
        try:
            respuesta = requests.post(
                request.build_absolute_uri("/api/usuarios/login/"),
                json={"usuario": usuario, "contrasena": contrasena},
                timeout=5,
            )
            datos = respuesta.json()
        except requests.RequestException:
            return render(request, "login.html",
                          {"error": "No se pudo conectar con la API."})

        if respuesta.status_code == 200:
            respuesta_http = redirect("api-index")
            respuesta_http.set_cookie(
                TOKEN_COOKIE,
                datos.get("token"),
                max_age=TOKEN_COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
            )
            return respuesta_http

        return render(request, "login.html",
                      {"error": datos.get("mensaje", "Credenciales inválidas.")})

    return render(request, "login.html")


def logout_view(request):
    """Cierra la sesión web (aquí y en el cliente, porque la cookie es la
    misma) y vuelve al login."""
    respuesta_http = redirect("/")
    respuesta_http.delete_cookie(TOKEN_COOKIE)
    return respuesta_http


def _render_index(request, sesion, *, status=200, not_found=False):
    """Renderiza el índice de endpoints. Reutilizado por el índice y por el 404.
    Los datos del usuario salen de la sesión de la BD, no de la sesión de
    Django, para que funcione igual si el login se hizo en el cliente."""
    total_endpoints = sum(len(m["endpoints"]) for m in API_MODULES)
    empleado = getattr(sesion.usuario, "empleado", None)
    rol = empleado.rol.codigo if empleado and empleado.rol else None
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
            "usuario": sesion.usuario.usuario,
            "rol": rol,
            "token": sesion.token,
        },
        status=status,
    )


def api_index(request):
    """Índice de endpoints. Requiere haber iniciado sesión, aquí o en el cliente."""
    sesion = _sesion_activa(request)
    if sesion is None:
        return redirect("/")
    return _render_index(request, sesion)


def not_found(request, unknown=None):
    """Cualquier URL inexistente lleva al índice con un aviso (estado 404).
    Si no hay sesión, primero manda al login."""
    sesion = _sesion_activa(request)
    if sesion is None:
        return redirect("/")
    return _render_index(request, sesion, status=404, not_found=True)
