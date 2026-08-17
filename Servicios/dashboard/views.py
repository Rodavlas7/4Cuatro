"""Endpoints del dashboard de administrador.

Todo lo de aquí es GET. No hay POST, ni PUT, ni DELETE, y no debería haberlos:
esta app lee vistas agregadas, y quien quiera escribir tiene que ir a la app
del módulo que le corresponde (produccion, calidad, componentes...).

Permisos
--------
Se usan los módulos "reportes" y "trazabilidad" de usuarios/permissions.py, que
sólo tiene el rol ADMIN. Así el dashboard queda cerrado para SUPER y OPCALI sin
inventar un permiso nuevo.

El rango de fechas
------------------
Entra por querystring (?desde=&hasta=) y se aplica como WHERE sobre la vista,
porque en MySQL una vista no recibe parámetros. Cualquiera de los dos lados
puede venir vacío y entonces ese extremo queda abierto. El formato es el ISO de
siempre, AAAA-MM-DD; si llega una fecha con otro formato se ignora en lugar de
tronar, porque un dashboard a medias es mejor que un 500.
"""

from datetime import date
from decimal import Decimal

from django.db import DatabaseError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api import procedimientos
from api.errores import mensaje_de_base
from usuarios.permissions import TienePermisoModulo

# Las dos alertas de abajo (paros abiertos y rechazos de calidad) NO tienen
# vista propia: reusan vista_paros y vista_inspeccion_calidad, que ya existían
# para las pantallas de esos módulos. Es a propósito. La alerta no necesita
# agregar nada, sólo filtrar filas que ya están resueltas, y duplicar la vista
# nada más para el dashboard sería tener dos definiciones de lo mismo que
# tarde o temprano se despegan.
from calidad.models import VistaInspeccionCalidad
from calidad.serializers import ListVistaInspeccionSerializer
from produccion.models import VistaParo
from produccion.serializers import VistaParoSerializer

from .models import *
from .serializers import *


# Cuántos eventos devuelve /actividad/ si no le piden otra cosa, y su tope duro.
# El tope existe porque vista_dash_actividad es un UNION de cinco tablas: sin
# límite, el día que la planta tenga historial de verdad, esa consulta se vuelve
# el cuello de botella del dashboard.
ACTIVIDAD_LIMITE = 15
ACTIVIDAD_LIMITE_MAX = 100


def _fecha(texto):
    """Convierte 'AAAA-MM-DD' a date, o None si viene vacío o mal escrito.

    Devolver None en lugar de reventar es a propósito: el rango es un filtro de
    comodidad, y si llega basura lo correcto es enseñar todo, no un error."""
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def _entero(texto, por_defecto, maximo=None):
    """Lee un entero de la querystring, con default y tope."""
    try:
        valor = int(texto)
    except (TypeError, ValueError):
        return por_defecto
    if valor < 0:
        return por_defecto
    if maximo is not None:
        return min(valor, maximo)
    return valor


