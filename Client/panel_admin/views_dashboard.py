"""Dashboard del panel de administrador.

Junta lo que devuelven los endpoints /api/dashboard/ y lo deja listo para que la
plantilla sólo pinte. Aquí NO se cuenta nada: los conteos ya vienen hechos por
las vistas SQL (DB/vistas.sql). Lo que sí se hace aquí es lo que es decisión de
pantalla y no de base:

  - el rango de fechas que se ofrece (hoy / 7 / 30 días / todo),
  - el umbral a partir del cual el material se considera bajo,
  - rellenar los días sin movimiento para que la gráfica no mienta,
  - y calcular los anchos de las barras, que son puro CSS.

Si la API está apagada, todo cae en ceros y listas vacías en lugar de tronar:
los helpers de core.api ya devuelven [] o {} cuando algo falla.
"""

from datetime import date, timedelta

from django.views import generic
from django.shortcuts import render

from core.api import headers, lista, objeto, url
from core.api import get as api_get
from core.guards import RolRequeridoMixin
from core.roles import ROL_ADMIN


# Rangos que ofrece el selector. La llave es lo que viaja en ?rango=.
#
# El default es 30 y no 7 a propósito: con la base de pruebas cargada, los
# movimientos más recientes son de julio de 2026, y una ventana de 7 días
# dejaría el dashboard en blanco el día que alguien lo abra en agosto.
RANGOS = {
    'hoy':  ('Hoy', 0),
    '7':    ('Últimos 7 días', 6),
    '30':   ('Últimos 30 días', 29),
    'todo': ('Todo el histórico', None),
}

RANGO_POR_DEFECTO = '30'

# Piezas disponibles a partir de las cuales un modelo de componente se considera
# bajo. Es un número de pantalla, no de negocio: si mañana se decide que son 25,
# se cambia aquí y ya.
UMBRAL_STOCK = 10

# Cuántos eventos se enseñan en la línea de tiempo.
EVENTOS = 12

# Cuántas barras caben cómodas en la gráfica de producción sin volverse ilegibles.
MAX_BARRAS = 30


def _rango(clave):
    """Traduce la clave del selector a (desde, hasta, etiqueta).

    'todo' devuelve desde = None, que para la API significa sin límite por ese
    lado. Una clave desconocida cae en el default en lugar de fallar."""
    if clave not in RANGOS:
        clave = RANGO_POR_DEFECTO

    etiqueta, dias = RANGOS[clave]
    hasta = date.today()

    if dias is None:
        return None, hasta, etiqueta, clave

    return hasta - timedelta(days=dias), hasta, etiqueta, clave


def _params(desde, hasta):
    """Querystring del rango. Omite el lado vacío en lugar de mandarlo nulo."""
    params = {'hasta': hasta.isoformat()}

    if desde is not None:
        params['desde'] = desde.isoformat()

    return params


def _pedir(ruta, cabeceras, params=None, como=lista):
    """GET a un endpoint del dashboard, ya leído con el helper que toque."""
    return como(api_get(url(f'dashboard/{ruta}'), cabeceras, params=params))


def _suma(filas, campo):
    """Suma un campo de una lista de dicts, tratando None como 0.

    La API puede mandar null en una columna agregada si la vista no encontró
    nada que sumar, y sum() no sabe sumar None."""
    return sum((fila.get(campo) or 0) for fila in filas)


def _por_dia(filas, campos):
    """Colapsa las filas por fecha, sumando los campos pedidos.

    Las vistas vienen abiertas por línea y modelo, y la gráfica de tendencia las
    quiere por día nada más."""
    dias = {}

    for fila in filas:
        fecha = fila.get('fecha')

        if not fecha:
            continue

        dia = dias.setdefault(fecha, {campo: 0 for campo in campos})

        for campo in campos:
            dia[campo] += fila.get(campo) or 0

    return dias


def _serie(filas, campos, desde, hasta):
    """Arma la serie de la gráfica, un punto por día, con los huecos en cero.

    Rellenar los días vacíos importa: si sólo se pintaran los días con
    movimiento, tres días sueltos se verían como tres días seguidos de
    producción constante, que es exactamente lo contrario de lo que pasó.

    Cuando el rango es 'todo' no hay un inicio con el cual rellenar, así que se
    toma el primer día que tenga datos."""
    dias = _por_dia(filas, campos)

    if desde is None:
        if not dias:
            return []
        desde = date.fromisoformat(min(dias))

    # Un rango largo con datos ralos daría cientos de barras de un pixel. Se
    # recorta al final, que es la parte que le interesa a quien mira.
    total_dias = (hasta - desde).days + 1

    if total_dias > MAX_BARRAS:
        desde = hasta - timedelta(days=MAX_BARRAS - 1)
        total_dias = MAX_BARRAS

    serie = []

    for indice in range(total_dias):
        dia = desde + timedelta(days=indice)
        valores = dias.get(dia.isoformat(), {})

        punto = {'fecha': dia}
        punto.update({campo: valores.get(campo, 0) for campo in campos})
        serie.append(punto)

    return serie


