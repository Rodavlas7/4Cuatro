from django.db import DatabaseError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import TienePermisoModulo
# Create your views here.

''' AQUI ESTAN LOS VIEWS DE:
│   - TipoComp (catálogo, solo lectura)
│   - EdoComponente (catálogo, solo lectura)
│   - LoteComp (catálogo: crear / modificar / eliminar)
│   - ModeloComponente (catálogo: crear / modificar / eliminar)
│   - OrdenMaterial + DetalleMaterial (crear / modificar / eliminar)
│   - VistaComponente (consulta general, lee de la vista SQL vista_componentes)
│   - Componente (crear / modificar / eliminar=marcar como Mermado)
'''
 
# Código de estado usado para el "soft delete" de un componente.
# EDC004 = Mermado (ver DB/datos.sql, tabla edo_componente).
ESTADO_MERMADO = 'EDC004'


# ==================================================
# E R R O R E S   D E   L A   B A S E
# ==================================================
#
# Buena parte de las reglas de negocio no vive en Python: vive en los triggers
# de DB/triggers.sql y en las llaves foráneas. Cuando una de esas reglas se
# rompe, MySQL levanta la excepción y Django la deja subir como un 500 con su
# página de depuración. El cliente no puede leer eso, así que sólo alcanza a
# mostrar "La API respondió 500." y el usuario nunca se entera de qué hizo mal,
# aunque el trigger le haya escrito el motivo en español.
#
# Aquí se atrapa y se devuelve un 400 con el motivo en la clave "mensaje", que
# es la que ya lee core.api.mensaje_error del cliente.

MYSQL_LLAVE_DUPLICADA = 1062
MYSQL_FK_EN_USO = 1451        # borrar un padre que todavía tiene hijos
MYSQL_FK_INEXISTENTE = 1452   # apuntar a un padre que no existe
MYSQL_TRIGGER = 1644          # el SIGNAL SQLSTATE '45000' de DB/triggers.sql


def mensaje_de_base(error):
    """Traduce el error crudo de MySQL a algo que se pueda mostrar en pantalla."""

    codigo = error.args[0] if error.args else None
    texto = str(error.args[1]) if len(error.args) > 1 else str(error)

    if codigo == MYSQL_TRIGGER:
        # El trigger ya trae el motivo redactado en español; sólo se le quita el
        # prefijo técnico "Error tg_Nombre_Del_Trigger:".
        return texto.split(':', 1)[-1].strip()

    if codigo == MYSQL_FK_EN_USO:
        return 'No se puede eliminar: hay registros que todavía dependen de este.'

    if codigo == MYSQL_FK_INEXISTENTE:
        return 'Alguno de los datos relacionados no existe.'

    if codigo == MYSQL_LLAVE_DUPLICADA:
        return 'Ya existe un registro con esa llave.'

    return 'La base de datos rechazó la operación.'


class ErroresDeBaseMixin:
    """Devuelve 400 con el motivo cuando la base rechaza un alta, cambio o baja.

    Va SIEMPRE primero en la lista de bases, para que su perform_* se ejecute
    antes que el de la vista genérica de DRF."""

    def _intentar(self, accion, argumento):
        try:
            accion(argumento)
        except DatabaseError as error:
            raise ValidationError({'mensaje': mensaje_de_base(error)})

    def perform_create(self, serializer):
        self._intentar(super().perform_create, serializer)

    def perform_update(self, serializer):
        self._intentar(super().perform_update, serializer)

    def perform_destroy(self, instance):
        self._intentar(super().perform_destroy, instance)


# Vistas de catálogos (solo lectura)
 
