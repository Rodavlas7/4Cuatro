from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from django.utils import timezone

from .models import DetalleInspeccion, InspeccionCalidad, VistaInspeccionCalidad
from . import serializers

from usuarios.permissions import TienePermisoModulo
from usuarios.models import EmpleadoLinea
from django.db import OperationalError
from produccion.models import Laptop, EdoLaptop

from django.db.models import Q



#----------------------------------------------------------------------------------------------
#           I N S P E C C I O N   C A L I D A D     V I E W S
#----------------------------------------------------------------------------------------------



# . . . . . .  . REGISTRO
class RegistroInspeccionCalidadAPIView(APIView):
    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
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
        
        # Validar que la laptop no tenga ya una inspección en la misma línea
        if InspeccionCalidad.objects.filter(
            laptop=laptop,
            linea=linea
        ).exists():
            return Response(
                {
                    "mensaje": (
                        "No es posible registrar la inspección. "
                        "La laptop ya fue inspeccionada en la línea seleccionada."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

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
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
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
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
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

RESULTADO_ESTADO_MAP = {
    1: 'APROV',
    0: 'RECHA',
    2: 'PENSAM',
}


class UpdateInspeccionCalidadAPIView(generics.UpdateAPIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "calidad"

    queryset = InspeccionCalidad.objects.all()

    serializer_class = serializers.UpdateInspeccionCalidadSerializer

    lookup_field = "numero"

    def perform_update(self, serializer):
        inspeccion = serializer.save()
        resultado = inspeccion.resultado
        estado_codigo = RESULTADO_ESTADO_MAP.get(resultado)

        if estado_codigo and inspeccion.laptop_id:
            Laptop.objects.filter(pk=inspeccion.laptop_id).update(estado_id=estado_codigo)


# . . . . . .  . DELETE

class DeleteInspeccionCalidadAPIView(APIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
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
        
       
class BuscarInspeccionCalidadView(generics.ListAPIView):

    permission_classes = [
        AllowAny
        # IsAuthenticated,
        # TienePermisoModulo
    ]

    modulo = "calidad"

    serializer_class = serializers.ListVistaInspeccionSerializer

    def get_queryset(self):

        queryset = VistaInspeccionCalidad.objects.all()

        buscar = self.request.GET.get("buscar")
        fecha_inicio = self.request.GET.get("fecha_inicio")
        fecha_fin = self.request.GET.get("fecha_fin")

        if buscar:

            queryset = queryset.filter(

                Q(numero__icontains=buscar) |
                Q(laptop_numero__icontains=buscar) |
                Q(empleado_nombre__icontains=buscar) |
                Q(linea_nombre__icontains=buscar) |
                Q(observaciones__icontains=buscar)

            )


        # Filtro desde fecha
        if fecha_inicio:
            queryset = queryset.filter(
                fecha__gte=fecha_inicio
            )


        # Filtro hasta fecha
        if fecha_fin:
            queryset = queryset.filter(
                fecha__lte=fecha_fin
            )


        return queryset.order_by("-fecha", "-hora")

#----------------------------------------------------------------------------------------------
#           D E T A L L E   D E   I N S P E C C I O N     V I E W S
#
#   Qué piezas reprobaron una inspección. Se registran DESPUÉS de crear la
#   inspección, porque el renglón la referencia por llave foránea.
#----------------------------------------------------------------------------------------------


class RegistroDetalleInspeccionAPIView(APIView):
    """Alta de los renglones de una inspección.

    Acepta un objeto o una lista: el inspector puede marcar varias piezas de un
    golpe y no tiene sentido obligar al cliente a una llamada por pieza.
    """

    permission_classes = [AllowAny]
    modulo = "calidad"

    def post(self, request):
        muchos = isinstance(request.data, list)

        serializer = serializers.CreateDetalleInspeccionSerializer(
            data=request.data, many=muchos
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # La pieza tiene que ser de la laptop que se inspeccionó. Si no, se
        # estaría culpando a un componente de otra unidad.
        renglones = serializer.validated_data if muchos else [serializer.validated_data]
        for renglon in renglones:
            inspeccion = renglon["inspeccion"]
            componente = renglon["componente"]
            registro = componente.registro_ensamblaje

            if registro is None or registro.laptop_id != inspeccion.laptop_id:
                return Response(
                    {"mensaje": (
                        f"El componente {componente.numero} no está montado en la "
                        f"laptop {inspeccion.laptop_id}, no puede reprobar su inspección."
                    )},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListaDetalleInspeccionAPIView(generics.ListAPIView):
    """Renglones de una inspección: qué piezas la reprobaron."""

    permission_classes = [AllowAny]
    modulo = "calidad"
    serializer_class = serializers.ListDetalleInspeccionSerializer

    def get_queryset(self):
        queryset = DetalleInspeccion.objects.all()
        inspeccion = self.kwargs.get("inspeccion")
        if inspeccion is not None:
            queryset = queryset.filter(inspeccion=inspeccion)
        return queryset
