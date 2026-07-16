from rest_framework import serializers
from . import models

# ============================================================================
# LOTE_COMP SERIALIZERS
# ============================================================================
class LoteCompListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteComp
        fields = ['codigo']


class LoteCompDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteComp
        fields = ['codigo', 'descripcion']


class LoteCompCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteComp
        fields = ['codigo', 'descripcion']


# ============================================================================
# TIPO_EMBALAJE SERIALIZERS
# ============================================================================
class TipoEmbalajeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoEmbalaje
        fields = ['codigo', 'nombre']


class TipoEmbalajeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoEmbalaje
        fields = ['codigo', 'nombre']


class TipoEmbalajeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TipoEmbalaje
        fields = ['codigo', 'nombre']


# ============================================================================
# EDO_PRODUCCION SERIALIZERS
# ============================================================================
class EdoProduccionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoProduccion
        fields = ['codigo', 'nombre']


class EdoProduccionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoProduccion
        fields = ['codigo', 'nombre']


class EdoProduccionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EdoProduccion
        fields = ['codigo', 'nombre']


# ============================================================================
# LOTE_LAPTOP SERIALIZERS
# ============================================================================
class LoteLaptopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteLaptop
        fields = ['codigo', 'fecha']


class LoteLaptopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteLaptop
        fields = ['codigo', 'fecha']


class LoteLaptopCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteLaptop
        fields = ['codigo', 'fecha']

# ============================================================================
# MODELO_LAPTOP SERIALIZERS
# ============================================================================
class ModeloLaptopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloLaptop
        fields = ['codigo', 'nombre']


class ModeloLaptopDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloLaptop
        fields = ['codigo', 'nombre']


class ModeloLaptopCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloLaptop
        fields = ['codigo', 'nombre']


# ============================================================================
# MODELO_COMPONENTE SERIALIZERS
# ============================================================================
class ModeloComponenteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloComponente
        fields = ['codigo', 'nombre', 'tipo_componente']


class ModeloComponenteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloComponente
        fields = ['codigo', 'nombre', 'tipo_componente']


class ModeloComponenteCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloComponente
        fields = ['codigo', 'nombre', 'tipo_componente']


# ============================================================================
# EMPLEADO SERIALIZERS
# ============================================================================
class EmpleadoListSerializer(serializers.ModelSerializer):
    turno = serializers.CharField(source='turno.nombre', read_only=True)
    class Meta:
        model = models.Empleado
        fields = ['numero', 'nombrepila', 'primerapell', 'segundoapell', 'turno']


class EmpleadoDetailSerializer(serializers.ModelSerializer):
    turno = serializers.CharField(source='turno.nombre', read_only=True)
    class Meta:
        model = models.Empleado
        fields = ['numero', 'nombrepila', 'primerapell', 'segundoapell', 'rol', 'turno']


class EmpleadoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Empleado
        fields = ['numero', 'nombrepila', 'primerapell', 'segundoapell', 'rol', 'turno']


# ============================================================================
# USUARIO SERIALIZERS
# ============================================================================
class UsuarioListSerializer(serializers.ModelSerializer):
    empleado = EmpleadoListSerializer(read_only=True)
    class Meta:
        model = models.Usuario
        fields = ['numero', 'usuario', 'estado', 'empleado']


class UsuarioDetailSerializer(serializers.ModelSerializer):
    empleado = EmpleadoDetailSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Usuario
        fields = ['numero', 'usuario', 'contrasena', 'estado', 'empleado']


class UsuarioCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        fields = ['numero', 'usuario', 'contrasena', 'empleado']


# ============================================================================
# LINEA SERIALIZERS
# ============================================================================
class LineaListSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Linea
        fields = ['codigo', 'nombre', 'estado']


class LineaDetailSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Linea
        fields = ['codigo', 'nombre', 'descripcion', 'estado']


class LineaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = ['codigo', 'nombre', 'descripcion']


# ============================================================================
# EMPLEADO_LINEA SERIALIZERS
# ============================================================================
class EmpleadoLineaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoLinea
        fields = ['empleado', 'linea', 'fecha_inicio']


class EmpleadoLineaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoLinea
        fields = ['empleado', 'linea', 'fecha_inicio', 'fecha_fin']


class EmpleadoLineaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoLinea
        fields = ['empleado', 'linea', 'fecha_inicio', 'fecha_fin']


# ============================================================================
# ESTACION SERIALIZERS
# ============================================================================
class EstacionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estacion
        fields = ['codigo', 'nombre']


class EstacionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estacion
        fields = ['codigo', 'nombre', 'descripcion', 'linea']


class EstacionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estacion
        fields = ['codigo', 'nombre', 'descripcion', 'linea']


# ============================================================================
# EMPLEADO_ESTACION SERIALIZERS
# ============================================================================
class EmpleadoEstacionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoEstacion
        fields = ['empleado', 'estacion', 'fecha_inicio']


class EmpleadoEstacionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoEstacion
        fields = ['empleado', 'estacion', 'fecha_inicio', 'fecha_fin']


class EmpleadoEstacionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmpleadoEstacion
        fields = ['empleado', 'estacion', 'fecha_inicio', 'fecha_fin']


# ============================================================================
# ORDEN_PRODUCCION SERIALIZERS
# ============================================================================
class OrdenProduccionListSerializer(serializers.ModelSerializer):
    modelo_laptop = ModeloLaptopListSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.OrdenProduccion
        fields = ['folio', 'fecha', 'modelo_laptop', 'estado']


