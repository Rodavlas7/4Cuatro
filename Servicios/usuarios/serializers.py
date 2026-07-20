from rest_framework import serializers
from .models import Usuario, Rol, Turno, Empleado


#----------------------------------------------------------------------------------------------
#           U S U A R I O S     S E R I A L I Z E R S
#----------------------------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=32)
    contrasena = serializers.CharField(write_only=True)