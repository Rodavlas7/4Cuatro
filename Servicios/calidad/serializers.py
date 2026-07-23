from rest_framework import serializers

from .models import InspeccionCalidad



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




#Actualizar
class UpdateInspeccionCalidadSerializer(serializers.ModelSerializer):

    class Meta:

        model = InspeccionCalidad

        fields = (
            "resultado",
            "observaciones",
        )