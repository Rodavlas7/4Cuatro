from django.db import models
from lineas.models import Linea
# Create your models here.

 
''' AQUI ESTAN LOS MODELS DE:
│    TipoComp
│    EdoComponente
│    LoteComp
│    ModeloComponente
│    OrdenMaterial
│    DetalleMaterial
│    Componente
│    VistaComponente  (mapea la vista SQL vista_componentes, ver DB/vistas.sql)
'''
# Create your models here.
 
 
# TIPOCOMP — catálogo de tipos de componente (Procesador, RAM, SSD, etc.)
class TipoComp(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'tipo_comp'
 
 
# EDOCOMPONENTE — catálogo de estados del componente (Disponible, En Uso, Dañado, Mermado)
class EdoComponente(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'edo_componente'
 
 
# LOTECOMP — catálogo de lotes de componentes
class LoteComp(models.Model):
    codigo = models.CharField(primary_key=True, max_length=12)
    descripcion = models.CharField(max_length=64, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'lote_comp'
 
 
# MODELOCOMPONENTE
class ModeloComponente(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=256, blank=True, null=True)
    tipo_componente = models.ForeignKey(TipoComp, models.DO_NOTHING, db_column='tipo_componente', blank=True, null=True)
    fabricante = models.CharField(max_length=64, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'modelo_componente'
 
 
# ORDENMATERIAL
class OrdenMaterial(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'orden_material'
 
 
# DETALLEMATERIAL — detalle (línea de pedido) de una orden de material.
# La tabla tiene PRIMARY KEY (orden, modelo) y NO tiene columna id, falto declararla compuesta
class DetalleMaterial(models.Model):
    pk = models.CompositePrimaryKey('orden', 'modelo')
    orden = models.ForeignKey(OrdenMaterial, models.DO_NOTHING, db_column='orden')
    modelo = models.ForeignKey(ModeloComponente, models.DO_NOTHING, db_column='modelo')
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_material'
 
 
# COMPONENTE
class Componente(models.Model):
    numero = models.AutoField(primary_key=True)
    num_serie = models.CharField(max_length=18, blank=True, null=True)
    descripcion = models.CharField(max_length=256, blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    orden_material = models.ForeignKey(OrdenMaterial, models.DO_NOTHING, db_column='orden_material', blank=True, null=True)
 
    # NOTA: registro_ensamblaje pertenecea produccion pero ese
    # modelo (RegistroEnsamblaje) aún no existe ahí. Se deja como IntegerField
    # simple -- la integridad ya la garantiza la FK real en MySQL (estructura.sql).
    # Cuando exista produccion.models.RegistroEnsamblaje, subir esto a ForeignKey.
    registro_ensamblaje = models.IntegerField(blank=True, null=True)
 
    modelo = models.ForeignKey(ModeloComponente, models.DO_NOTHING, db_column='modelo', blank=True, null=True)
    lote = models.ForeignKey(LoteComp, models.DO_NOTHING, db_column='lote', blank=True, null=True)
    estado = models.ForeignKey(EdoComponente, models.DO_NOTHING, db_column='estado', blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'componente'
 
 
# VISTACOMPONENTE — consulta general del módulo (vista_componentes en DB/vistas.sql)
class VistaComponente(models.Model):
    numero = models.IntegerField(primary_key=True)
    num_serie = models.CharField(max_length=18, blank=True, null=True)
    descripcion = models.CharField(max_length=256, blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    orden_material = models.IntegerField(blank=True, null=True)
    registro_ensamblaje = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=256, blank=True, null=True)
    modelo_fabricante = models.CharField(max_length=64, blank=True, null=True)
    lote_codigo = models.CharField(max_length=12, blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
 
    class Meta:
        managed = False
        db_table = 'vista_componentes'
