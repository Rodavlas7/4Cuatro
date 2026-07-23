from django.db import OperationalError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import TienePermisoModulo
from .models import RegistroEmbalaje
from . import serializers



from calidad.models import InspeccionCalidad


from rest_framework import generics


from django.db.models import Q







#----------------------------------------------------------------------------------------------
#           R E G I S T R O   E M B A L A J E     V I E W S
#----------------------------------------------------------------------------------------------


# . . . . . .  . REGISTRO

class RegistroEmbalajeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"



    def post(self, request):

        serializer = serializers.CreateRegistroEmbalajeSerializer(
            data=request.data
        )


        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        laptop = serializer.validated_data["laptop"]



        # ==================================================
        # VALIDAR CALIDAD
        # ==================================================

        aprobada = InspeccionCalidad.objects.filter(
            laptop=laptop,
            resultado=1
        ).exists()


        if not aprobada:

            return Response(
                {
                    "mensaje":
                    "No es posible registrar el embalaje. La laptop no cuenta con una inspección de calidad aprobada."
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        rechazada = InspeccionCalidad.objects.filter(
            laptop=laptop,
            resultado=0
        ).exists()


        if rechazada:

            return Response(
                {
                    "mensaje":
                    "No es posible registrar el embalaje. La laptop fue rechazada en calidad."
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        try:

            embalaje = serializer.save()


        except OperationalError as e:


            mensaje = str(e)


            if "ya fue embalada previamente" in mensaje:

                return Response(
                    {
                        "mensaje":
                        "No es posible registrar el embalaje. La laptop seleccionada ya fue embalada previamente."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            return Response(
                {
                    "mensaje":
                    "No fue posible registrar el embalaje."
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        return Response(
            {
                "mensaje":
                "Embalaje registrado correctamente",
                "numero":
                embalaje.numero
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

        embalajes = RegistroEmbalaje.objects.all()


        serializer = serializers.ListRegistroEmbalajeSerializer(
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



        serializer = serializers.DetailRegistroEmbalajeSerializer(
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





# . . . . . .  . DELETE

class DeleteRegistroEmbalajeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"



    def delete(self, request, numero):

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



        embalaje.delete()


        return Response(
            {
                "mensaje":
                "Registro de embalaje eliminado correctamente"
            }
        )
        
        
        
#busqueda
class BuscarRegistroEmbalajeView(generics.ListAPIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "embalaje"


    serializer_class = serializers.ListRegistroEmbalajeSerializer


    def get_queryset(self):

        queryset = RegistroEmbalaje.objects.all()


        buscar = self.request.GET.get("buscar")


        if buscar:

            queryset = queryset.filter(

                Q(numero__icontains=buscar) |

                Q(laptop__num_serie__icontains=buscar) |

                Q(tipo__nombre__icontains=buscar)

            )


        return queryset.order_by(
            "-fecha",
            "-hora"
        )