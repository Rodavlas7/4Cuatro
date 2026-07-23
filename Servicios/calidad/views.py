from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.utils import timezone

from .models import InspeccionCalidad, VistaInspeccionCalidad
from . import serializers

from usuarios.permissions import TienePermisoModulo
from usuarios.models import EmpleadoLinea
from django.db import OperationalError




from django.db.models import Q



#----------------------------------------------------------------------------------------------
#           I N S P E C C I O N   C A L I D A D     V I E W S
#----------------------------------------------------------------------------------------------



# . . . . . .  . REGISTRO
class RegistroInspeccionCalidadAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "calidad"

    def post(self, request):
        serializer = serializers.CreateInspeccionCalidadSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        empleado = serializer.validated_data["empleado"]
        linea = serializer.validated_data["linea"]
        laptop = serializer.validated_data["laptop"]
        
        #validar rol del empleado
        if not empleado.rol or empleado.rol.codigo != "OPCALI":
            return Response(
                {
                    "mensaje":
                    "El empleado seleccionado no tiene permisos para realizar inspecciones de calidad."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        #validar que el empleado actualmente trabaje en esa linea
        trabaja_linea = EmpleadoLinea.objects.filter(
            empleado=empleado,
            linea=linea,
            fecha_fin__isnull=True
        ).exists()

        if not trabaja_linea:
            return Response(
                {
                    "mensaje":
                    "El empleado no trabaja actualmente en la línea seleccionada."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

       #validar estado de la laptop
        if InspeccionCalidad.objects.filter(
            laptop=laptop,
            resultado=0
        ).exists():
            return Response(
                {
                    "mensaje":
                    "No es posible registrar la inspección. La laptop ya fue rechazada y no puede continuar el proceso."
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        try:
            inspeccion = serializer.save()
        except OperationalError as e:
            mensaje = str(e)
            if "la laptop ya cuenta con una inspección" in mensaje:
                return Response(
                    {
                        "mensaje":
                        "No es posible registrar la inspección. La laptop ya cuenta con una inspección final registrada."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif "la laptop no está en estado de ensamblaje" in mensaje:
                return Response(
                    {
                        "mensaje":
                        "No es posible registrar la inspección. La laptop no se encuentra en estado de ensamblaje."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif "resultado de inspección no válido" in mensaje:
                return Response(
                    {
                        "mensaje":
                        "No es posible registrar la inspección. El resultado seleccionado no es válido."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "mensaje":
                    "No fue posible registrar la inspección de calidad."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "mensaje":
                "Inspección de calidad registrada correctamente",
                "numero":
                inspeccion.numero
            },
            status=status.HTTP_201_CREATED
        )



'''
# . . . . . .  . LISTA

class ListaInspeccionCalidadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    def get(self, request):

        inspecciones = InspeccionCalidad.objects.all()

        serializer = serializers.ListInspeccionCalidadSerializer(
            inspecciones,
            many=True
        )

        return Response(
            serializer.data
        )





# . . . . . .  . DETAIL

class DetailInspeccionCalidadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    def get(self, request, numero):

        try:

            inspeccion = InspeccionCalidad.objects.get(
                numero=numero
            )

        except InspeccionCalidad.DoesNotExist:

            return Response(
                {
                    "mensaje":
                    "Inspección de calidad no encontrada"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.DetailInspeccionCalidadSerializer(
            inspeccion
        )

        return Response(
            serializer.data
        )

'''

# Asegúrate de importar el nuevo modelo:
# from .models import InspeccionCalidad, VistaInspeccionCalidad


# . . . . . .  . LISTA con la vista

class ListaInspeccionCalidadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    def get(self, request):

        inspecciones = VistaInspeccionCalidad.objects.all()

        # Usamos el serializer de lista (ligero)
        serializer = serializers.ListVistaInspeccionSerializer(
            inspecciones,
            many=True
        )

        return Response(
            serializer.data
        )


# . . . . . .  . DETAIL

class DetailInspeccionCalidadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    def get(self, request, numero):

        try:
            
            inspeccion = VistaInspeccionCalidad.objects.get(
                numero=numero
            )

        except VistaInspeccionCalidad.DoesNotExist:

            return Response(
                {
                    "mensaje":
                    "Inspección de calidad no encontrada"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Usamos el serializer de detalle (completo)
        serializer = serializers.DetailVistaInspeccionSerializer(
            inspeccion
        )

        return Response(
            serializer.data
        )


# . . . . . .  . UPDATE

# ==========================================
# UPDATE INSPECCION DE CALIDAD
# ==========================================

class UpdateInspeccionCalidadAPIView(generics.UpdateAPIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    queryset = InspeccionCalidad.objects.all()

    serializer_class = serializers.UpdateInspeccionCalidadSerializer

    lookup_field = "numero"




# . . . . . .  . DELETE

class DeleteInspeccionCalidadAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    def delete(self, request, numero):

        try:

            inspeccion = InspeccionCalidad.objects.get(
                numero=numero
            )

        except InspeccionCalidad.DoesNotExist:

            return Response(
                {
                    "mensaje":
                    "Inspección de calidad no encontrada"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        inspeccion.delete()

        return Response(
            {
                "mensaje":
                "Inspección de calidad eliminada correctamente"
            }
        )
        
       
#busqueda 
class BuscarInspeccionCalidadView(generics.ListAPIView):

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]

    modulo = "calidad"

    serializer_class = serializers.ListInspeccionCalidadSerializer


    def get_queryset(self):

        queryset = InspeccionCalidad.objects.all()

        buscar = self.request.GET.get("buscar")


        if buscar:

            queryset = queryset.filter(

                Q(numero__icontains=buscar) |

                Q(laptop__numero__icontains=buscar) |

                Q(empleado__nombrepila__icontains=buscar) |

                Q(empleado__primerapell__icontains=buscar) |

                Q(linea__nombre__icontains=buscar) |

                Q(observaciones__icontains=buscar)

            )


        return queryset.order_by("-fecha", "-hora")