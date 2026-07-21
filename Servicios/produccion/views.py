from django.utils import timezone
from rest_framework import generics

from .models import *
from .serializers import *

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
    queryset = EdoProduccion.objects.all()
    serializer_class = EdoProduccionSerializer


class ModeloLaptopListAPIView(generics.ListCreateAPIView):
    queryset = ModeloLaptop.objects.all()
    serializer_class = ModeloLaptopSerializer


class ModeloLaptopDetailAPIView(generics.RetrieveAPIView):
    """GET: detalle del modelo de laptop con los componentes que lleva
    (lista de materiales) anidados."""
    queryset = ModeloLaptop.objects.all()
    serializer_class = ModeloLaptopDetailSerializer
    lookup_field = 'codigo'


class EdoLaptopListAPIView(generics.ListAPIView):
    queryset = EdoLaptop.objects.all()
    serializer_class = EdoLaptopSerializer


class LoteLaptopListAPIView(generics.ListCreateAPIView):
    queryset = LoteLaptop.objects.all()
    serializer_class = LoteLaptopSerializer


class LoteLaptopDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un lote, con sus laptops anidadas."""
    queryset = LoteLaptop.objects.all()
    serializer_class = LoteLaptopDetailSerializer
    lookup_field = 'codigo'


class OrdenProduccionListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_ordenes_produccion).
    POST: crea una nueva orden de producción."""

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
    queryset = VistaOrdenProduccion.objects.all()
    serializer_class = VistaOrdenProduccionSerializer
    lookup_field = 'folio'


class OrdenProduccionModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la orden; DELETE la cancela (estado=CANC)
    en lugar de borrar el registro."""
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionSerializer
    lookup_field = 'folio'

    def perform_destroy(self, instance):
        instance.estado_id = 'CANC'
        instance.save(update_fields=['estado'])


class ParoListCreateAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_paros).
    POST: crea un nuevo paro."""

    def get_queryset(self):
        if self.request.method == 'POST':
            return Paro.objects.all()
        return VistaParo.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ParoSerializer
        return VistaParoSerializer


class ParoDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un paro (lee de la vista SQL vista_paros)."""
    queryset = VistaParo.objects.all()
    serializer_class = VistaParoSerializer
    lookup_field = 'numero'


class ParoModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el paro; DELETE lo cierra (fecha_fin/hora_fin = ahora)
    en lugar de borrar el registro."""
    queryset = Paro.objects.all()
    serializer_class = ParoSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        ahora = timezone.localtime()
        instance.fecha_fin = ahora.date()
        instance.hora_fin = ahora.time()
        instance.save(update_fields=['fecha_fin', 'hora_fin'])


class LaptopListAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_laptops).
    POST: crea una nueva laptop."""

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
    queryset = VistaLaptop.objects.all()
    serializer_class = VistaLaptopDetailSerializer
    lookup_field = 'numero'


class LaptopModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la laptop; DELETE la rechaza (estado=RECHA)
    en lugar de borrar el registro."""
    queryset = Laptop.objects.all()
    serializer_class = LaptopSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        instance.estado_id = 'RECHA'
        instance.save(update_fields=['estado'])


class RegistroEnsamblajeListCreateAPIView(generics.ListCreateAPIView):
    queryset = RegistroEnsamblaje.objects.select_related('laptop', 'linea').all()
    serializer_class = RegistroEnsamblajeSerializer


class RegistroEnsamblajeDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un registro de ensamblaje."""
    queryset = RegistroEnsamblaje.objects.select_related('laptop', 'linea').all()
    serializer_class = RegistroEnsamblajeSerializer
    lookup_field = 'numero'


class RegistroEnsamblajeModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el registro; DELETE lo cierra (fecha_fin/hora_fin = ahora)
    en lugar de borrar el registro."""
    queryset = RegistroEnsamblaje.objects.all()
    serializer_class = RegistroEnsamblajeSerializer
    lookup_field = 'numero'

    def perform_destroy(self, instance):
        ahora = timezone.localtime()
        instance.fecha_fin = ahora.date()
        instance.hora_fin = ahora.time()
        instance.save(update_fields=['fecha_fin', 'hora_fin'])