class SoloLecturaAdmin(generics.ListAPIView):
    """Base de las listas del dashboard: sólo GET y sólo para ADMIN."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "reportes"


class SerieDiariaAPIView(SoloLecturaAdmin):
    """Base de las tres series por día.

    Las subclases ponen queryset y serializer; el filtro de rango y el orden
    son iguales para todas, porque las tres vistas exponen la columna `fecha`.
    """

    def get_queryset(self):
        queryset = self.queryset

        desde = _fecha(self.request.query_params.get('desde'))
        hasta = _fecha(self.request.query_params.get('hasta'))
        linea = self.request.query_params.get('linea')

        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        if linea:
            queryset = queryset.filter(linea_codigo=linea)

        return queryset.order_by('fecha')


# ==================================================
# S E R I E S   P O R   D Í A
# ==================================================


class ProduccionDiariaAPIView(SerieDiariaAPIView):
    """Laptops producidas (embaladas) por día, línea y modelo."""

    queryset = ProduccionDiaria.objects.all()
    serializer_class = ProduccionDiariaSerializer


class CalidadDiariaAPIView(SerieDiariaAPIView):
    """Inspecciones por día y línea, con aprobadas / rechazadas / continuar."""

    queryset = CalidadDiaria.objects.all()
    serializer_class = CalidadDiariaSerializer


class ParosDiariaAPIView(SerieDiariaAPIView):
    """Paros por día y línea, con cuántos siguen abiertos y cuántos minutos."""

    queryset = ParosDiaria.objects.all()
    serializer_class = ParosDiariaSerializer


class TiempoLineaDiariaAPIView(SerieDiariaAPIView):
    """Cuánto tarda una laptop en cada línea, por día, con los dos tiempos.

    Cae en SerieDiariaAPIView como las otras tres porque la vista expone las
    mismas columnas `fecha` y `linea_codigo` que el filtro de rango espera."""

    queryset = TiempoLineaDiaria.objects.all()
    serializer_class = TiempoLineaDiariaSerializer


# ==================================================
# F O T O   D E   A H O R A
# ==================================================


class ResumenPlantaAPIView(APIView):
    """La foto de la planta en este momento, sin fechas de por medio.

    Es APIView y no RetrieveAPIView porque la vista siempre devuelve un solo
    renglón: no hay nada que buscar por id."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "reportes"

    def get(self, request):
        resumen = ResumenPlanta.objects.first()

        # No debería pasar nunca: vista_dash_resumen_planta está armada con
        # subconsultas y siempre regresa una fila. Pero si alguien corrió el
        # cliente sin cargar DB/vistas.sql, mejor un objeto vacío que un 500.
        if resumen is None:
            return Response({})

        return Response(ResumenPlantaSerializer(resumen).data)


