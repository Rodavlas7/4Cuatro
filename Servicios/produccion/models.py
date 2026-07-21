from django.db import models

from lineas.models import Linea

''' MODELS DE:
│    EdoProduccion
│    ModeloLaptop    (catálogo de apoyo, solo lectura)
│    EdoLaptop       (catálogo de apoyo, solo lectura)
│    LoteLaptop      (catálogo de apoyo, solo lectura)
│    OrdenProduccion
│    Paro
│    Laptop
│    RegistroEnsamblaje
│    VistaOrdenProduccion  (mapea la vista SQL vista_ordenes_produccion, ver DB/vistas.sql)
│    VistaParo             (mapea la vista SQL vista_paros, ver DB/vistas.sql)
│    VistaLaptop           (mapea la vista SQL vista_laptops, ver DB/vistas.sql)
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


# EDOLAPTOP
class EdoLaptop(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_laptop'


# LOTELAPTOP
class LoteLaptop(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    fecha = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lote_laptop'


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


# LAPTOP
class Laptop(models.Model):
    numero = models.AutoField(primary_key=True)
    num_serie = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=256, blank=True, null=True)
    orden = models.ForeignKey(OrdenProduccion, models.DO_NOTHING, db_column='orden', blank=True, null=True)
    modelo = models.ForeignKey(ModeloLaptop, models.DO_NOTHING, db_column='modelo', blank=True, null=True)
    estado = models.ForeignKey(EdoLaptop, models.DO_NOTHING, db_column='estado', blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    lote = models.ForeignKey(LoteLaptop, models.DO_NOTHING, db_column='lote', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'laptop'


# REGISTROENSAMBLAJE
class RegistroEnsamblaje(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    laptop = models.ForeignKey(Laptop, models.DO_NOTHING, db_column='laptop', blank=True, null=True)
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registro_ensamblaje'


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


# VISTAPARO — consulta general de paros (vista_paros en DB/vistas.sql)
class VistaParo(models.Model):
    numero = models.IntegerField(primary_key=True)
    razon = models.CharField(max_length=256, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    abierto = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_paros'


# VISTALAPTOP — consulta general de laptops (vista_laptops en DB/vistas.sql)
class VistaLaptop(models.Model):
    numero = models.IntegerField(primary_key=True)
    num_serie = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=256, blank=True, null=True)
    orden_folio = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    lote_codigo = models.CharField(max_length=8, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_laptops'
