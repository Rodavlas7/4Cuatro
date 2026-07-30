"""Catálogos que llenan los selects del formulario de inspecciones.

Versión del panel de administrador.
"""

from core.api import get, headers_token, lista, url


def get_choices_laptops(token):
    """Laptops pendientes de ensamblar."""
    laptops = lista(get(url('produccion/laptops/'), headers_token(token)))

    return [
        (l["numero"], f"{l['numero']} - {l.get('num_serie', '')} ({l.get('modelo_nombre', '')})")
        for l in laptops
        if l.get("estado_codigo") == "PENSAM"
    ]


def get_choices_lineas_produccion(token):
    """Líneas activas."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [(l.get("codigo"), l.get("nombre")) for l in lineas]
