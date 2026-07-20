from django.db import models

from lineas.models import Linea

''' AQUI ESTAN LOS MODELS DE:
│    EdoProduccion
│    ModeloLaptop    (catálogo de apoyo, solo lectura)
│    OrdenProduccion
│    Paro
│    VistaOrdenProduccion  (mapea la vista SQL vista_ordenes_produccion, ver DB/vistas.sql)
'''
# Create your models here.


# EDOPRODUCCION
class EdoProduccion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_produccion'


# MODELOLAPTOP
class ModeloLaptop(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'modelo_laptop'


# ORDENPRODUCCION
class OrdenProduccion(models.Model):
    folio = models.AutoField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    modelo_laptop = models.ForeignKey(ModeloLaptop, models.DO_NOTHING, db_column='modelo_laptop', blank=True, null=True)
    cant_planificada = models.IntegerField(blank=True, null=True, default=0)
    cant_producida = models.IntegerField(blank=True, null=True, default=0)
    estado = models.ForeignKey(EdoProduccion, models.DO_NOTHING, db_column='estado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orden_produccion'


# PARO
class Paro(models.Model):
    numero = models.AutoField(primary_key=True)
    razon = models.CharField(max_length=256, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paro'


# VISTAORDENPRODUCCION — consulta general del módulo (vista_ordenes_produccion en DB/vistas.sql)
class VistaOrdenProduccion(models.Model):
    folio = models.IntegerField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    cant_planificada = models.IntegerField(blank=True, null=True)
    cant_producida = models.IntegerField(blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_ordenes_produccion'
