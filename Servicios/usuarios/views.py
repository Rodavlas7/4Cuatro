from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password, check_password

#ESTO ES PARA EL TOKEN
from secrets import token_hex
from django.utils import timezone
from datetime import timedelta

from .models import Usuario,Sesion
from .serializers import LoginSerializer

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
                
      