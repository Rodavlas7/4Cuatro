"""Catálogos que llenan los selects de los formularios de este panel.

Es la copia del panel de supervisor: junta lo que en el panel de administrador
está repartido entre `produccion/forms.py` y `calidad/forms.py`. Al ser propia,
se puede filtrar distinto (por ejemplo, sólo las líneas del supervisor) sin
tocar los otros paneles.
"""

from core.api import get, headers_token, lista, url


def get_choices_lineas_paro(token):
    """Líneas activas, para el formulario de paros."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [
        (l.get('codigo'), l.get('nombre'))
        for l in lineas
        if l.get('estado_codigo') == 'ACTI'
    ]


def get_choices_lineas_produccion(token):
    """Líneas activas, para el formulario de inspecciones."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [(l.get('codigo'), l.get('nombre')) for l in lineas]


def get_choices_laptops(token):
    """Laptops pendientes de ensamblar, para el formulario de inspecciones."""
    laptops = lista(get(url('produccion/laptops/'), headers_token(token)))

    return [
        (l['numero'], f"{l['numero']} - {l.get('num_serie', '')} ({l.get('modelo_nombre', '')})")
        for l in laptops
        if l.get('estado_codigo') == 'PENSAM'
    ]
