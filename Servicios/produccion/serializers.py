from rest_framework import serializers
from .models import *
from componentes.models import Componente, ModeloLaptopComponente
from componentes.serializers import ComponenteSerializer, ModeloLaptopComponenteDetalleSerializer


# Estados con los que nacen los registros del módulo. Se aplican en la propia
# API para que la regla no dependa de que el cliente los mande.
EDO_ORDEN_INICIAL = 'PEND'      # Pendiente (edo_produccion)
EDO_LAPTOP_INICIAL = 'REGIS'    # Registrada (edo_laptop)

# Órdenes a las que todavía se les puede registrar producción.
EDOS_ORDEN_ABIERTA = ('PEND', 'PROC')


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

    def validate_cant_planificada(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("cant_planificada no puede ser menor a 0.")
        return value

    def validate(self, attrs):
        """Una orden nueva nace Pendiente. El usuario no elige el estado al
        registrarla: de ahí en adelante lo mueven los triggers (a En Proceso
        cuando se le registra la primera laptop, a Completada cuando se embala
        todo lo planificado) o el botón de cancelar."""
        if self.instance is None and not attrs.get('estado'):
            attrs['estado'] = EdoProduccion.objects.filter(
                codigo=EDO_ORDEN_INICIAL).first()
        return attrs


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

    def validate_num_serie(self, value):
        """El número de serie se fija al registrar la laptop y solo lo sustituye
        el trigger tg_Generar_Numero_Serie_Final cuando calidad la aprueba. Es el
        identificador con el que la laptop queda trazada, así que un update no lo
        puede reescribir. Mandar el mismo valor no estorba: solo se rechaza el cambio."""
        if self.instance is not None and value != self.instance.num_serie:
            raise serializers.ValidationError(
                "El número de serie no se puede modificar."
            )
        return value

    def validate_orden(self, value):
        """Solo se registra producción contra órdenes abiertas: una Completada o
        Cancelada ya no admite laptops nuevas."""
        if value is not None and self.instance is None:
            if value.estado_id not in EDOS_ORDEN_ABIERTA:
                raise serializers.ValidationError(
                    "Solo se pueden registrar laptops en órdenes Pendientes o En Proceso."
                )
        return value

    def validate(self, attrs):
        """El modelo y el lote de una laptop NO se capturan: salen de su orden de
        producción, que es la que define qué se está fabricando y bajo qué lote.
        Se recalculan también al editar, para que una laptop no termine con un
        modelo distinto al de su orden.

        Además, una laptop nueva nace Registrada."""
        orden = attrs.get('orden') or getattr(self.instance, 'orden', None)
        if orden is not None:
            attrs['modelo'] = orden.modelo_laptop
            attrs['lote'] = orden.lote

        if self.instance is None and not attrs.get('estado'):
            attrs['estado'] = EdoLaptop.objects.filter(
                codigo=EDO_LAPTOP_INICIAL).first()

        return attrs


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
