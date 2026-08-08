"""Lo compartido sobre líneas: su tipo y la del empleado que inició sesión.

El TIPO de la línea (ensamblaje o embalaje) decide dónde se puede registrar
ensamblaje. Aquí abajo están la constante y el filtro que usan los formularios;
la regla de verdad la imponen la API y el trigger tg_Validar_Linea_Ensamblaje.

Lo demás de este archivo resuelve la otra pregunta:

La línea a la que está asignado el empleado que inició sesión.

El panel de supervisor la necesita para no mostrarle material de otras líneas y
para llenar el campo 'linea' por él, en vez de dejárselo elegir.

De dónde sale: de empleado_linea, la tabla que dice en qué línea está cada
empleado. Se leen sólo las asignaciones vigentes (fecha_fin nula), que es lo que
ya devuelve ese endpoint.

Por qué de ahí y no del catálogo /api/lineas/: porque el rol SUPER no tiene
permiso del módulo 'lineas' (ver PERMISOS_ROL en Servicios), así que a un
supervisor ese catálogo le responde 403. El endpoint de empleado_linea ya trae
el nombre de la línea junto con su código, y con eso basta.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

from core.api import get, headers, lista, url


# Tipos de línea (catálogo tipo_linea, ver DB/datos.sql). El tipo dice qué
# proceso corre la línea; no confundir con el estado (activa, en paro...).
TIPO_ENSAMBLAJE = 'ENSA'
TIPO_EMBALAJE = 'EMBA'


def es_de_ensamblaje(linea):
    """True si en esa línea se puede registrar ensamblaje.

    `linea` es un renglón de /api/lineas/, que lee de vista_lineas y por eso
    trae el tipo ya resuelto en 'tipo_codigo'."""
    return isinstance(linea, dict) and linea.get('tipo_codigo') == TIPO_ENSAMBLAJE


def solo_de_ensamblaje(lineas):
    """Filtra un catálogo de líneas a las de ensamblaje.

    Se usa para llenar los selects de los formularios de ensamblaje: la API y el
    trigger tg_Validar_Linea_Ensamblaje ya rechazan una línea de embalaje, pero
    ofrecerla en la lista sólo sirve para que el operador se lleve el error."""
    return [l for l in (lineas or []) if es_de_ensamblaje(l)]


def de_la_sesion(request):
    """La línea del empleado de la sesión como {'codigo', 'nombre'}, o None.

    A propósito NO se guarda en la sesión: si a alguien lo cambian de línea, con
    caché seguiría viendo la anterior hasta volver a entrar, y aquí de eso
    depende qué material alcanza a ver. Una llamada más a la API sale más barata
    que enseñar la línea equivocada."""

    empleado = request.session.get('empleado')
    if not empleado:
        return None

    asignaciones = lista(get(url('usuarios/Empleado/Linea/Buscar/'), headers(request)))

    for asignacion in asignaciones:
        if asignacion.get('empleado_numero') == empleado:
            codigo = asignacion.get('linea_codigo')
            if not codigo:
                continue
            return {
                'codigo': codigo,
                # Si por lo que sea viniera sin nombre, el código se lee mejor
                # que un hueco.
                'nombre': asignacion.get('linea') or codigo,
            }

    return None
