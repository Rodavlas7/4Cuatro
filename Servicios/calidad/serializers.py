from rest_framework import serializers

from .models import DetalleInspeccion, InspeccionCalidad, VistaInspeccionCalidad


# --------------------------------------------------------------------------
#   D E T A L L E   D E   I N S P E C C I O N   (piezas que reprobaron)
# --------------------------------------------------------------------------

class CreateDetalleInspeccionSerializer(serializers.ModelSerializer):
    """Alta de un renglón: qué pieza falló en qué inspección y por qué."""

    class Meta:
        model = DetalleInspeccion
        fields = ("inspeccion", "componente", "observacion")


class ListDetalleInspeccionSerializer(serializers.ModelSerializer):
    """Solo lectura, con lo mínimo para pintar la pieza sin otra llamada."""

    componente_numero = serializers.IntegerField(source="componente.numero", read_only=True)
    componente_serie = serializers.CharField(source="componente.num_serie", read_only=True)
    componente_modelo = serializers.CharField(source="componente.modelo.nombre", read_only=True)
    componente_tipo = serializers.CharField(
        source="componente.modelo.tipo_componente.nombre", read_only=True)
    componente_estado = serializers.CharField(source="componente.estado.nombre", read_only=True)

    class Meta:
        model = DetalleInspeccion
        fields = ("inspeccion", "componente", "observacion",
                  "componente_numero", "componente_serie",
                  "componente_modelo", "componente_tipo", "componente_estado")



#registrar
class CreateInspeccionCalidadSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspeccionCalidad
        fields = (
            "resultado",
            "observaciones",
            "fecha",
            "hora",
            "laptop",
            "empleado",
            "linea",
        )



#listar
class ListInspeccionCalidadSerializer(serializers.ModelSerializer):
    resultado = serializers.CharField(
        source="get_resultado_display",
        read_only=True
    )
    empleado = serializers.SerializerMethodField()
    laptop = serializers.IntegerField(source="laptop.numero", read_only=True)
    linea = serializers.CharField(source="linea.nombre",read_only=True)
    def get_empleado(self,obj):
        return (
            f"{obj.empleado.nombrepila} "
            f"{obj.empleado.primerapell}"
        )

    class Meta:
        model = InspeccionCalidad
        fields = (
            "numero",
            "resultado",
            "observaciones",
            "fecha",
            "hora",
            "laptop",
            "empleado",
            "linea",
        )



#detalle
class DetailInspeccionCalidadSerializer(serializers.ModelSerializer):
    resultado = serializers.CharField(
        source="get_resultado_display",
        read_only=True
    )
    class Meta:
        model = InspeccionCalidad
        fields = "__all__"
        
        
#---------------------------------------------------------------------------
class ListVistaInspeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaInspeccionCalidad
        fields = (
            "numero",
            "resultado_nombre",
            "fecha",
            "hora",
            "laptop_numero",
            "laptop_num_serie",
            "empleado_nombre",
            "linea_nombre",
        )

class DetailVistaInspeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaInspeccionCalidad
        fields = "__all__"
#----------------------------------------------------------------------------



#Actualizar
class UpdateInspeccionCalidadSerializer(serializers.ModelSerializer):

    class Meta:

        model = InspeccionCalidad

        fields = (
            "resultado",
            "observaciones",
        )