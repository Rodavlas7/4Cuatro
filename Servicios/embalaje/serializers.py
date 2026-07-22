from rest_framework import serializers
from embalaje.models import TipoEmbalaje, RegistroEmbalaje


#----------------------------------------------------------------------------------------------
#           R E G I S T R O   E M B A L A J E   
#----------------------------------------------------------------------------------------------

# . . . . . .  . REGISTRAR
class CreateRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmbalaje

        fields = (
            "fecha",
            "hora",
            "laptop",
            "tipo",
        )



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


# . . . . . .  . UPDATE
class UpdateRegistroEmbalajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmbalaje

        fields = (
            "fecha",
            "hora",
            "tipo",
        )
    