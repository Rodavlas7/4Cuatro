from django.db import IntegrityError

from rest_framework import generics, status

from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from usuarios import asignaciones
from usuarios.models import Empleado, EmpleadoLinea, ROL_SUPERVISOR
from usuarios.permissions import TienePermisoModulo
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - EdoLinea
│   - TipoLinea
│   - VistaLinea (consulta general, lee de la vista SQL vista_lineas)
│   - Linea (crear / modificar / eliminar=desactivar)
│   - VistaEstacion (consulta general, lee de la vista SQL vista_estaciones)
│   - Estacion (crear / modificar / eliminar=desactivar)
│   - Supervisores de una línea (asignar / quitar, sobre empleado_linea)
'''

# Vistas de LINEAS

class EdoLineaListAPIView(generics.ListAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "lineas"
    queryset = EdoLinea.objects.all()
    serializer_class = EdoLineaSerializer


class TipoLineaListAPIView(generics.ListAPIView):
    """Catálogo de tipos de línea (Ensamblaje / Embalaje). Llena el select del
    alta y la edición de líneas en el cliente."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "lineas"
    queryset = TipoLinea.objects.all()
    serializer_class = TipoLineaSerializer


class LineaListAPIView(generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_lineas).
    POST: crea una nueva línea."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "lineas"

    def get_queryset(self):
        if self.request.method == 'POST':
            return Linea.objects.all()
        return VistaLinea.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LineaSerializer
        return VistaLineaSerializer


class LineaDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una línea (lee de la vista SQL vista_lineas)
    e incluye sus estaciones anidadas."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "lineas"
    queryset = VistaLinea.objects.all()
    serializer_class = VistaLineaDetailSerializer
    lookup_field = 'codigo'


class LineaModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la línea; DELETE la desactiva (activo=False)
    en lugar de borrar el registro."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "lineas"
    queryset = Linea.objects.all()
    serializer_class = LineaSerializer
    lookup_field = 'codigo'

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=['activo'])


class EstacionListCreateAPIView(generics.ListCreateAPIView):
    """GET: consulta general (lee de la vista SQL vista_estaciones).
    POST: crea una nueva estación."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "estaciones"

    def get_queryset(self):
        if self.request.method == 'POST':
            return Estacion.objects.all()
        return VistaEstacion.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EstacionSerializer
        return VistaEstacionSerializer


class EstacionDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de una estación (lee de la vista SQL vista_estaciones)."""
    permission_classes = [
                        IsAuthenticated,
                        TienePermisoModulo
                    ]
    modulo = "estaciones"
    queryset = VistaEstacion.objects.all()
    serializer_class = VistaEstacionSerializer
    lookup_field = 'codigo'


class EstacionModifyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la estación; DELETE la desactiva (activo=False)
    en lugar de borrar el registro."""
    permission_classes = [
                        IsAuthenticated,
                        TienePermisoModulo
                    ]
    modulo = "estaciones"
    queryset = Estacion.objects.all()
    serializer_class = EstacionSerializer
    lookup_field = 'codigo'

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=['activo'])



class ListaEstacionesAPIView(APIView):
    permission_classes = [
            AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
        ]
    modulo = "empleados"
    def get(self, request):
        linea_id = request.query_params.get('linea')
        estaciones = Estacion.objects.all()
        if linea_id:
            estaciones = estaciones.filter(linea_id=linea_id)
        serializer = EstacionSerializer(estaciones, many=True)
        return Response(serializer.data)
    
class LineasActivasAPIView(APIView):
    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request):
        lineas = VistaLinea.objects.exclude(estado_codigo="INAC")
        serializer = VistaLineaSerializer(lineas, many=True)
        return Response(serializer.data)



# SUPERVISORES DE UNA LINEA
#
# Se guardan en empleado_linea, la misma tabla donde vive la asignación de
# cualquier empleado a una línea. Es M a M en los dos sentidos: una línea puede
# tener varios supervisores y un supervisor puede llevar varias líneas.
#
# Vigente = fecha_fin nula. Quitar a un supervisor NO borra el renglón: le pone
# fecha_fin, igual que el resto del sistema desactiva en vez de borrar, para que
# no se pierda quién supervisaba la línea cuando pasó lo que sea que se esté
# investigando.


def _supervisores_de(codigo):
    """Asignaciones vigentes de supervisor en esa línea."""
    return (
        EmpleadoLinea.objects
        .filter(linea_id=codigo, fecha_fin__isnull=True, empleado__rol=ROL_SUPERVISOR)
        .select_related('empleado', 'empleado__turno')
        .order_by('empleado__nombrepila', 'empleado__primerapell')
    )


class SupervisoresLineaAPIView(APIView):
    """GET: supervisores de la línea, más el catálogo de los que se le pueden
    asignar (los que todavía no la llevan).
    POST: asigna un supervisor a la línea. Espera {"empleado": <numero>}."""

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "lineas"

    def get(self, request, codigo):

        if not Linea.objects.filter(codigo=codigo).exists():
            return Response(
                {"mensaje": "La línea no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        asignados = _supervisores_de(codigo)

        # Para el select del formulario: supervisores activos que no estén ya en
        # esta línea. Que lleven otras no los descarta, justo porque es M a M.
        ya_asignados = [a.empleado_id for a in asignados]

        disponibles = (
            Empleado.objects
            .filter(rol=ROL_SUPERVISOR, activo=True)
            .exclude(numero__in=ya_asignados)
            .order_by('nombrepila', 'primerapell')
        )

        return Response({
            "asignados": SupervisorLineaSerializer(asignados, many=True).data,
            "disponibles": [
                {"numero": e.numero, "nombre": nombre_de_empleado(e)}
                for e in disponibles
            ],
        })

    def post(self, request, codigo):

        if not Linea.objects.filter(codigo=codigo).exists():
            return Response(
                {"mensaje": "La línea no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        numero = request.data.get("empleado")

        if not numero:
            return Response(
                {"mensaje": "Falta el empleado que se va a asignar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            empleado = Empleado.objects.get(numero=numero)
        except (Empleado.DoesNotExist, ValueError):
            return Response(
                {"mensaje": "El empleado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        if empleado.rol_id != ROL_SUPERVISOR:
            return Response(
                {"mensaje": "Ese empleado no es supervisor, así que no puede supervisar una línea."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not empleado.activo:
            return Response(
                {"mensaje": "El empleado está dado de baja."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            asignado = asignaciones.asignar(empleado, codigo)
        except IntegrityError:
            return Response(
                {"mensaje": "No se pudo guardar la asignación de este supervisor a la línea."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not asignado:
            return Response(
                {"mensaje": "Ese supervisor ya está asignado a esta línea."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"mensaje": "Supervisor asignado correctamente."},
            status=status.HTTP_201_CREATED
        )


class SupervisorLineaQuitarAPIView(APIView):
    """DELETE: cierra la asignación del supervisor en esa línea (fecha_fin=hoy).
    El renglón se conserva como historial."""

    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "lineas"

    def delete(self, request, codigo, numero):

        if not asignaciones.quitar(numero, codigo):
            return Response(
                {"mensaje": "Ese supervisor no está asignado a esta línea."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)