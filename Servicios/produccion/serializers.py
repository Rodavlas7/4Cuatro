from rest_framework import serializers
from .models import EdoProduccion, ModeloLaptop, OrdenProduccion, Paro, VistaOrdenProduccion


# Produccion Serializers

class EdoProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoProduccion
        fields = '__all__'


class ModeloLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloLaptop
        fields = '__all__'


class OrdenProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenProduccion
        fields = '__all__'


class VistaOrdenProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaOrdenProduccion
        fields = '__all__'


class ParoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paro
        fields = '__all__'
