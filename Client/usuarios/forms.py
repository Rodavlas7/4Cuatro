"""Catálogos que llenan los selects de los formularios de personal."""

from core.api import get, headers_token, lista, url
import unicodedata
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()

def get_choices_lineas(token):
    """Líneas activas."""
    lineas = lista(get(url('lineas/lineas/activas/'), headers_token(token)))

    return [(l["codigo"], l["nombre"]) for l in lineas]

def get_choices_estaciones(token, linea_id=None, rol_codigo=None):
    """Estaciones activas filtradas por línea y rol."""

    # Administrador y supervisor no tienen estación
    if rol_codigo in {"ADMIN", "SUPER"}:
        return []

    if not linea_id:
        return []

    params = {"linea": linea_id}

    estaciones = lista(
        get(
            url('lineas/lineas/estaciones/'),
            headers_token(token),
            params=params
        )
    )

    estaciones = [
        e for e in estaciones
        if e.get("activo") is True
    ]


    # Filtros según rol
    # Filtros según rol
    if rol_codigo == "OPCALI":

        estaciones = [
            e for e in estaciones
            if "inspeccion" in normalizar(e.get("descripcion", ""))
        ]

    elif rol_codigo == "OPEMBA":

        estaciones = [
            e for e in estaciones
            if "embalaje" in normalizar(e.get("descripcion", ""))
        ]

    elif rol_codigo == "OPENSA":

        estaciones = [
            e for e in estaciones
            if "ensamblaje" in normalizar(e.get("descripcion", ""))
        ]


    return [
        (e["codigo"], e["nombre"])
        for e in estaciones
    ]
    
    

def get_choices_roles(token):
    roles = lista(get(url('usuarios/Rol/Listar/'), headers_token(token)))

    return [(r["codigo"], r["nombre"]) for r in roles]


def get_choices_turnos(token):
    turnos = lista(get(url('usuarios/Turno/Listar/'), headers_token(token)))

    return [(t["codigo"], t["nombre"]) for t in turnos]
