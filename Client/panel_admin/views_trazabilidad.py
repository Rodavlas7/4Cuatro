"""Trazabilidad por orden de producción, para el panel de administrador.

Contesta una sola pregunta: "cuéntame todo lo que le pasó al folio N". La API lo
devuelve completo en una llamada (/api/dashboard/trazabilidad/<folio>/), así que
aquí sólo se reparte en el contexto y se calculan las cosas de pantalla: los
anchos de las barras de avance y la línea de tiempo.

Es pantalla aparte y no un pedazo de produccion/detalle_orden.html a propósito:
esa pantalla es la operativa y la comparten el admin y el supervisor, mientras
que ésta es de consulta y sólo del admin.
"""

from django.views import generic
from django.shortcuts import render

from core.api import headers, lista, objeto, url
from core.api import get as api_get
from core.guards import RolRequeridoMixin
from core.roles import ROL_ADMIN


# Resultado de la última inspección de una laptop, como lo guarda la base
# (inspeccion_calidad.resultado). Se traduce aquí para que la plantilla no tenga
# que saber de números.
RESULTADOS = {
    1: ('Aprobada', 'ok'),
    0: ('Rechazada', 'mal'),
    2: ('Continuar', 'medio'),
}


# Cuántas órdenes se ofrecen en el buscador. Son las más recientes: quien busca
# una vieja escribe el folio.
ORDENES_SUGERIDAS = 15


def _resultado(valor):
    """Traduce el resultado de la última inspección a (texto, clase de estilo).

    None significa que la laptop nunca pasó por calidad, que no es lo mismo que
    haber salido mal."""
    return RESULTADOS.get(valor, ('Sin inspección', 'neutro'))


def _laptops(filas):
    """Prepara las laptops para la tabla: traduce el resultado de calidad."""
    for fila in filas:
        texto, clase = _resultado(fila.get('ultimo_resultado'))
        fila['resultado_texto'] = texto
        fila['resultado_clase'] = clase

    return filas


def _componentes(filas):
    """Le pone a cada renglón de material su ancho de barra en porcentaje.

    El ancho se mide contra el modelo más consumido de la orden, para que se vea
    de un golpe qué componente es el que más se gastó."""
    tope = max([(f.get('piezas') or 0) for f in filas], default=0)

    for fila in filas:
        piezas = fila.get('piezas') or 0
        fila['ancho'] = round(100 * piezas / tope) if tope else 0

    return filas


def _avance(orden):
    """Reparte el avance de la orden en los tramos de la barra apilada.

    Se mide contra lo planificado, no contra las laptops registradas: lo que le
    importa al admin es cuánto falta para cerrar la orden. Si ya se registraron
    más laptops que las planificadas (pasa cuando se reemplazan rechazadas), los
    tramos se recortan para no desbordar la barra."""
    planificada = orden.get('cant_planificada') or 0

    if not planificada:
        return []

    tramos = [
        ('Embaladas', 'embaladas', orden.get('laptops_embaladas') or 0),
        ('Aprobadas', 'aprobadas', orden.get('laptops_aprobadas') or 0),
        ('En ensamblaje', 'proceso', orden.get('laptops_en_ensamblaje') or 0),
        ('Rechazadas', 'rechazadas', orden.get('laptops_rechazadas') or 0),
    ]

    barra = []
    acumulado = 0

    for etiqueta, clase, cantidad in tramos:
        if not cantidad:
            continue

        # Lo que quepa en lo que resta de la barra.
        ancho = min(round(100 * cantidad / planificada), max(0, 100 - acumulado))

        if not ancho:
            continue

        barra.append({'etiqueta': etiqueta, 'clase': clase,
                      'cantidad': cantidad, 'ancho': ancho})
        acumulado += ancho

    return barra


class TrazabilidadOrden(RolRequeridoMixin, generic.View):
    """Buscador de folio y, cuando hay uno, la trazabilidad completa."""

    roles_permitidos = (ROL_ADMIN,)
    template_name = 'panel_admin/trazabilidad_orden.html'

    def get(self, request, folio=None):
        cabeceras = headers(request)

        # El folio puede venir por la URL (/trazabilidad/2/) o por el buscador
        # (?folio=2). Se acepta cualquiera de los dos para que el formulario
        # funcione con un GET simple, sin JavaScript.
        if folio is None:
            escrito = (request.GET.get('folio') or '').strip()
            folio = int(escrito) if escrito.isdigit() else None

        contexto = {
            'folio': folio,
            'ordenes': lista(api_get(url('dashboard/trazabilidad/'), cabeceras))[:ORDENES_SUGERIDAS],
        }

        if folio is None:
            return render(request, self.template_name, contexto)

        respuesta = api_get(url(f'dashboard/trazabilidad/{folio}/'), cabeceras)
        datos = objeto(respuesta)

        if not datos:
            # Folio que no existe, o API caída. Se distingue por el status para
            # no acusar al usuario de escribir mal cuando el problema es otro.
            contexto['error'] = (
                f'No existe la orden con folio {folio}.'
                if respuesta is not None and respuesta.status_code == 404
                else 'No se pudo consultar la trazabilidad en este momento.'
            )
            return render(request, self.template_name, contexto)

        orden = datos.get('orden') or {}

        contexto.update({
            'orden': orden,
            'laptops': _laptops(datos.get('laptops') or []),
            'componentes': _componentes(datos.get('componentes') or []),
            'paros': datos.get('paros') or [],
            'avance': _avance(orden),
        })

        return render(request, self.template_name, contexto)
