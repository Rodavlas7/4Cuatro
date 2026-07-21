from django.db import models
from lineas.models import Estacion, Linea


''' AQUI ESTAN LOS MODELS DE:
│   - Empleado
│   - Usuario
│   - Rol
│   - Turno
│   - Sesion
│   - EmpleadoLinea  
│   - EmpleadoEstacion 
'''
# Create your models here.

#------------------ ROL--------------------
class Rol(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    descripcion = models.CharField(max_length=130, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rol'
        
#------------------ TURNO--------------------
class Turno(models.Model):
    codigo = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(unique=True, max_length=32, blank=True, null=True)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'turno'
        
#------------------ EMPLEADO--------------------
class Empleado(models.Model):
    numero = models.AutoField(primary_key=True)
    nombrepila = models.CharField(db_column='nombrePila', max_length=50, blank=True, null=True)
    primerapell = models.CharField(db_column='primerApell', max_length=32, blank=True, null=True)
    segundoapell = models.CharField(db_column='segundoApell', max_length=32, blank=True, null=True)
    rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='rol', blank=True, null=True)
    turno = models.ForeignKey(Turno, models.DO_NOTHING, db_column='turno', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empleado'
    

class EmpleadoEstacion(models.Model):
    pk = models.CompositePrimaryKey('empleado', 'estacion', 'fecha_inicio')
    empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='empleado')
    estacion = models.ForeignKey('lineas.Estacion', models.DO_NOTHING, db_column='estacion')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empleado_estacion'


class EmpleadoLinea(models.Model):
    pk = models.CompositePrimaryKey('empleado', 'linea', 'fecha_inicio')
    empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='empleado')
    linea = models.ForeignKey('lineas.Linea', models.DO_NOTHING, db_column='linea')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empleado_linea'
        
#------------------ USUARIO--------------------
class Usuario(models.Model):
    numero = models.AutoField(primary_key=True)
    usuario = models.CharField(unique=True, max_length=32, blank=True, null=True)
    contrasena = models.CharField(max_length=128, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)
    empleado = models.OneToOneField(Empleado, models.DO_NOTHING, db_column='empleado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuario'
        
        
#------------------ SESION--------------------        
class Sesion(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column="usuario"
    )
    token = models.CharField(max_length=64, unique=True)
    fecha_inicio = models.DateTimeField()
    fecha_expiracion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "sesion"