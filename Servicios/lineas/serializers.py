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
