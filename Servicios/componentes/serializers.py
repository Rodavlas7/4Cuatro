
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
 
 
# Ordenes de material
 
class OrdenMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenMaterial
        fields = '__all__'
 
 
class DetalleMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleMaterial
        fields = '__all__'
 
 
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