from rest_framework import serializers
from .models import *


# Linea Serializers

class EdoLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoLinea
        fields = '__all__'


class LineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Linea
        fields = '__all__'


class VistaLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaLinea
        fields = '__all__'


class EstacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estacion
        fields = '__all__'


class VistaLineaDetailSerializer(VistaLineaSerializer):
    """Detalle de línea con sus estaciones anidadas."""
    estaciones = serializers.SerializerMethodField()

    def get_estaciones(self, obj):
        estaciones = Estacion.objects.filter(linea=obj.codigo).order_by('codigo')
        return EstacionSerializer(estaciones, many=True).data
