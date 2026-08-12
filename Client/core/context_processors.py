"""Datos de sesión disponibles en todas las plantillas.

Sirve para que el topbar y los sidebars puedan mostrar quién está dentro y con
qué rol sin que cada vista de cada panel tenga que acordarse de pasarlo.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

from .lineas import de_la_sesion, todas_de_la_sesion
from .roles import nombre_rol, ROL_SUPERVISOR


def sesion(request):
    return {
        'sesion_usuario': request.session.get('usuario'),
        'sesion_nombre': request.session.get('nombre'),
        'sesion_rol': request.session.get('rol'),
        'sesion_rol_nombre': nombre_rol(request.session.get('rol')),
    }


def linea_del_supervisor(request):
    """Con cuál de sus líneas trabaja el supervisor, y cuáles más tiene.

    Lo usa el selector de su menú. Un supervisor puede tener varias líneas a su
    cargo (empleado_linea es M a M) pero las pantallas muestran una a la vez.

    Sólo se resuelve para el rol SUPER: es el único panel con selector, y esto
    cuesta una llamada a la API, así que no se le cobra a los otros dos."""

    if request.session.get('rol') != ROL_SUPERVISOR:
        return {}

    suyas = todas_de_la_sesion(request)

    return {
        'lineas_a_mi_cargo': suyas,
        'linea_en_uso': de_la_sesion(request, suyas),
    }
