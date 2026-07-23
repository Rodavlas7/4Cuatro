from django.db import models
from produccion.models import Laptop

# Create your models here.
class TipoEmbalaje(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_embalaje'
        
class RegistroEmbalaje(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    laptop = models.ForeignKey(Laptop, models.DO_NOTHING, db_column='laptop', blank=True, null=True)
    tipo = models.ForeignKey('TipoEmbalaje', models.DO_NOTHING, db_column='tipo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registro_embalaje'
#----------------------------------------VISTA DE EMLABAJE

class VistaRegistroEmbalaje(models.Model):
    numero = models.IntegerField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    laptop_numero = models.IntegerField(blank=True, null=True)
    laptop_num_serie = models.CharField(max_length=50, blank=True, null=True) # Ajusta el max_length al de tu tabla
    tipo_codigo = models.CharField(max_length=8, blank=True, null=True)
    tipo_nombre = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_registro_embalaje'