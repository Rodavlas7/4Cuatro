from django.db import models

# Create your models here.
"""
Modelos:
   - Linea
   - Estacion
"""

class Estacion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=64, blank=True, null=True)
    linea = models.ForeignKey('Linea', models.DO_NOTHING, db_column='linea', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estacion'

class EdoLinea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_linea'
             
class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=32, blank=True, null=True)
    estado = models.ForeignKey(EdoLinea, models.DO_NOTHING, db_column='estado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'linea'