def _con_altura(serie, campo):
    """Le agrega a cada punto su altura en porcentaje, para el CSS.

    El alto de la barra se calcula aquí y no en la plantilla porque el lenguaje
    de plantillas de Django no divide. La barra del día más alto mide 100% y las
    demás se miden contra ella; si todo el rango está en cero, todas quedan en
    cero y la gráfica se ve plana, que es la verdad."""
    tope = max([punto[campo] for punto in serie], default=0)

    for punto in serie:
        punto['altura'] = round(100 * punto[campo] / tope) if tope else 0

    return serie


def _porcentaje(parte, total):
    """Porcentaje entero, o None si no hay de dónde sacarlo.

    None y 0 no son lo mismo: 0% es "se rechazó todo" y None es "todavía no se
    ha inspeccionado nada". La plantilla los pinta distinto."""
    if not total:
        return None

    return round(100 * parte / total)


def _ranking(filas, etiqueta, campo, limite=5):
    """Ordena filas por un campo y les pone su ancho de barra en porcentaje.

    Sirve para las dos gráficas horizontales: rechazos por línea y paros por
    línea. Devuelve sólo las que tienen algo que enseñar."""
    agrupado = {}

    for fila in filas:
        nombre = fila.get(etiqueta) or 'Sin línea'
        agrupado[nombre] = agrupado.get(nombre, 0) + (fila.get(campo) or 0)

    barras = [{'nombre': n, 'valor': v} for n, v in agrupado.items() if v]
    barras.sort(key=lambda b: b['valor'], reverse=True)
    barras = barras[:limite]

    tope = max([b['valor'] for b in barras], default=0)

    for barra in barras:
        barra['ancho'] = round(100 * barra['valor'] / tope) if tope else 0

    return barras


class Dashboard(RolRequeridoMixin, generic.View):
    """Portada del panel de administrador, con las estadísticas de la planta."""

    roles_permitidos = (ROL_ADMIN,)
    template_name = 'panel_admin/dashboard.html'

    def get(self, request):
        cabeceras = headers(request)

        desde, hasta, etiqueta, clave = _rango(request.GET.get('rango'))
        params = _params(desde, hasta)

        # --- lo que trae la API -------------------------------------------
        resumen = _pedir('resumen/', cabeceras, como=objeto)
        produccion = _pedir('produccion/', cabeceras, params)
        calidad = _pedir('calidad/', cabeceras, params)
        paros = _pedir('paros/', cabeceras, params)
        stock = _pedir('stock/', cabeceras, {'umbral': UMBRAL_STOCK})
        actividad = _pedir('actividad/', cabeceras, {'limite': EVENTOS})
        paros_abiertos = _pedir('paros-abiertos/', cabeceras)
        rechazos = _pedir('rechazos/', cabeceras, params)

        # --- totales del rango --------------------------------------------
        producidas = _suma(produccion, 'total')
        inspecciones = _suma(calidad, 'total')
        aprobadas = _suma(calidad, 'aprobadas')
        rechazadas = _suma(calidad, 'rechazadas')
        paros_total = _suma(paros, 'total')
        paros_minutos = _suma(paros, 'minutos')

        # --- si la API no contestó nada de nada ---------------------------
        # Un dashboard en ceros y un dashboard desconectado se ven igual, y no
        # son lo mismo. `resumen` siempre trae algo cuando la API responde, así
        # que su vacío es la señal de que no hubo respuesta.
        sin_api = not resumen

        contexto = {
            # Selector de rango
            'rangos': [{'clave': c, 'etiqueta': e} for c, (e, _) in RANGOS.items()],
            'rango': clave,
            'rango_etiqueta': etiqueta,
            'rango_desde': desde,
            'rango_hasta': hasta,

            'sin_api': sin_api,

            # Foto de la planta
            'resumen': resumen,

            # Tarjetas del rango
            'producidas': producidas,
            'inspecciones': inspecciones,
            'aprobadas': aprobadas,
            'rechazadas': rechazadas,
            'aprobacion': _porcentaje(aprobadas, inspecciones),
            'paros_total': paros_total,
            'paros_minutos': paros_minutos,
            'paros_horas': round(paros_minutos / 60, 1) if paros_minutos else 0,

            # Gráficas
            'serie_produccion': _con_altura(_serie(produccion, ['total'], desde, hasta), 'total'),
            'rechazos_por_linea': _ranking(calidad, 'linea_nombre', 'rechazadas'),
            'paros_por_linea': _ranking(paros, 'linea_nombre', 'total'),

            # Alertas
            'paros_abiertos': paros_abiertos,
            'rechazos': rechazos,
            'stock_bajo': stock,
            'umbral_stock': UMBRAL_STOCK,

            # Actividad
            'actividad': actividad,
        }

        return render(request, self.template_name, contexto)
