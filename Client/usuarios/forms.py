"""Catálogos que llenan los selects de los formularios de personal."""

from core.api import get, headers_token, lista, url


def get_choices_lineas(token):
    """Líneas activas."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [(l["codigo"], l["nombre"]) for l in lineas]


def get_choices_estaciones(token, linea_id=None):
    """Estaciones activas; si se pasa `linea_id`, sólo las de esa línea."""
    params = {"linea": linea_id} if linea_id else None

    estaciones = lista(
        get(url('lineas/lineas/estaciones/'), headers_token(token), params=params)
    )

    return [
        (e["codigo"], e["nombre"])
        for e in estaciones
        if e.get("activo") is True
    ]


def get_choices_roles(token):
    roles = lista(get(url('usuarios/Rol/Listar/'), headers_token(token)))

    return [(r["codigo"], r["nombre"]) for r in roles]


def get_choices_turnos(token):
    turnos = lista(get(url('usuarios/Turno/Listar/'), headers_token(token)))

    return [(t["codigo"], t["nombre"]) for t in turnos]