class OrdenProduccionDetailSerializer(serializers.ModelSerializer):
    modelo_laptop = ModeloLaptopDetailSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.OrdenProduccion
        fields = ['folio', 'fecha', 'hora', 'modelo_laptop', 'cant_planificda', 'cant_producida', 'estado']


class OrdenProduccionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenProduccion
        fields = ['folio', 'fecha', 'hora', 'modelo_laptop', 'cant_planificda', 'cant_producida']



# ============================================================================
# ORDEN_MATERIAL SERIALIZERS
# ============================================================================
class OrdenMaterialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'linea']


class OrdenMaterialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'hora', 'linea']


class OrdenMaterialCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'hora', 'linea']

# ============================================================================
# DETALLE_MATERIAL SERIALIZERS
# ============================================================================
class DetalleMaterialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DetalleMaterial
        fields = ['orden', 'modelo']


class DetalleMaterialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DetalleMaterial
        fields = ['orden', 'modelo', 'cantidad']


class DetalleMaterialCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DetalleMaterial
        fields = ['orden', 'modelo', 'cantidad']


# ============================================================================
# COMPONENTE SERIALIZERS
# ============================================================================
class ComponenteListSerializer(serializers.ModelSerializer):
    modelo = ModeloComponenteListSerializer(read_only=True)
    lote = LoteCompListSerializer(read_only=True)
    linea = LineaListSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Componente
        fields = ['numero', 'num_serie', 'modelo', 'lote', 'linea', 'estado']


class ComponenteDetailSerializer(serializers.ModelSerializer):
    modelo = ModeloComponenteDetailSerializer(read_only=True)
    lote = LoteCompDetailSerializer(read_only=True)
    linea = LineaDetailSerializer(read_only=True)
    orden_material = OrdenMaterialDetailSerializer(read_only=True)
    registro_ensamblaje = RegistroEnsamblajeDetailSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Componente
        fields = ['numero', 'num_serie', 'descripcion', 'linea', 'orden_material', 'registro_ensamblaje', 'modelo', 'lote', 'estado']


class ComponenteCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Componente
        fields = ['numero', 'num_serie', 'descripcion', 'linea', 'orden_material', 'registro_ensamblaje', 'modelo', 'lote']


# ============================================================================
# REGISTRO_ENSAMBLAJE SERIALIZERS
# ============================================================================
class RegistroEnsamblajeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEnsamblaje
        fields = ['numero', 'fecha_inicio', 'laptop', 'linea']


class RegistroEnsamblajeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEnsamblaje
        fields = ['numero', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'laptop', 'linea']


class RegistroEnsamblajeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEnsamblaje
        fields = ['numero', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'laptop', 'linea']

# ============================================================================
# LAPTOP SERIALIZERS
# ============================================================================
class LaptopListSerializer(serializers.ModelSerializer):
    modelo = ModeloLaptopListSerializer(read_only=True)
    linea = LineaListSerializer(read_only=True)
    lote = LoteLaptopListSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Laptop
        fields = ['numero', 'descripcion', 'modelo', 'estado', 'linea', 'lote']


class LaptopDetailSerializer(serializers.ModelSerializer):
    modelo = ModeloLaptopDetailSerializer(read_only=True)
    linea = LineaDetailSerializer(read_only=True)
    lote = LoteLaptopDetailSerializer(read_only=True)
    orden = OrdenProduccionDetailSerializer(read_only=True)
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    class Meta:
        model = models.Laptop
        fields = ['numero', 'descripcion', 'orden', 'modelo', 'estado', 'linea', 'lote']


class LaptopCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Laptop
        fields = ['numero', 'descripcion', 'orden', 'modelo', 'linea', 'lote']


# ============================================================================
# ORDEN_MATERIAL SERIALIZERS
# ============================================================================
class OrdenMaterialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'linea']


class OrdenMaterialDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'hora', 'linea']


class OrdenMaterialCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenMaterial
        fields = ['numero', 'fecha', 'hora', 'linea']


# ============================================================================
# INSPECCION_CALIDAD SERIALIZERS
# ============================================================================
class InspeccionCalidadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InspeccionCalidad
        fields = ['numero', 'resultado', 'fecha', 'laptop']


class InspeccionCalidadDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InspeccionCalidad
        fields = ['numero', 'resultado', 'observaciones', 'fecha', 'hora', 'laptop', 'empleado', 'linea']


class InspeccionCalidadCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InspeccionCalidad
        fields = ['numero', 'resultado', 'observaciones', 'fecha', 'hora', 'laptop', 'empleado', 'linea']


# ============================================================================
# PARO SERIALIZERS
# ============================================================================
class ParoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paro
        fields = ['numero', 'razon', 'fecha_inicio', 'linea']


class ParoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paro
        fields = ['numero', 'razon', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'linea']


class ParoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paro
        fields = ['numero', 'razon', 'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin', 'linea']


# ============================================================================
# REGISTRO_EMBALAJE SERIALIZERS
# ============================================================================
class RegistroEmbalajeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEmbalaje
        fields = ['numero', 'fecha', 'laptop', 'tipo']


class RegistroEmbalajeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEmbalaje
        fields = ['numero', 'fecha', 'hora', 'laptop', 'tipo']


class RegistroEmbalajeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroEmbalaje
        fields = ['numero', 'fecha', 'hora', 'laptop', 'tipo']