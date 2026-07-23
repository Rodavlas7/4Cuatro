from datetime import date, timedelta
from secrets import token_hex

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lineas.models import Estacion, Linea

from usuarios import models, serializers
from .models import Sesion, Usuario, Empleado, VistaEmpleado, VistaUsuario
from .serializers import LoginSerializer, ListEmpleadoSerializer, DetailEmpleadoSerializer, UpdateEmpleadoSerializer, BajaEmpleadoSerializer
from usuarios.permissions import TienePermisoModulo

#################################
# MARLENE MARLENE MARLENE AHORA EN POSTMAN usa "Bearer tu_token", en la parte donde tienes que poner tu token
###########################

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - Empleado          (FALTA PONER ESTE)
│   - Usuario           
│   - Rol               (NO PONDREMOS)
│   - Turno             (NO PONDREMOS)
│   - EmpleadoLinea   (FALTA PONER ESTE)
│   - EmpleadoEstacion (FALTA PONER ESTE)
'''
# Create your models here.


#----------------------------------------------------------------------------------------------
#           U S U A R I O S     V I E W S
#----------------------------------------------------------------------------------------------
#Login
class LoginAPIView(APIView):

    permission_classes = [AllowAny]
    def get(self, request):
        return Response(
            {
                "mensaje": "Utiliza el método POST para iniciar sesión."
            }
        )

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = serializer.validated_data['usuario']
        contrasena = serializer.validated_data['contrasena']


        # Buscar usuario
        try:

            usuario_db = Usuario.objects.get(
                usuario=usuario
            )
        except Usuario.DoesNotExist:
            return Response(
                {
                    "mensaje": "Usuario o contraseña incorrectos"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar estado del usuario
        if not usuario_db.estado:
            return Response(
                {
                    "mensaje": "El usuario se encuentra desactivado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Verificar contraseña
        if not check_password(
            contrasena,
            usuario_db.contrasena
        ):
            return Response(
                {
                    "mensaje": "Usuario o contraseña incorrectos"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==================================================
        # VALIDAR EMPLEADO Y ROL
        # ==================================================
        try:
            empleado = usuario_db.empleado
        except Empleado.DoesNotExist:
            return Response(
                {
                    "mensaje": "El usuario no tiene un empleado asignado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if not empleado.rol:
            return Response(
                {
                    "mensaje": "El empleado no tiene un rol asignado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener código del rol
        rol = empleado.rol.codigo

        # ROLES QUE PUEDEN USAR EL SISTEMA
        roles_permitidos = [
            "ADMIN",
            "SUPER",
            "OPCALI"
        ]
        if rol not in roles_permitidos:
            return Response(
                {
                    "mensaje": "Este rol no tiene acceso al sistema"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # GENERAR TOKEN
        # Eliminar sesiones anteriores
        Sesion.objects.filter(
            usuario=usuario_db
        ).delete()

        token = token_hex(32)
        
        ahora = timezone.now()
        expiracion = ahora + timedelta(hours=10)
        
        # Crear nueva sesión
        Sesion.objects.create(
            usuario=usuario_db,
            token=token,
            fecha_inicio=ahora,
            fecha_expiracion=expiracion
        )

        # YA CUANDO INICIA SESION CHIDO
        return Response(
            {
                "mensaje": "Inicio de sesión exitoso",
                "usuario": usuario_db.usuario,
                "empleado": empleado.numero,
                "nombre": f"{empleado.nombrepila} {empleado.primerapell}",      
                "rol": rol,
                "token": token
            },
            status=status.HTTP_200_OK
        )

# . . . . . . . . REGISTRAR

class RegistroUsuarioAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "usuarios"
     
    def post(self, request):

        serializer = serializers.CreateUsuarioSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        empleado = serializer.validated_data["empleado"]

        if Usuario.objects.filter(empleado=empleado).exists():
            return Response(
                {
                    "mensaje": "El empleado ya tiene un usuario asignado"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if Usuario.objects.filter(
            usuario=serializer.validated_data["usuario"]
        ).exists():
            return Response(
                {
                    "mensaje": "El nombre de usuario ya existe"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = serializer.save()

        return Response(
            {
                "mensaje": "Usuario registrado correctamente",
                "usuario": {
                    "numero": usuario.numero,
                    "usuario": usuario.usuario
                }
            },
            status=status.HTTP_201_CREATED
        )
# . . . . . . . . LISTAR
class ListaUsuariosAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "usuarios"

    def get(self, request):

        usuarios = VistaUsuario.objects.all()

        serializer = serializers.ListUsuarioSerializer(
            usuarios,
            many=True
        )

        return Response(serializer.data)

#Detalle usuario
class DetailUsuarioAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "usuarios"

    def get(self, request, numero):

        try:
            usuario = VistaUsuario.objects.get(numero=numero)

        except VistaUsuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.DetailUsuarioSerializer(usuario)

        return Response(serializer.data)
    
# . . . . . .  . . . Actualizar
class UpdateUsuarioAPIView(APIView):

    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "usuarios" 

    def put(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.UpdateUsuarioSerializer(
            usuario,
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()

        return Response(
            {
                "mensaje": "Usuario actualizado correctamente"
            }
        )
        


# . . . . . .  . . . BAJA LOGICA
class BajaUsuarioAPIView(APIView):

    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "usuarios" 

    def patch(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not usuario.estado:
            return Response(
                {
                    "mensaje": "El usuario ya se encuentra desactivado"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.estado = False
        usuario.save()

        return Response(
            {
                "mensaje": "Usuario desactivado correctamente"
            }
        )
        
# . . . . . .  . . .  REACTIVAR USURAIO
class ReactivarUsuarioAPIView(APIView):

    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "usuarios" 

    def patch(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if usuario.estado:
            return Response(
                {
                    "mensaje": "El usuario ya se encuentra activo"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.estado = True
        usuario.save()

        return Response(
            {
                "mensaje": "Usuario reactivado correctamente"
            }
        )

#---------------------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------        E M P L E A D O     V I E W S       -------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------


#. . . . . .  . REGISTRO

class RegistroEmpleadoAPIView(APIView):
    
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "empleados" 

    @transaction.atomic
    def post(self, request):
        
        linea_id = request.data.get("linea")
        estacion_id = request.data.get("estacion")
        
        if not linea_id or not estacion_id:
            return Response(
                {
                    "mensaje": "Debe seleccionar una línea y una estación"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            linea = Linea.objects.get(
                pk=linea_id
            )


            estacion = Estacion.objects.get(
                pk=estacion_id
            )


        except Linea.DoesNotExist:

            return Response(
                {
                    "mensaje": "La línea seleccionada no existe"
                },
                status=status.HTTP_404_NOT_FOUND
            )


        except Estacion.DoesNotExist:

            return Response(
                {
                    "mensaje": "La estación seleccionada no existe"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if estacion.linea_id != linea.codigo:

            return Response(
                {
                    "mensaje": "La estación no pertenece a la línea seleccionada"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

#registrar empleado

        empleado_serializer = serializers.CreateEmpleadoSerializer(
            data=request.data
        )


        if not empleado_serializer.is_valid():

            return Response(
                empleado_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        empleado = empleado_serializer.save()

#asignar linea
        linea_data = {

            "empleado": empleado.numero,

            "linea": linea.codigo,

            "fecha_inicio": date.today()

        }


        linea_serializer = serializers.CreateEmpleadoLineaSerializer(
            data=linea_data
        )


        if not linea_serializer.is_valid():

            return Response(
                linea_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        linea_serializer.save()
        
#asignar estacion  
        estacion_data = {

            "empleado": empleado.numero,

            "estacion": estacion.codigo,

            "fecha_inicio": date.today()

        }
        
        estacion_serializer = serializers.CreateEmpleadoEstacionSerializer(
            data=estacion_data
        )


        if not estacion_serializer.is_valid():

            return Response(
                estacion_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        estacion_serializer.save()

        return Response(
            {
                "mensaje": "Empleado registrado correctamente",
                "empleado": empleado.numero,
                "linea": linea.nombre,
                "estacion": estacion.nombre
            },
            status=status.HTTP_201_CREATED
        )
        

#. . . . . .  . LISTA
class ListaEmpleadosAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request):

        empleados = VistaEmpleado.objects.all()

        serializer = ListEmpleadoSerializer(
            empleados,
            many=True
        )

        return Response(serializer.data)
#. . . . . .  . DETAIL
class DetailEmpleadoAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request, numero):

        try:
            empleado = VistaEmpleado.objects.get(numero=numero)

        except VistaEmpleado.DoesNotExist:
            return Response(
                {"mensaje": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailEmpleadoSerializer(empleado)

        return Response(serializer.data)
    
#. . . . . .  . Update
class UpdateEmpleadoView(generics.RetrieveUpdateAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "empleados" 
    queryset = Empleado.objects.all()
    serializer_class = UpdateEmpleadoSerializer
    lookup_field = "numero"
    
    
#. . . . . .  . DELETE 

# chavalines, no os preocupeis, es la desactivación de empleado, es decir, cambia el estado activo a False para conservar trazabilidad histórica
class BajaEmpleadoView(generics.UpdateAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "empleados" 
    queryset = Empleado.objects.all()
    serializer_class = BajaEmpleadoSerializer
    lookup_field = "numero"
    
