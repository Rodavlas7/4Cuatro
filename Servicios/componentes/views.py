from django.shortcuts import get_object_or_404
from rest_framework import generics
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import TienePermisoModulo
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
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "componentes"
    
    queryset = TipoComp.objects.all()
    serializer_class = TipoCompSerializer
 
 
class EdoComponenteListAPIView(generics.ListAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
        
    queryset = EdoComponente.objects.all()
    serializer_class = EdoComponenteSerializer
 
 
# Vistas de LOTE_COMP
 
class LoteCompListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
 
 
class LoteCompDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
    lookup_field = 'codigo'
 
 
class LoteCompModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
    lookup_field = 'codigo'
 
 
# Vistas de MODELO_COMPONENTE
 
class ModeloComponenteListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
 
 
class ModeloComponenteDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
    lookup_field = 'codigo'
 
 
class ModeloComponenteModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
    lookup_field = 'codigo'


# Vistas de MODELO_LAPTOP_COMPONENTE (tabla puente / lista de materiales)

class ModeloLaptopComponenteListCreateAPIView(generics.ListCreateAPIView):
    """GET: todos los renglones. Filtra por modelo de laptop con
    ?modelo_laptop=<codigo>.  POST: agrega un componente (con su capacidad)
    a un modelo de laptop."""
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    
    serializer_class = ModeloLaptopComponenteSerializer

    def get_queryset(self):
        queryset = ModeloLaptopComponente.objects.all()
        modelo_laptop = self.request.query_params.get('modelo_laptop')
        if modelo_laptop is not None:
            queryset = queryset.filter(modelo_laptop=modelo_laptop)
        return queryset


class ModeloLaptopComponenteModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Modifica/borra un renglón del BOM. Se direcciona por la llave
    compuesta (modelo_laptop, modelo_componente)."""
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    serializer_class = ModeloLaptopComponenteSerializer

    def get_object(self):
        obj = get_object_or_404(
            ModeloLaptopComponente,
            modelo_laptop=self.kwargs['modelo_laptop'],
            modelo_componente=self.kwargs['modelo_componente'],
        )
        self.check_object_permissions(self.request, obj)
        return obj



# Vistas de ORDEN_MATERIAL / DETALLE_MATERIAL

 
class OrdenMaterialListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
 
 
class OrdenMaterialDetailAPIView(generics.RetrieveAPIView):
    """GET: detalle de la orden de material con sus renglones (detalle_material) anidados."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialDetailSerializer
    lookup_field = 'numero'
 
 
class OrdenMaterialModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
    lookup_field = 'numero'
 
 
class DetalleMaterialListCreateAPIView(generics.ListCreateAPIView):
    """GET: todos los renglones. Filtra por orden con ?orden=<numero>.
    POST: agrega un renglón (modelo + cantidad) a una orden de material."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    serializer_class = DetalleMaterialSerializer
 
    def get_queryset(self):
        queryset = DetalleMaterial.objects.all()
        orden = self.request.query_params.get('orden')
        if orden is not None:
            queryset = queryset.filter(orden=orden)
        return queryset
 
 
class DetalleMaterialModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la cantidad; DELETE borra el renglón.
    Se direcciona por la llave compuesta (orden, modelo), ya que la tabla
    detalle_material no tiene un id simple."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    serializer_class = DetalleMaterialSerializer

    def get_object(self):
        obj = get_object_or_404(
            DetalleMaterial,
            orden=self.kwargs['orden'],
            modelo=self.kwargs['modelo'],
        )
        self.check_object_permissions(self.request, obj)
        return obj
 
 
# Vistas de COMPONENTE
 
class ComponenteListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_componentes).
    POST: registra un nuevo componente."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "componentes"
 
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
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "componentes"
    queryset = VistaComponente.objects.all()
    serializer_class = VistaComponenteSerializer
    lookup_field = 'numero'
 
 
class ComponenteModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el componente; DELETE lo marca como Mermado (EDC004)
    en lugar de borrar el registro físicamente."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "componentes"
    queryset = Componente.objects.all()
    serializer_class = ComponenteSerializer
    lookup_field = 'numero'
 
    def perform_destroy(self, instance):
        instance.estado_id = ESTADO_MERMADO
        instance.save(update_fields=['estado'])