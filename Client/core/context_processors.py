"""Datos de sesión disponibles en todas las plantillas.

Sirve para que el topbar y los sidebars puedan mostrar quién está dentro y con
qué rol sin que cada vista de cada panel tenga que acordarse de pasarlo.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

from .roles import nombre_rol


def sesion(request):
    return {
        'sesion_usuario': request.session.get('usuario'),
        'sesion_nombre': request.session.get('nombre'),
        'sesion_rol': request.session.get('rol'),
        'sesion_rol_nombre': nombre_rol(request.session.get('rol')),
    }
