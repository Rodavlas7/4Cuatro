from django.utils import timezone
from rest_framework import generics

from .models import EdoProduccion, ModeloLaptop, OrdenProduccion, Paro, VistaOrdenProduccion
from .serializers import (
    EdoProduccionSerializer,
    ModeloLaptopSerializer,
    OrdenProduccionSerializer,
    ParoSerializer,
    VistaOrdenProduccionSerializer,
)

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - EdoProduccion (catálogo, solo lectura)
│   - ModeloLaptop (catálogo, solo lectura)
│   - VistaOrdenProduccion (consulta general, lee de la vista SQL vista_ordenes_produccion)
│   - OrdenProduccion (crear / modificar / eliminar=cancelar)
│   - Paro (crear / modificar / eliminar=cerrar)
'''

# Vistas de PRODUCCION

class EdoProduccionListAPIView(generics.ListAPIView):
    queryset = EdoProduccion.objects.all()
    serializer_class = EdoProduccionSerializer


class ModeloLaptopListAPIView(generics.ListAPIView):
    queryset = ModeloLaptop.objects.all()
    serializer_class = ModeloLaptopSerializer


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


class OrdenProduccionModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    """PUT/PATCH modifican la orden; DELETE la cancela (estado=CANC)
    en lugar de borrar el registro."""
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionSerializer
    lookup_field = 'folio'

    def perform_destroy(self, instance):
        instance.estado_id = 'CANC'
        instance.save(update_fields=['estado'])


class ParoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Paro.objects.select_related('linea').all()
    serializer_class = ParoSerializer


class ParoDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un paro."""
    queryset = Paro.objects.select_related('linea').all()
    serializer_class = ParoSerializer
    lookup_field = 'numero'


class ParoModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
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
