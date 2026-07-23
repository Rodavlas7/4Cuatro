from django.db import models
from usuarios.models import Empleado
from produccion.models import Laptop, Linea

# Create your models here.

RESULTADO_CHOICES = [
    (1, "Aprobada"),
    (0, "Rechazada"),
    (2, "Continuar ensamblaje"),
]


class InspeccionCalidad(models.Model):

    numero = models.AutoField(primary_key=True)
    resultado = models.IntegerField(choices=RESULTADO_CHOICES, blank=True, null=True)
    observaciones = models.CharField(max_length=256, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField( blank=True, null=True)
    laptop = models.ForeignKey(Laptop, models.DO_NOTHING, db_column='laptop', blank=True, null=True)
    empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='empleado', blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inspeccion_calidad'
        
        
#-------------------------------------VISTA INSPECCION CALIDAD---------------------------------------------

class VistaInspeccionCalidad(models.Model):
    numero = models.IntegerField(primary_key=True)
    resultado = models.IntegerField(blank=True, null=True)
    resultado_nombre = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.CharField(max_length=256, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    laptop_numero = models.IntegerField(blank=True, null=True)
    empleado_id = models.IntegerField(blank=True, null=True)
    empleado_nombre = models.CharField(max_length=256, blank=True, null=True)
    linea_codigo = models.CharField(max_length=50, blank=True, null=True)
    linea_nombre = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_inspeccion_calidad'