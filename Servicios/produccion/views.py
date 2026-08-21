from django.utils import timezone
from rest_framework import generics
from api.errores import ErroresDeBaseMixin
from api.views import AccionDeProcedimientoAPIView
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import TienePermisoModulo
from django.db.models import Q
from lineas.models import Linea
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - EdoProduccion (catálogo, solo lectura)
│   - ModeloLaptop (catálogo, crear)
│   - EdoLaptop (catálogo, solo lectura)
│   - LoteLaptop (catálogo, crear)
│   - VistaOrdenProduccion (consulta general, lee de la vista SQL vista_ordenes_produccion)
│   - OrdenProduccion (crear / modificar / eliminar=cancelar)
│   - VistaParo (consulta general, lee de la vista SQL vista_paros)
│   - Paro (crear / modificar / eliminar=cerrar)
│   - VistaLaptop (consulta general, lee de la vista SQL vista_laptops)
│   - Laptop (crear / modificar / eliminar=rechazar)
│   - RegistroEnsamblaje (crear / modificar / eliminar=cerrar)
'''

# Vistas de PRODUCCION

class EdoProduccionListAPIView(generics.ListAPIView):
    permission_classes = [
                        IsAuthenticated,
                        TienePermisoModulo
                    ]
    modulo = "orden_produccion"
    queryset = EdoProduccion.objects.all()
    serializer_class = EdoProduccionSerializer


class ModeloLaptopListAPIView(generics.ListCreateAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = ModeloLaptop.objects.all()
    serializer_class = ModeloLaptopSerializer


class ModeloLaptopDetailAPIView(generics.RetrieveAPIView):
    """GET: detalle del modelo de laptop con los componentes que lleva
    (lista de materiales) anidados."""
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "laptops"
    queryset = ModeloLaptop.objects.all()
    serializer_class = ModeloLaptopDetailSerializer
    lookup_field = 'codigo'


class EdoLaptopListAPIView(generics.ListAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = EdoLaptop.objects.all()
    serializer_class = EdoLaptopSerializer


class LoteLaptopListAPIView(generics.ListCreateAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = LoteLaptop.objects.all()
    serializer_class = LoteLaptopSerializer


class LoteLaptopDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un lote, con sus laptops anidadas."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = LoteLaptop.objects.all()
    serializer_class = LoteLaptopDetailSerializer
    lookup_field = 'codigo'


class OrdenProduccionListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_ordenes_produccion).
    POST: crea una nueva orden de producción."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_produccion"

    def get_queryset(self):
        if self.request.method == 'POST':
            return OrdenProduccion.objects.all()
        return VistaOrdenProduccion.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrdenProduccionSerializer
        return VistaOrdenProduccionSerializer


class OrdenProduccionDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una orden (lee de la vista SQL vista_ordenes_produccion)."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_produccion"
    queryset = VistaOrdenProduccion.objects.all()
    serializer_class = VistaOrdenProduccionSerializer
    lookup_field = 'folio'


class OrdenProduccionModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la orden; DELETE la cancela (estado=CANC)
    en lugar de borrar el registro."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_produccion"
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionSerializer
    lookup_field = 'folio'

    def perform_destroy(self, instance):
        instance.estado_id = 'CANC'
        instance.save(update_fields=['estado'])




class ParoListCreateAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_paros).
    POST: crea un nuevo paro, valida que la línea esté Activa y la marca como En Paro."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "paro"

    def get_queryset(self):
        if self.request.method == 'POST':
            return Paro.objects.all()
        return VistaParo.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ParoSerializer
        return VistaParoSerializer

    def create(self, request, *args, **kwargs):
        linea_id = request.data.get("linea")

        try:
            linea = Linea.objects.get(pk=linea_id)
        except Linea.DoesNotExist:
            return Response(
                {"mensaje": "La línea seleccionada no existe"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not linea.estado or linea.estado.codigo != "ACTI":
            return Response(
                {"mensaje": "Solo se puede registrar un paro en una línea que esté Activa"},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            linea.estado_id = "PARO"
            linea.save(update_fields=["estado"])

        return response


class ParoDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un paro (lee de la vista SQL vista_paros)."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "paro"
    queryset = VistaParo.objects.all()
    serializer_class = VistaParoSerializer
    lookup_field = 'numero'


class ParoModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el paro; DELETE lo cierra (fecha_fin/hora_fin = ahora)
    y regresa la línea a estado Activa."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "paro"
    queryset = Paro.objects.all()
    serializer_class = ParoSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        ahora = timezone.localtime()
        instance.fecha_fin = ahora.date()
        instance.hora_fin = ahora.time()
        instance.save(update_fields=['fecha_fin', 'hora_fin'])

        if instance.linea:
            instance.linea.estado_id = "ACTI"
            instance.linea.save(update_fields=["estado"])
            
            
            

class LaptopListAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_laptops).
    POST: crea una nueva laptop."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"

    def get_queryset(self):
        if self.request.method == 'POST':
            return Laptop.objects.all()
        return VistaLaptop.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LaptopSerializer
        return VistaLaptopSerializer


class LaptopDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una laptop (lee de la vista SQL vista_laptops)
    e incluye sus registros de ensamblaje y componentes anidados."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = VistaLaptop.objects.all()
    serializer_class = VistaLaptopDetailSerializer
    lookup_field = 'numero'


class LaptopModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la laptop; DELETE la rechaza (estado=RECHA)
    en lugar de borrar el registro."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "laptops"
    queryset = Laptop.objects.all()
    serializer_class = LaptopSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        instance.estado_id = 'RECHA'
        instance.save(update_fields=['estado'])


class RegistroEnsamblajeListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "ensamblaje"
    queryset = RegistroEnsamblaje.objects.select_related('laptop', 'linea').all()
    serializer_class = RegistroEnsamblajeSerializer


class RegistroEnsamblajeDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un registro de ensamblaje."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "ensamblaje"
    queryset = RegistroEnsamblaje.objects.select_related('laptop', 'linea').all()
    serializer_class = RegistroEnsamblajeSerializer
    lookup_field = 'numero'


class RegistroEnsamblajeModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el registro; DELETE lo cierra (fecha_fin/hora_fin = ahora)
    en lugar de borrar el registro."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "ensamblaje"
    queryset = RegistroEnsamblaje.objects.all()
    serializer_class = RegistroEnsamblajeSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        ahora = timezone.localtime()
        instance.fecha_fin = ahora.date()
        instance.hora_fin = ahora.time()
        instance.save(update_fields=['fecha_fin', 'hora_fin'])

class BuscarParoAPIView(generics.ListAPIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "paro"
    serializer_class = VistaParoSerializer

    def get_queryset(self):
        queryset = VistaParo.objects.all()
        buscar = self.request.GET.get("buscar")
        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(razon__icontains=buscar) |
                Q(linea_nombre__icontains=buscar)
            )

        if fecha_desde:
            queryset = queryset.filter(fecha_inicio__gte=fecha_desde)

        if fecha_hasta:
            queryset = queryset.filter(fecha_inicio__lte=fecha_hasta)

        return queryset.order_by("-fecha_inicio", "-hora_inicio")

# ==================================================
# A C C I O N E S   ( P R O C E D I M I E N T O S )
# ==================================================
#
# Estas tres no son CRUD sobre una tabla: son operaciones que tocan varias y
# tienen que pasar o no pasar completas, así que las resuelve la base con un
# procedimiento (DB/procedimientos.sql) y aquí sólo se dispara la llamada.
#
# La clase base vive en api/views.py: la comparten todos los módulos de la API
# (componentes también la usa, para sp_Recibir_Orden_Material).


class CancelarOrdenProduccionAPIView(AccionDeProcedimientoAPIView):
    """Cancela la orden, libera el material de sus laptops a medias y las
    rechaza. Las Aprobadas y Embaladas se respetan."""

    modulo = "orden_produccion"
    procedimiento = "sp_Cancelar_Orden_Produccion" #AQUI SE LLAMA UN PROCEDIMIENTO

    def argumentos(self, request, folio=None):
        return (folio,)


class IniciarEnsamblajeOrdenAPIView(AccionDeProcedimientoAPIView):
    """Da de alta las laptops que le faltan a la orden para llegar a su
    cantidad planificada.

    No recibe línea: las laptops nacen sin ella. En qué línea se arma cada una
    lo dice su registro de ensamblaje, y ése se abre después, unidad por
    unidad."""

    modulo = "orden_produccion"
    procedimiento = "sp_Iniciar_Ensamblaje_Orden"#AQUI SE LLAMA UN PROCEDIMIENTO

    def argumentos(self, request, folio=None):
        return (folio,)


class LiberarComponentesLaptopAPIView(AccionDeProcedimientoAPIView):
    """Desarma la laptop: suelta sus componentes y cierra su ensamblaje.

    'estado' dice a dónde regresan los componentes: EDC001 (Disponible) si
    sirven, EDC003 (Dañado) si no. Si no viene, se toma Disponible."""

    modulo = "ensamblaje"
    procedimiento = "sp_Liberar_Componentes_Laptop"#AQUI SE LLAMA UN PROCEDIMIENTO

    def argumentos(self, request, numero=None):
        return (numero, request.data.get('estado'))
