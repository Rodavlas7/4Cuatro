"""Catálogos que llenan los selects de los formularios de producción.

Versión del panel de administrador.
"""

from core.api import get, headers_token, lista, url


def get_choices_lineas_paro(token):
    """Líneas activas, para el formulario de paros."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [
        (l.get("codigo"), l.get("nombre"))
        for l in lineas
        if l.get("estado_codigo") == "ACTI"
    ]
