from rest_framework import serializers
from embalaje.models import RegistroEmbalaje, VistaRegistroEmbalaje, TipoEmbalaje
from produccion.models import Laptop
from calidad.models import InspeccionCalidad

# SERIALIZERS PARA EL FRONTEND ---
class TipoEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalaje
        fields = (
            "codigo", 
            "nombre")

class LaptopDisponibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laptop
        fields = ("numero", "num_serie") 

# --- SERIALIZADOR DE CREACIÓN ---
class CreateRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmbalaje
        fields = ("fecha", "hora", "laptop", "tipo")

    def validate(self, attrs):
        laptop = attrs.get('laptop')

        # 1. Validar si ya fue embalada
        if RegistroEmbalaje.objects.filter(laptop=laptop).exists():
            raise serializers.ValidationError({"laptop": "Esta laptop ya ha sido embalada anteriormente."})

        # 2. Validar calidad aprobada (resultado=1)
        if not InspeccionCalidad.objects.filter(laptop=laptop, resultado=1).exists():
            raise serializers.ValidationError({"laptop": "La laptop no cuenta con una inspección de calidad aprobada."})

        # 3. Validar que no esté rechazada (resultado=0)
        if InspeccionCalidad.objects.filter(laptop=laptop, resultado=0).exists():
            raise serializers.ValidationError({"laptop": "La laptop tiene una inspección de calidad rechazada."})

        return attrs



# . . . . . .  . LISTAR
class ListRegistroEmbalajeSerializer(serializers.ModelSerializer):
    laptop = serializers.CharField(
        source="laptop.num_serie",
        read_only=True
    )
    tipo = serializers.CharField(
        source="tipo.nombre",
        read_only=True
    )
    
    class Meta:
        model = RegistroEmbalaje
        fields = (
            "numero",
            "fecha",
            "hora",
            "laptop",
            "tipo",
        )



# . . . . . .  . DETAIL
class DetailRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmbalaje

        fields = "__all__"

#--------------------------------------------------------------------------------------------------
class ListVistaRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaRegistroEmbalaje
        # Ponemos los equivalentes exactos a los que tenías
        fields = (
            "numero",
            "fecha",
            "hora",
            "laptop_num_serie", 
            "tipo_nombre",
        )

# . . . . . .  . DETAIL
class DetailVistaRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaRegistroEmbalaje
        fields = "__all__"
#---------------------------------------------------------------------------------------------------------


# . . . . . .  . UPDATE
class UpdateRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmbalaje

        fields = (
            "fecha",
            "hora",
            "tipo",
        )
    