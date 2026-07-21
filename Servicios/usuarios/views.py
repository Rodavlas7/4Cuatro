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
from .models import Sesion, Usuario, Empleado
from .serializers import LoginSerializer, ListEmpleadoSerializer, DetailEmpleadoSerializer, UpdateEmpleadoSerializer, BajaEmpleadoSerializer

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

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(
            {
                "mensaje": "Utiliza el método POST para iniciar sesión."
            }
        )
    
    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = serializer.validated_data['usuario']
        contrasena = serializer.validated_data['contrasena']


        try:
            usuario_db = Usuario.objects.get(usuario=usuario)


        except Usuario.DoesNotExist:
            return Response(
                {"mensaje": "Usuario o contraseña incorrectos"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(contrasena, usuario_db.contrasena):
            return Response(
                {"mensaje": "Usuario o contraseña incorrectos"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        # SE GENERA EL TOKEN
        Sesion.objects.filter(usuario=usuario_db).delete() #SOLO UNA SESIÓN ACTIVA
        token = token_hex(32)

        # Calcular expiración (8 horas)
        expiracion = timezone.now() + timedelta(hours=10)

        # Guardar la sesión
        ahora = timezone.now()
        expiracion = ahora + timedelta(hours=10)

        Sesion.objects.create(
            usuario=usuario_db,
            token=token,
            fecha_inicio=ahora,
            fecha_expiracion=expiracion
        )
        return Response(
            {
                "mensaje": "Inicio de sesión exitoso",
                "usuario": usuario_db.usuario,
                "token": token
            },
            status=status.HTTP_200_OK
        )
              

#----------------------------------------------------------------------------------------------
#           E M P L E A D O     V I E W S
#----------------------------------------------------------------------------------------------


#. . . . . .  . REGISTRO

class RegistroEmpleadoAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

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

    def get(self, request):

        empleados = Empleado.objects.all()

        serializer = ListEmpleadoSerializer(
            empleados,
            many=True
        )

        return Response(serializer.data)
    
#. . . . . .  . DETAIL
class DetailEmpleadoAPIView(APIView):

    def get(self, request, numero):

        try:
            empleado = Empleado.objects.get(numero=numero)

        except Empleado.DoesNotExist:
            return Response(
                {"mensaje": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailEmpleadoSerializer(empleado)

        return Response(serializer.data)
    
#. . . . . .  . DETAIL
class UpdateEmpleadoView(generics.RetrieveUpdateAPIView):
    queryset = Empleado.objects.all()
    serializer_class = UpdateEmpleadoSerializer
    lookup_field = "numero"
    
    
#. . . . . .  . DELETE 

# chavalines, no os preocupeis, es la desactivación de empleado, es decir, cambia el estado activo a False para conservar trazabilidad histórica
class BajaEmpleadoView(generics.UpdateAPIView):
    queryset = Empleado.objects.all()
    serializer_class = BajaEmpleadoSerializer
    lookup_field = "numero"