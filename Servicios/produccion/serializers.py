from rest_framework import serializers
from .models import *
from componentes.models import Componente, ModeloLaptopComponente
from componentes.serializers import ComponenteSerializer, ModeloLaptopComponenteDetalleSerializer


# Produccion Serializers

class EdoProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoProduccion
        fields = '__all__'


class ModeloLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloLaptop
        fields = '__all__'


class ModeloLaptopDetailSerializer(ModeloLaptopSerializer):
    """Detalle del modelo con los componentes que puede llevar (BOM) y
    la capacidad de cada uno, tomados de la tabla puente."""
    componentes = serializers.SerializerMethodField()

    def get_componentes(self, obj):
        filas = ModeloLaptopComponente.objects.filter(
            modelo_laptop=obj.codigo
        ).select_related('modelo_componente')
        return ModeloLaptopComponenteDetalleSerializer(filas, many=True).data


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


class VistaParoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaParo
        fields = '__all__'


class EdoLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoLaptop
        fields = '__all__'


class LoteLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoteLaptop
        fields = '__all__'


class LaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laptop
        fields = '__all__'


class VistaLaptopSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaLaptop
        fields = '__all__'


class RegistroEnsamblajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEnsamblaje
        fields = '__all__'


class VistaLaptopDetailSerializer(VistaLaptopSerializer):
    """Detalle de laptop con sus registros de ensamblaje y componentes anidados."""
    registros_ensamblaje = serializers.SerializerMethodField()
    componentes = serializers.SerializerMethodField()

    def get_registros_ensamblaje(self, obj):
        registros = RegistroEnsamblaje.objects.filter(laptop=obj.numero).order_by('numero')
        return RegistroEnsamblajeSerializer(registros, many=True).data

    def get_componentes(self, obj):
        registro_ids = RegistroEnsamblaje.objects.filter(
            laptop=obj.numero
        ).values_list('numero', flat=True)
        componentes = Componente.objects.filter(
            registro_ensamblaje__in=list(registro_ids)
        ).order_by('numero')
        return ComponenteSerializer(componentes, many=True).data


class LoteLaptopDetailSerializer(LoteLaptopSerializer):
    """Detalle de lote con las laptops que le pertenecen anidadas."""
    laptops = serializers.SerializerMethodField()

    def get_laptops(self, obj):
        laptops = Laptop.objects.filter(lote=obj.codigo).order_by('numero')
        return LaptopSerializer(laptops, many=True).data
