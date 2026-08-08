from django.db import models
from usuarios.models import Empleado
from produccion.models import Laptop, Linea
from componentes.models import Componente

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
        
        
class DetalleInspeccion(models.Model):
    """Qué piezas concretas reprobó una inspección.

    La inspección dice si la laptop pasa o no; esto dice POR CUÁL componente no
    pasó. Es lo que permite cruzar fallas contra lote o proveedor: sin esto el
    motivo solo vivía en el texto libre de `observaciones`.

    Llave compuesta (inspeccion, componente), igual que detalle_material.
    """
    pk = models.CompositePrimaryKey('inspeccion', 'componente')
    inspeccion = models.ForeignKey(InspeccionCalidad, models.DO_NOTHING, db_column='inspeccion')
    componente = models.ForeignKey(Componente, models.DO_NOTHING, db_column='componente')
    observacion = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_inspeccion'


#-------------------------------------VISTA INSPECCION CALIDAD---------------------------------------------

class VistaInspeccionCalidad(models.Model):
    numero = models.IntegerField(primary_key=True)
    resultado = models.IntegerField(blank=True, null=True)
    resultado_nombre = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.CharField(max_length=256, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)

    laptop_numero = models.IntegerField(blank=True, null=True)
    laptop_num_serie = models.CharField(max_length=50, blank=True, null=True)

    empleado_id = models.IntegerField(blank=True, null=True)
    empleado_nombre = models.CharField(max_length=256, blank=True, null=True)

    linea_codigo = models.CharField(max_length=50, blank=True, null=True)
    linea_nombre = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_inspeccion_calidad'