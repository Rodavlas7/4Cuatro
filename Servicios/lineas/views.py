from rest_framework import generics

from .models import *
from .serializers import *

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - EdoLinea
│   - VistaLinea (consulta general, lee de la vista SQL vista_lineas)
│   - Linea (crear / modificar / eliminar=desactivar)
│   - VistaEstacion (consulta general, lee de la vista SQL vista_estaciones)
│   - Estacion (crear / modificar / eliminar=desactivar)
'''

# Vistas de LINEAS

class EdoLineaListAPIView(generics.ListAPIView):
    queryset = EdoLinea.objects.all()
    serializer_class = EdoLineaSerializer


class LineaListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_lineas).
    POST: crea una nueva línea."""

    def get_queryset(self):
        if self.request.method == 'POST':
            return Linea.objects.all()
        return VistaLinea.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LineaSerializer
        return VistaLineaSerializer


class LineaDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una línea (lee de la vista SQL vista_lineas)
    e incluye sus estaciones anidadas."""
    queryset = VistaLinea.objects.all()
    serializer_class = VistaLineaDetailSerializer
    lookup_field = 'codigo'


class LineaModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    """PUT/PATCH modifican la línea; DELETE la desactiva (activo=False)
    en lugar de borrar el registro."""
    queryset = Linea.objects.all()
    serializer_class = LineaSerializer
    lookup_field = 'codigo'

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=['activo'])


class EstacionListCreateAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_estaciones).
    POST: crea una nueva estación."""

    def get_queryset(self):
        if self.request.method == 'POST':
            return Estacion.objects.all()
        return VistaEstacion.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EstacionSerializer
        return VistaEstacionSerializer


class EstacionDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una estación (lee de la vista SQL vista_estaciones)."""
    queryset = VistaEstacion.objects.all()
    serializer_class = VistaEstacionSerializer
    lookup_field = 'codigo'


class EstacionModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    """PUT/PATCH modifican la estación; DELETE la desactiva (activo=False)
    en lugar de borrar el registro."""
    queryset = Estacion.objects.all()
    serializer_class = EstacionSerializer
    lookup_field = 'codigo'

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=['activo'])