class TipoCompListAPIView(generics.ListAPIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "componentes"
    
    queryset = TipoComp.objects.all()
    serializer_class = TipoCompSerializer
 
 
class EdoComponenteListAPIView(generics.ListAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
        
    queryset = EdoComponente.objects.all()
    serializer_class = EdoComponenteSerializer
 
 
# Vistas de LOTE_COMP
 
class LoteCompListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer


class LoteCompDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    serializer_class = LoteCompSerializer
    lookup_field = 'codigo'
 
 
class LoteCompModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = LoteComp.objects.all()
    # Al editar, el codigo lo manda la URL y no se toca (ver serializers.py).
    serializer_class = LoteCompUpdateSerializer
    lookup_field = 'codigo'


# Vistas de MODELO_COMPONENTE

class ModeloComponenteListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
 
 
class ModeloComponenteDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    queryset = ModeloComponente.objects.all()
    serializer_class = ModeloComponenteSerializer
    lookup_field = 'codigo'
 
 
class ModeloComponenteModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"

    queryset = ModeloComponente.objects.all()
    # Al editar, el codigo lo manda la URL y no se toca (ver serializers.py).
    serializer_class = ModeloComponenteUpdateSerializer
    lookup_field = 'codigo'


# Vistas de MODELO_LAPTOP_COMPONENTE (tabla puente / lista de materiales)

class ModeloLaptopComponenteListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    """GET: todos los renglones. Filtra por modelo de laptop con
    ?modelo_laptop=<codigo>.  POST: agrega un componente (con su capacidad)
    a un modelo de laptop."""
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    
    serializer_class = ModeloLaptopComponenteSerializer

    def get_queryset(self):
        queryset = ModeloLaptopComponente.objects.all()
        modelo_laptop = self.request.query_params.get('modelo_laptop')
        if modelo_laptop is not None:
            queryset = queryset.filter(modelo_laptop=modelo_laptop)
        return queryset


class ModeloLaptopComponenteModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    """Modifica/borra un renglón del BOM. Se direcciona por la llave
    compuesta (modelo_laptop, modelo_componente)."""
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "componentes"
    serializer_class = ModeloLaptopComponenteSerializer

    def get_object(self):
        obj = get_object_or_404(
            ModeloLaptopComponente,
            modelo_laptop=self.kwargs['modelo_laptop'],
            modelo_componente=self.kwargs['modelo_componente'],
        )
        self.check_object_permissions(self.request, obj)
        return obj



# Vistas de ORDEN_MATERIAL / DETALLE_MATERIAL

 
class OrdenMaterialListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    permission_classes = [
            IsAuthenticated,
            TienePermisoModulo
        ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
 
 
class OrdenMaterialDetailAPIView(generics.RetrieveAPIView):
    """GET: detalle de la orden de material con sus renglones (detalle_material) anidados."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialDetailSerializer
    lookup_field = 'numero'
 
 
class OrdenMaterialModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    queryset = OrdenMaterial.objects.all()
    serializer_class = OrdenMaterialSerializer
    lookup_field = 'numero'
 
 
class DetalleMaterialListCreateAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    """GET: todos los renglones. Filtra por orden con ?orden=<numero>.
    POST: agrega un renglón (modelo + cantidad) a una orden de material."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    serializer_class = DetalleMaterialSerializer
 
    def get_queryset(self):
        queryset = DetalleMaterial.objects.all()
        orden = self.request.query_params.get('orden')
        if orden is not None:
            queryset = queryset.filter(orden=orden)
        return queryset
 
 
class DetalleMaterialModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican la cantidad; DELETE borra el renglón.
    Se direcciona por la llave compuesta (orden, modelo), ya que la tabla
    detalle_material no tiene un id simple."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "orden_material"
    serializer_class = DetalleMaterialSerializer

    def get_object(self):
        obj = get_object_or_404(
            DetalleMaterial,
            orden=self.kwargs['orden'],
            modelo=self.kwargs['modelo'],
        )
        self.check_object_permissions(self.request, obj)
        return obj
 
 
# Vistas de COMPONENTE
 
class ComponenteListAPIView(ErroresDeBaseMixin, generics.ListCreateAPIView):
    """GET: consulta general del módulo (lee de la vista SQL vista_componentes).
    POST: registra un nuevo componente."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "componentes"
 
    def get_queryset(self):
        if self.request.method == 'POST':
            return Componente.objects.all()
        return VistaComponente.objects.all()
 
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ComponenteSerializer
        return VistaComponenteSerializer
 
 
class ComponenteDetailAPIView(generics.RetrieveAPIView):
    """GET: vista detallada de un componente (lee de la vista SQL vista_componentes)."""
    permission_classes = [
                IsAuthenticated,
                TienePermisoModulo
            ]
    modulo = "componentes"
    queryset = VistaComponente.objects.all()
    serializer_class = VistaComponenteSerializer
    lookup_field = 'numero'
 
 
class ComponenteModifyAPIView(ErroresDeBaseMixin, generics.RetrieveUpdateDestroyAPIView):
    """PUT/PATCH modifican el componente; DELETE lo marca como Mermado (EDC004)
    en lugar de borrar el registro físicamente."""
    permission_classes = [
                    IsAuthenticated,
                    TienePermisoModulo
                ]
    modulo = "componentes"
    queryset = Componente.objects.all()
    serializer_class = ComponenteSerializer
    lookup_field = 'numero'
 
    def perform_destroy(self, instance):
        # Reemplaza al perform_destroy del mixin (la baja no borra, marca), así
        # que el guardado se pasa por _intentar para no perder la traducción del
        # error de la base.
        def marcar_como_mermado(componente):
            componente.estado_id = ESTADO_MERMADO
            componente.save(update_fields=['estado'])

        self._intentar(marcar_como_mermado, instance)