from django.db import models

''' AQUI ESTAN LOS MODELS DE:
│    EdoLinea
│    TipoLinea
│    Linea
│    Estacion
│    VistaLinea      (mapea la vista SQL vista_lineas, ver DB/vistas.sql)
│    VistaEstacion   (mapea la vista SQL vista_estaciones, ver DB/vistas.sql)
'''
# Create your models here.


# Tipo de línea de ensamblaje. Es el único en el que se puede registrar
# ensamblaje; lo revisan la API, el procedimiento y el trigger de la base.
TIPO_LINEA_ENSAMBLAJE = 'ENSA'

# Tipo de línea de embalaje.
TIPO_LINEA_EMBALAJE = 'EMBA'


# EDOLINEA
class EdoLinea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_linea'


# TIPOLINEA — qué proceso corre la línea (ensamblaje o embalaje).
# Ojo: no confundir con EdoLinea. El estado dice CÓMO ESTÁ la línea (activa,
# en paro, en mantenimiento); el tipo dice PARA QUÉ SIRVE, y es lo que decide
# si en ella se puede registrar ensamblaje.
class TipoLinea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_linea'


# LINEA
class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    tipo = models.ForeignKey(TipoLinea, models.DO_NOTHING, db_column='tipo', blank=True, null=True)
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
    tipo_codigo = models.CharField(max_length=8, blank=True, null=True)
    tipo_nombre = models.CharField(max_length=32, blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    total_estaciones = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_lineas'


# VISTAESTACION — consulta general de estaciones (vista_estaciones en DB/vistas.sql)
class VistaEstacion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    total_empleados = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_estaciones'
