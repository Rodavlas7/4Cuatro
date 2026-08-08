from django.db import OperationalError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import TienePermisoModulo
from .models import RegistroEmbalaje, VistaRegistroEmbalaje
from . import serializers
from produccion.models import Laptop
from .models import TipoEmbalaje

from calidad.models import InspeccionCalidad
from rest_framework import generics
from django.db.models import Q



# --- NUEVAS VISTAS PARA LOS SELECTS DEL FORMULARIO ---
class LaptopsDisponiblesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "embalaje"
    serializer_class = serializers.LaptopDisponibleSerializer

    def get_queryset(self):
        # Excluir las que ya están en RegistroEmbalaje
        laptops_embaladas = RegistroEmbalaje.objects.values_list('laptop', flat=True)
        
        return Laptop.objects.filter(
            inspeccioncalidad__resultado=1
        ).exclude(
            inspeccioncalidad__resultado=0
        ).exclude(
            pk__in=laptops_embaladas # pk o el nombre de tu primary key en Laptop
        ).exclude(
            estado='RECHA' 
        ).exclude(
            estado='PENSAM' 
        ).distinct()

class TipoEmbalajeListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "embalaje"
    queryset = TipoEmbalaje.objects.all()
    serializer_class = serializers.TipoEmbalajeSerializer


# --- REFACTOR: REGISTRO (MÁS LIMPIO Y ESTÁNDAR) ---
class RegistroEmbalajeAPIView(APIView):
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "embalaje"

    def post(self, request):
        serializer = serializers.CreateRegistroEmbalajeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        embalaje = serializer.save()
        
        return Response(
            {
                "mensaje": "Embalaje registrado correctamente",
                "numero": embalaje.numero
            },
            status=status.HTTP_201_CREATED
        )

# . . . . . .  . LISTA

class ListaRegistroEmbalajeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"

    def get(self, request):

        embalajes = VistaRegistroEmbalaje.objects.all()

        serializer = serializers.ListVistaRegistroEmbalajeSerializer(
            embalajes,
            many=True
        )

        return Response(
            serializer.data
        )


# . . . . . .  . DETAIL

class DetailRegistroEmbalajeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"

    def get(self, request, numero):

        try:

            embalaje = VistaRegistroEmbalaje.objects.get(
                numero=numero
            )

        except VistaRegistroEmbalaje.DoesNotExist:

            return Response(
                {
                    "mensaje":
                    "Registro de embalaje no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.DetailVistaRegistroEmbalajeSerializer(
            embalaje
        )

        return Response(
            serializer.data
        )



# . . . . . .  . UPDATE

class UpdateRegistroEmbalajeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"



    def put(self, request, numero):

        try:

            embalaje = RegistroEmbalaje.objects.get(
                numero=numero
            )


        except RegistroEmbalaje.DoesNotExist:


            return Response(
                {
                    "mensaje":
                    "Registro de embalaje no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )



        serializer = serializers.UpdateRegistroEmbalajeSerializer(
            embalaje,
            data=request.data
        )


        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )



        try:

            serializer.save()


        except OperationalError:


            return Response(
                {
                    "mensaje":
                    "No fue posible actualizar el registro de embalaje."
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        return Response(
            {
                "mensaje":
                "Registro de embalaje actualizado correctamente"
            }
        )
        
        
#busqueda
# --- REFACTOR: BÚSQUEDA (CORRECCIÓN DE QUERYSET) ---
class BuscarRegistroEmbalajeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, TienePermisoModulo]
    modulo = "embalaje"
    serializer_class = serializers.ListVistaRegistroEmbalajeSerializer

    def get_queryset(self):
        # CAMBIO: Hacemos la consulta directamente sobre la vista SQL
        queryset = VistaRegistroEmbalaje.objects.all()
        buscar = self.request.GET.get("buscar")

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(laptop_num_serie__icontains=buscar) |
                Q(tipo_nombre__icontains=buscar)
            )

        return queryset.order_by("-fecha", "-hora")