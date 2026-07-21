from django.db import models

from lineas.models import Linea
from produccion.models import RegistroEnsamblaje

''' MODELS DE:
│    EdoComponente     (catálogo de apoyo, solo lectura)
│    TipoComp          (catálogo de apoyo, solo lectura)
│    ModeloComponente  (catálogo de apoyo, solo lectura)
│    LoteComp          (catálogo de apoyo, solo lectura)
│    OrdenMaterial     (catálogo de apoyo, solo lectura)
│    Componente        (solo lectura por ahora — se usa anidado en el detalle de Laptop)
'''
# Create your models here.


# EDOCOMPONENTE
class EdoComponente(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_componente'


# TIPOCOMP
class TipoComp(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_comp'


# MODELOCOMPONENTE
class ModeloComponente(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=256, blank=True, null=True)
    tipo_componente = models.ForeignKey(TipoComp, models.DO_NOTHING, db_column='tipo_componente', blank=True, null=True)
    fabricante = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'modelo_componente'


# LOTECOMP
class LoteComp(models.Model):
    codigo = models.CharField(primary_key=True, max_length=12)
    descripcion = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lote_comp'


# ORDENMATERIAL
class OrdenMaterial(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orden_material'


# COMPONENTE
class Componente(models.Model):
    numero = models.AutoField(primary_key=True)
    num_serie = models.CharField(max_length=18, blank=True, null=True)
    descripcion = models.CharField(max_length=256, blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    orden_material = models.ForeignKey(OrdenMaterial, models.DO_NOTHING, db_column='orden_material', blank=True, null=True)
    registro_ensamblaje = models.ForeignKey(RegistroEnsamblaje, models.DO_NOTHING, db_column='registro_ensamblaje', blank=True, null=True)
    modelo = models.ForeignKey(ModeloComponente, models.DO_NOTHING, db_column='modelo', blank=True, null=True)
    lote = models.ForeignKey(LoteComp, models.DO_NOTHING, db_column='lote', blank=True, null=True)
    estado = models.ForeignKey(EdoComponente, models.DO_NOTHING, db_column='estado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'componente'
