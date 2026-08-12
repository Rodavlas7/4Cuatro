from rest_framework import serializers

from usuarios.models import EmpleadoLinea

from .models import *


# Linea Serializers

class EdoLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdoLinea
        fields = '__all__'


class TipoLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoLinea
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


class VistaEstacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaEstacion
        fields = '__all__'


# SUPERVISORES DE LA LINEA
#
# Un renglón de empleado_linea visto desde la línea, que es como lo pinta el
# detalle de línea del panel de administrador: ahí lo que importa es quién
# supervisa, no la asignación en sí, así que el empleado viene aplanado.

class SupervisorLineaSerializer(serializers.ModelSerializer):
    numero = serializers.IntegerField(source='empleado.numero', read_only=True)
    nombre = serializers.SerializerMethodField()
    turno = serializers.SerializerMethodField()

    class Meta:
        model = EmpleadoLinea
        fields = ('numero', 'nombre', 'turno', 'fecha_inicio')

    def get_nombre(self, obj):
        return nombre_de_empleado(obj.empleado)

    def get_turno(self, obj):
        # El turno es opcional en empleado; sin este rodeo un empleado sin turno
        # tumbaría el serializer al recorrer turno.nombre.
        turno = obj.empleado.turno
        return turno.nombre if turno else None


def nombre_de_empleado(empleado):
    """Nombre completo del empleado, sin los huecos de los apellidos nulos."""
    partes = (empleado.nombrepila, empleado.primerapell, empleado.segundoapell)
    return ' '.join(parte for parte in partes if parte)
