from rest_framework import generics
from .models import *
from .serializers import *
# Create your views here.

''' AQUI ESTAN LOS VIEWS DE:
│   - TipoComp (catálogo, solo lectura)
│   - EdoComponente (catálogo, solo lectura)
│   - LoteComp (catálogo: crear / modificar / eliminar)
│   - ModeloComponente (catálogo: crear / modificar / eliminar)
│   - OrdenMaterial + DetalleMaterial (crear / modificar / eliminar)
│   - VistaComponente (consulta general, lee de la vista SQL vista_componentes)
│   - Componente (crear / modificar / eliminar=marcar como Mermado)
'''
 
# Código de estado usado para el "soft delete" de un componente.
# EDC004 = Mermado (ver DB/datos.sql, tabla edo_componente).
ESTADO_MERMADO = 'EDC004'
 
 
# Vistas de catálogos (solo lectura)
 
class TipoCompListAPIView(generics.ListAPIView):
    queryset = TipoComp.objects.all()
    serializer_class = TipoCompSerializer
 
 
class EdoComponenteListAPIView(generics.ListAPIView):
    queryset = EdoComponente.objects.all()
    serializer_class = EdoComponenteSerializer
 
 
# Vistas de LOTE_COMP
 
class LoteCompListCreateAPIView(generics.ListCreateAPIView):
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
 
 
class LoteCompDetailAPIView(generics.RetrieveAPIView):
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
    lookup_field = 'codigo'
 
 
class LoteCompModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
    lookup_field = 'codigo'
 
 
# Vistas de MODELO_COMPONENTE
 
class ModeloComponenteListCreateAPIView(generics.ListCreateAPIView):
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
 
 
class ModeloComponenteDetailAPIView(generics.RetrieveAPIView):
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
    lookup_field = 'codigo'
 
 
class ModeloComponenteModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
    lookup_field = 'codigo'
 
 
# Vistas de ORDEN_MATERIAL / DETALLE_MATERIAL
 
class OrdenMaterialListCreateAPIView(generics.ListCreateAPIView):
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
 
 
class OrdenMaterialDetailAPIView(generics.RetrieveAPIView):
    """GET: detalle de la orden de material con sus renglones (detalle_material) anidados."""
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialDetailSerializer
    lookup_field = 'numero'
 
 
class OrdenMaterialModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
    lookup_field = 'numero'
 
 
class DetalleMaterialListCreateAPIView(generics.ListCreateAPIView):
    """GET: todos los renglones. Filtra por orden con ?orden=<numero>.
    POST: agrega un renglón (modelo + cantidad) a una orden de material."""
    serializer_class = DetalleMaterialSerializer
 
    def get_queryset(self):
        queryset = DetalleMaterial.objects.all()
        orden = self.request.query_params.get('orden')
        if orden is not None:
            queryset = queryset.filter(orden=orden)
        return queryset
 
 
class DetalleMaterialModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = DetalleMaterial.objects.all()
    serializer_class = DetalleMaterialSerializer
    lookup_field = 'pk'
 
 
# Vistas de COMPONENTE
 
class ComponenteListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_componentes).
    POST: registra un nuevo componente."""
 
    def get_queryset(self):
        if self.request.method == 'POST':
            return Componente.objects.all()
        return VistaComponente.objects.all()
 
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComponenteSerializer
        return VistaComponenteSerializer
 
 
class ComponenteDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un componente (lee de la vista SQL vista_componentes)."""
    queryset = VistaComponente.objects.all()
    serializer_class = VistaComponenteSerializer
    lookup_field = 'numero'
 
 
class ComponenteModifyAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    """PUT/PATCH modifican el componente; DELETE lo marca como Mermado (EDC004)
    en lugar de borrar el registro físicamente."""
    queryset = Componente.objects.all()
    serializer_class = ComponenteSerializer
    lookup_field = 'numero'
 
    def perform_destroy(self, instance):
        instance.estado_id = ESTADO_MERMADO
        instance.save(update_fields=['estado'])