class ResumenRangoAPIView(APIView):
    """Totales de producción, inspección y paros dentro del rango."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "reportes"

    def get(self, request):
        desde = _fecha(request.query_params.get('desde'))
        hasta = _fecha(request.query_params.get('hasta'))

        try:
            resumen = procedimientos.llamar('sp_Dashboard_Resumen', desde, hasta)
        except DatabaseError as error:
            return Response({'mensaje': mensaje_de_base(error)},
                            status=status.HTTP_400_BAD_REQUEST)


        return Response({
            clave: int(valor) if isinstance(valor, (Decimal, int)) else valor
            for clave, valor in resumen.items()
        })


class StockComponentesAPIView(SoloLecturaAdmin):
    """Inventario por modelo de componente.

    Con ?umbral=N devuelve nada más los modelos con N piezas disponibles o
    menos, que es la alerta de material bajo. Sin umbral devuelve todo, para
    quien quiera ver el inventario completo."""

    queryset = StockComponentes.objects.all()
    serializer_class = StockComponentesSerializer

    def get_queryset(self):
        queryset = self.queryset

        umbral = self.request.query_params.get('umbral')
        if umbral is not None:
            queryset = queryset.filter(disponibles__lte=_entero(umbral, 0))

        return queryset.order_by('disponibles', 'modelo_nombre')


class ActividadAPIView(SoloLecturaAdmin):
    """Los últimos movimientos del sistema, del más nuevo al más viejo.

    ?limite=N acota cuántos (default 15, tope 100) y ?tipo=PARO filtra a un
    solo tipo de evento."""

    queryset = Actividad.objects.all()
    serializer_class = ActividadSerializer

    def get_queryset(self):
        queryset = self.queryset

        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo.upper())

        desde = _fecha(self.request.query_params.get('desde'))
        if desde:
            queryset = queryset.filter(fecha__gte=desde)

        limite = _entero(self.request.query_params.get('limite'),
                         ACTIVIDAD_LIMITE, ACTIVIDAD_LIMITE_MAX)

        return queryset.order_by('-fecha', '-hora')[:limite]


# ==================================================
# A L E R T A S
# ==================================================
#
# Las dos devuelven filas, no conteos: una alerta que sólo dice "hay 3" obliga a
# irse a otra pantalla para saber cuáles son, y entonces no sirvió de alerta.


class ParosAbiertosAPIView(SoloLecturaAdmin):
    """Paros que siguen sin cerrarse, del más viejo al más nuevo.

    El más viejo primero a propósito: es el que lleva más tiempo deteniendo una
    línea y el que hay que atender."""

    serializer_class = VistaParoSerializer

    def get_queryset(self):
        return (VistaParo.objects
                .filter(fecha_fin__isnull=True)
                .order_by('fecha_inicio', 'hora_inicio'))


class RechazosAPIView(SoloLecturaAdmin):
    """Inspecciones rechazadas dentro del rango, de la más reciente hacia atrás.

    resultado = 0 es Rechazada (ver vista_inspeccion_calidad)."""

    serializer_class = ListVistaInspeccionSerializer

    def get_queryset(self):
        queryset = VistaInspeccionCalidad.objects.filter(resultado=0)

        desde = _fecha(self.request.query_params.get('desde'))
        hasta = _fecha(self.request.query_params.get('hasta'))

        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)

        return queryset.order_by('-fecha', '-hora')


# ==================================================
# T R A Z A B I L I D A D   P O R   O R D E N
# ==================================================


class TrazabilidadOrdenAPIView(APIView):
    """Todo lo que le pasó a una orden, en una sola respuesta.

    Son cuatro vistas distintas, pero se devuelven juntas a propósito: la
    pantalla las necesita todas al mismo tiempo y no tiene caso hacerle cuatro
    viajes al cliente. El permiso es "trazabilidad", no "reportes", porque es
    otra pantalla y podría abrirse a otro rol sin mover el dashboard."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "trazabilidad"

    def get(self, request, folio):
        orden = TrazaOrden.objects.filter(folio=folio).first()

        if orden is None:
            return Response({'mensaje': f'No existe la orden con folio {folio}.'},
                            status=404)

        laptops = (TrazaOrdenLaptop.objects
                   .filter(orden_folio=folio)
                   .order_by('numero'))

        componentes = (TrazaOrdenComponente.objects
                       .filter(orden_folio=folio)
                       .order_by('tipo_nombre', 'modelo_nombre'))

        # Los abiertos primero: son los que todavía le pueden estorbar.
        paros = (TrazaOrdenParo.objects
                 .filter(orden_folio=folio)
                 .order_by('-abierto', '-fecha_inicio', '-hora_inicio'))

        return Response({
            'orden': TrazaOrdenSerializer(orden).data,
            'laptops': TrazaOrdenLaptopSerializer(laptops, many=True).data,
            'componentes': TrazaOrdenComponenteSerializer(componentes, many=True).data,
            'paros': TrazaOrdenParoSerializer(paros, many=True).data,
        })


class TiempoLaptopAPIView(APIView):
    """Cuánto lleva una laptop en línea: su acumulado y el desglose por pasada.

    Las dos cosas juntas en una respuesta porque la pantalla las enseña juntas:
    el total arriba y el renglón por línea abajo. Los tiempos vienen en las dos
    medidas, bruta y de turno (ver models.py, bloque TIEMPO EN LÍNEA)."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "trazabilidad"

    def get(self, request, numero):
        pasadas = (TiempoLinea.objects
                   .filter(laptop_numero=numero)
                   .order_by('fecha_inicio', 'hora_inicio', 'numero'))

        total = TiempoLaptop.objects.filter(laptop=numero).first()

        return Response({
            'total': TiempoLaptopSerializer(total).data if total else None,
            'pasadas': TiempoLineaSerializer(pasadas, many=True).data,
        })


class TrazabilidadOrdenesAPIView(SoloLecturaAdmin):
    """Listado de órdenes con su avance, para el buscador de trazabilidad.

    Sirve para que la pantalla ofrezca los folios que existen en lugar de
    obligar al admin a adivinar uno."""

    queryset = TrazaOrden.objects.all()
    serializer_class = TrazaOrdenSerializer
    modulo = "trazabilidad"

    def get_queryset(self):
        queryset = self.queryset

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado_codigo=estado)

        return queryset.order_by('-folio')
