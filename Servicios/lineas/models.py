from django.db import models

''' AQUI ESTAN LOS MODELS DE:
│    EdoLinea
│    Linea
│    Estacion
│    VistaLinea      (mapea la vista SQL vista_lineas, ver DB/vistas.sql)
'''
# Create your models here.


# EDOLINEA
class EdoLinea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_linea'


# LINEA
class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    estado = models.ForeignKey(EdoLinea, models.DO_NOTHING, db_column='estado', blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'linea'


# ESTACION
class Estacion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estacion'


# VISTALINEA — consulta general del módulo (vista_lineas en DB/vistas.sql)
class VistaLinea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    total_estaciones = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_lineas'

