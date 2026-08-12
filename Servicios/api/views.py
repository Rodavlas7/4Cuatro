"""Vista base para disparar los procedimientos almacenados.

Los procedimientos de DB/procedimientos.sql no son CRUD sobre una tabla: son
operaciones que tocan varias y tienen que pasar o no pasar completas, así que
las resuelve la base y aquí sólo se dispara la llamada.

Por eso son APIView y no generics: no hay queryset ni serializer que valga. El
manejo de errores tampoco puede ser ErroresDeBaseMixin —ese envuelve los
perform_* de las vistas genéricas—, así que se atrapa el DatabaseError a mano y
se traduce con el mismo api.errores.

ES COMPARTIDO: vivía en produccion/views.py, y se movió aquí cuando componentes
empezó a necesitarla también (sp_Recibir_Orden_Material). Importar los views de
una app desde otra sólo por la clase base era acoplarlas sin razón.
"""

from django.db import DatabaseError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api import procedimientos
from api.errores import mensaje_de_base
from usuarios.permissions import TienePermisoModulo


class AccionDeProcedimientoAPIView(APIView):
    """Llama al procedimiento y devuelve su SELECT de resumen.

    Las subclases ponen el nombre del procedimiento, el módulo del permiso y
    de dónde salen los argumentos."""

    permission_classes = [IsAuthenticated, TienePermisoModulo]

    procedimiento = None

    def argumentos(self, request, **kwargs):
        raise NotImplementedError

    def post(self, request, **kwargs):
        try:
            resumen = procedimientos.llamar(self.procedimiento, *self.argumentos(request, **kwargs))
        except DatabaseError as error:
            return Response({'mensaje': mensaje_de_base(error)},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(resumen, status=status.HTTP_200_OK)
