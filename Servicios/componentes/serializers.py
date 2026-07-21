
from rest_framework import serializers
from .models import *
 
 
# Catálogos
 
class TipoCompSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoComp
        fields = '__all__'
 
 
class EdoComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoComponente
        fields = '__all__'
 
 
class LoteCompSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoteComp
        fields = '__all__'
 
 
class ModeloComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloComponente
        fields = '__all__'


# Tabla puente modelo_laptop <-> modelo_componente

class ModeloLaptopComponenteSerializer(serializers.ModelSerializer):
    """Para crear/editar renglones de la lista de materiales (BOM)."""
    class Meta:
        model = ModeloLaptopComponente
        # se listan explícitos para no exponer el campo virtual 'pk'
        fields = ['modelo_laptop', 'modelo_componente', 'capacidad']


class ModeloLaptopComponenteDetalleSerializer(serializers.ModelSerializer):
    """Solo lectura: el componente con su nombre/tipo y la capacidad,
    para anidarlo en el detalle de un modelo de laptop."""
    componente_codigo = serializers.CharField(source='modelo_componente.codigo', read_only=True)
    componente_nombre = serializers.CharField(source='modelo_componente.nombre', read_only=True)
    componente_tipo = serializers.CharField(source='modelo_componente.tipo_componente_id', read_only=True)

    class Meta:
        model = ModeloLaptopComponente
        fields = ['componente_codigo', 'componente_nombre', 'componente_tipo', 'capacidad']
 
 
# Ordenes de material
 
class OrdenMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenMaterial
        fields = '__all__'
 
 
class DetalleMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleMaterial
        # Se listan los campos explícitamente para no exponer el campo
        # virtual 'pk' (la llave compuesta orden+modelo se ve en sus columnas).
        fields = ['orden', 'modelo', 'cantidad']
 
 
class OrdenMaterialDetailSerializer(OrdenMaterialSerializer):
    """Detalle de una orden de material con sus renglones (detalle_material) anidados."""
    detalles = serializers.SerializerMethodField()
 
    def get_detalles(self, obj):
        detalles = DetalleMaterial.objects.filter(orden=obj.numero)
        return DetalleMaterialSerializer(detalles, many=True).data
 
 
# Componente
 
class ComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Componente
        fields = '__all__'
 
 
class VistaComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaComponente
        fields = '__all__'