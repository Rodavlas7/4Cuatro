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

PUEDEN SER VARIAS. empleado_linea es M a M: al supervisor el administrador le
puede asignar más de una línea desde el detalle de cada línea. Como las
pantallas trabajan una sola a la vez, el supervisor elige cuál con el selector
de su panel y la elegida se guarda en la sesión; `de_la_sesion` devuelve ésa. Si
no ha elegido —o si le quitaron la que traía elegida— se le devuelve la primera
de las suyas, para que nunca se quede sin nada que ver.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

from core.api import get, headers, lista, url


# Dónde se guarda el código de la línea que el empleado eligió. Se guarda sólo
# el código, no el renglón entero: el nombre y lo demás se vuelven a leer de la
# API en cada pantalla, así que un cambio de nombre no se queda pegado.
CLAVE_SESION = 'linea_elegida'


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


def todas_de_la_sesion(request):
    """Todas las líneas vigentes del empleado, como [{'codigo', 'nombre'}, ...].

    A propósito NO se guardan en la sesión: si a alguien lo cambian de línea, con
    caché seguiría viendo la anterior hasta volver a entrar, y aquí de eso
    depende qué material alcanza a ver. Una llamada más a la API sale más barata
    que enseñar la línea equivocada."""

    empleado = request.session.get('empleado')
    if not empleado:
        return []

    asignaciones = lista(get(url('usuarios/Empleado/Linea/Buscar/'), headers(request)))

    suyas = []

    for asignacion in asignaciones:
        if asignacion.get('empleado_numero') != empleado:
            continue

        codigo = asignacion.get('linea_codigo')
        if not codigo:
            continue

        suyas.append({
            'codigo': codigo,
            # Si por lo que sea viniera sin nombre, el código se lee mejor
            # que un hueco.
            'nombre': asignacion.get('linea') or codigo,
        })

    return suyas


def de_la_sesion(request, suyas=None):
    """La línea con la que está trabajando el empleado, o None si no tiene.

    Es la que eligió en el selector de su panel. Si no ha elegido, o si la que
    tenía elegida ya no es suya —se la quitaron mientras estaba dentro—, se
    devuelve la primera de las suyas en lugar de dejarlo sin nada.

    `suyas` es para quien ya tiene la lista en la mano (el menú del supervisor,
    que enseña las dos cosas) y así no la pide dos veces a la API."""

    if suyas is None:
        suyas = todas_de_la_sesion(request)

    if not suyas:
        return None

    elegida = request.session.get(CLAVE_SESION)

    for linea in suyas:
        if linea['codigo'] == elegida:
            return linea

    return suyas[0]


def elegir(request, codigo):
    """Deja esa línea como la activa de la sesión. True si se pudo.

    Se comprueba contra las líneas del empleado antes de guardarla: si no se
    comprobara, cualquiera podría mandar el código de una línea ajena en el
    formulario y ponerse a ver material que no le toca."""

    for linea in todas_de_la_sesion(request):
        if linea['codigo'] == codigo:
            request.session[CLAVE_SESION] = codigo
            return True

    return False
