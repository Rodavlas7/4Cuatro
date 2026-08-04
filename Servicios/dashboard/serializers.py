"""Serializers del dashboard.

Son todos ModelSerializer pelones con fields = '__all__': las vistas de la base
ya traen exactamente las columnas que la pantalla necesita, así que no hay nada
que calcular aquí. Si algún día hace falta un campo derivado, que se agregue a
la vista SQL y no a este archivo: así el número queda disponible también para
quien consulte la base a mano.
"""

from rest_framework import serializers

from .models import (
    Actividad,
    CalidadDiaria,
    ParosDiaria,
    ProduccionDiaria,
    ResumenPlanta,
    StockComponentes,
    TrazaOrden,
    TrazaOrdenComponente,
    TrazaOrdenLaptop,
    TrazaOrdenParo,
)


class ProduccionDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduccionDiaria
        fields = '__all__'


class CalidadDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalidadDiaria
        fields = '__all__'


class ParosDiariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParosDiaria
        fields = '__all__'


class ResumenPlantaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumenPlanta
        fields = '__all__'


class StockComponentesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockComponentes
        fields = '__all__'


class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actividad
        fields = '__all__'


class TrazaOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrazaOrden
        fields = '__all__'


class TrazaOrdenLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrazaOrdenLaptop
        fields = '__all__'


class TrazaOrdenComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrazaOrdenComponente
        fields = '__all__'


class TrazaOrdenParoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrazaOrdenParo
        fields = '__all__'
