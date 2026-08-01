from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password
from .models import Usuario, Rol, Turno, Empleado,  EmpleadoEstacion, EmpleadoLinea, VistaEmpleado, VistaUsuario


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
# usuarios/serializers.py (API)
import re

class CreateEmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ("nombrepila", "primerapell", "segundoapell", "rol", "turno")

    def validate_nombrepila(self, value):
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
            raise serializers.ValidationError("El nombre no puede contener números.")
        return value

    def validate_primerapell(self, value):
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
            raise serializers.ValidationError("El apellido no puede contener números.")
        return value

    def validate_segundoapell(self, value):
        if value and not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
            raise serializers.ValidationError("El apellido no puede contener números.")
        return value


class ListEmpleadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VistaEmpleado
        fields = "__all__"

class DetailEmpleadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VistaEmpleado
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
    usuario = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = (
            "usuario",
            "contrasena",
            "empleado"
        )
        extra_kwargs = {
            "contrasena": {
                "write_only": True
            }
        }

    def validate_usuario(self, value):
        if value and not re.match(r'^[A-Za-z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos."
            )
        return value

    def _generar_usuario_por_empleado(self, empleado):
        numero = str(int(empleado.numero))[-4:].zfill(4)
        nombre = (empleado.nombrepila or "").strip()
        primer_apellido = (empleado.primerapell or "").strip()
        segundo_apellido = (empleado.segundoapell or "").strip()

        inicial_nombre = nombre[:1].upper() if nombre else "X"
        inicial_primer_apellido = primer_apellido[:1].upper() if primer_apellido else "X"

        if segundo_apellido:
            inicial_segundo_apellido = segundo_apellido[:1].upper()
        else:
            inicial_segundo_apellido = (
                primer_apellido[1:2].upper() if len(primer_apellido) > 1 else 
                nombre[1:2].upper() if len(nombre) > 1 else "X"
            )

        return numero + inicial_nombre + inicial_primer_apellido + inicial_segundo_apellido

    def validate(self, data):
        if not data.get("usuario"):
            empleado = data.get("empleado")
            if not empleado:
                raise serializers.ValidationError(
                    {"empleado": "Debe asignar un empleado para generar el nombre de usuario."}
                )
            data["usuario"] = self._generar_usuario_por_empleado(empleado)
        return data

    def validate_contrasena(self, value):
        if value == "":
            raise serializers.ValidationError(
                "La contraseña no puede estar vacía."
            )

        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener mínimo 8 caracteres."
            )

        return value

    def create(self, validated_data):
        validated_data["contrasena"] = make_password(
            validated_data["contrasena"]
        )
        validated_data["estado"] = True
        return Usuario.objects.create(**validated_data)
    
    
class ListUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = VistaUsuario
        fields = (
            "numero",
            "usuario",
            "empleado_nombre",
            "rol_nombre",
            "estado_usuario",
        )
        
        
class DetailUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = VistaUsuario
        fields = "__all__"
        
        
class UpdateUsuarioSerializer(serializers.ModelSerializer):
    admin_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = (
            "usuario",
            "contrasena",
            "admin_password",
        )
        extra_kwargs = {
            "contrasena": {
                "write_only": True,
                "required": False
            }
        }

    def validate_usuario(self, value):
        if value and not re.match(r'^[A-Za-z0-9_.-]+$', value):
            raise serializers.ValidationError(
                "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos."
            )
        if Usuario.objects.filter(usuario=value).exclude(numero=self.instance.numero).exists():
            raise serializers.ValidationError(
                "El nombre de usuario ya está en uso por otro registro."
            )
        return value

    def validate_contrasena(self, value):
        if value == "":
            raise serializers.ValidationError(
                "La contraseña no puede estar vacía."
            )

        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener mínimo 8 caracteres."
            )

        return value

    def update(self, instance, validated_data):
        if "contrasena" in validated_data:
            instance.contrasena = make_password(
                validated_data.pop("contrasena")
            )
        # admin_password is only used for authorization, not stored on the model.
        validated_data.pop("admin_password", None)
        return super().update(
            instance,
            validated_data
        )
    

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