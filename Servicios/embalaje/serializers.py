from rest_framework import serializers
from embalaje.models import RegistroEmbalaje, VistaRegistroEmbalaje


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



'''# . . . . . .  . LISTAR
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

        fields = "__all__"'''
        
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
    