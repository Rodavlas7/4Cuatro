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
