from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Usuario, Rol, Turno, Empleado,  EmpleadoEstacion, EmpleadoLinea

#----------------------------------------------------------------------------------------------
#           R O L
#----------------------------------------------------------------------------------------------

class RolSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rol
        fields = "__all__"


#----------------------------------------------------------------------------------------------
#           T U R N O
#----------------------------------------------------------------------------------------------

class TurnoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Turno
        fields = "__all__"

#----------------------------------------------------------------------------------------------
#           E M P L E A D O
#----------------------------------------------------------------------------------------------  
class CreateEmpleadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Empleado
        fields = (
            "nombrepila",
            "primerapell",
            "segundoapell",
            "rol",
            "turno"
        )


class ListEmpleadoSerializer(serializers.ModelSerializer):

    rol = serializers.CharField(source="rol.nombre", read_only=True)
    turno = serializers.CharField(source="turno.nombre", read_only=True)

    class Meta:
        model = Empleado
        fields = (
            "numero",
            "nombrepila",
            "primerapell",
            "segundoapell",
            "rol",
            "turno",
            "activo"
        )


class DetailEmpleadoSerializer(serializers.ModelSerializer):

    rol = RolSerializer(read_only=True)
    turno = TurnoSerializer(read_only=True)

    class Meta:
        model = Empleado
        fields = "__all__"


class UpdateEmpleadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Empleado
        fields = (
            "nombrepila",
            "primerapell",
            "segundoapell",
            "rol",
            "turno"
        )
        
class BajaEmpleadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Empleado
        fields = (
            "activo",
        )
        
#----------------------------------------------------------------------------------------------
#           U S U A R I O S     S E R I A L I Z E R S
#----------------------------------------------------------------------------------------------

class CreateUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario

        fields = (
            "usuario",
            "contrasena",
            "estado",
            "empleado"
        )

        extra_kwargs = {
            "contrasena":{
                "write_only":True
            }
        }

    def create(self,validated_data):

        validated_data["contrasena"] = make_password(
            validated_data["contrasena"]
        )

        return Usuario.objects.create(**validated_data)
    
    
class CreateUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = (
            "usuario",
            "contrasena",
            "estado",
            "empleado"
        )
        
        extra_kwargs = {
            "contrasena": {
                "write_only": True
            }
        }

    def create(self, validated_data):
        validated_data["contrasena"] = make_password(
            validated_data["contrasena"]
        )

        return Usuario.objects.create(**validated_data)
    
    
class ListUsuarioSerializer(serializers.ModelSerializer):
    empleado = serializers.SerializerMethodField()
    def get_empleado(self,obj):

        return (
            f"{obj.empleado.nombrepila} "
            f"{obj.empleado.primerapell}"
        )

    class Meta:
        model = Usuario
        fields = (
            "numero",
            "usuario",
            "estado",
            "empleado",
        )
        
        
class DetailUsuarioSerializer(serializers.ModelSerializer):
    empleado = DetailEmpleadoSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "numero",
            "usuario",
            "estado",
            "empleado",
        )
        
        
class UpdateUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            "usuario",
            "contrasena",
            "estado",
        )

        extra_kwargs = {
            "contrasena": {
                "write_only": True,
                "required": False
            }
        }

    def update(self, instance, validated_data):
        if "contrasena" in validated_data:
            instance.contrasena = make_password(
                validated_data.pop("contrasena")
            )
        return super().update(instance, validated_data)
    

#----------------------------------------------------------------------------------------------
#           S E S I O N     S E R I A L I Z E R S
#----------------------------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=32)
    contrasena = serializers.CharField(write_only=True)


#----------------------------------------------------------------------------------------------
#           E M P L E A D O - L I N E A     S E R I A L I Z E R S
#----------------------------------------------------------------------------------------------
class CreateEmpleadoLineaSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmpleadoLinea

        fields = (
            "empleado",
            "linea",
            "fecha_inicio",
        )


class ListEmpleadoLineaSerializer(serializers.ModelSerializer):
    empleado = serializers.CharField(
        source="empleado.nombrepila",
        read_only=True
    )
    
    linea = serializers.CharField(
        source="linea.nombre",
        read_only=True
    )

    class Meta:
        model = EmpleadoLinea

        fields = (
            "empleado",
            "linea",
            "fecha_inicio",
            "fecha_fin",
        )
        
        
class DetailEmpleadoLineaSerializer(serializers.ModelSerializer):
    empleado = DetailEmpleadoSerializer(
        read_only=True
    )

    class Meta:
        model = EmpleadoLinea

        fields = "__all__"
        
class UpdateEmpleadoLineaSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmpleadoLinea

        fields = (
            "fecha_fin",
        )
        
        
#----------------------------------------------------------------------------------------------
#           E M P L E A D O - E S T A C I O N     S E R I A L I Z E R S
#----------------------------------------------------------------------------------------------
class ListEmpleadoEstacionSerializer(serializers.ModelSerializer):

    empleado = serializers.CharField(
        source="empleado.nombrepila",
        read_only=True
    )

    estacion = serializers.CharField(
        source="estacion.nombre",
        read_only=True
    )


    class Meta:
        model = EmpleadoEstacion

        fields = (
            "empleado",
            "estacion",
            "fecha_inicio",
            "fecha_fin",
        )
        
class DetailEmpleadoEstacionSerializer(serializers.ModelSerializer):
    empleado = DetailEmpleadoSerializer(
        read_only=True
    )
    
    class Meta:
        model = EmpleadoEstacion

        fields = "__all__"
        

class UpdateEmpleadoEstacionSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmpleadoEstacion

        fields = (
            "fecha_fin",
        )
        
class CreateEmpleadoEstacionSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmpleadoEstacion

        fields = (
            "empleado",
            "estacion",
            "fecha_inicio",
        )