from django.db import models

# Create your models here.
# 1
class Rol(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    descripcion = models.CharField(max_length=130)

    class Meta:
        db_table = "rol"

    def _str_(self):
        return self.nombre


# 2
class Turno(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    class Meta:
        db_table = "turno"

    def _str_(self):
        return self.nombre


# 3
class EdoLinea(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    descripcion = models.CharField(max_length=128)

    class Meta:
        db_table = "edo_linea"

    def _str_(self):
        return self.nombre


# 4
class TipoComp(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "tipo_comp"

    def _str_(self):
        return self.nombre


# 5
class EdoComponente(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    descripcion = models.CharField(max_length=64)

    class Meta:
        db_table = "edo_componente"

    def _str_(self):
        return self.nombre


# 6
class LoteComp(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    descripcion = models.CharField(max_length=64)

    class Meta:
        db_table = "lote_comp"

    def _str_(self):
        return self.codigo


# 7
class TipoEmbalaje(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "tipo_embalaje"

    def _str_(self):
        return self.nombre


# 8
class EdoProduccion(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "edo_produccion"

    def _str_(self):
        return self.nombre


# 9
class LoteLaptop(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    fecha = models.DateField()

    class Meta:
        db_table = "lote_laptop"

    def _str_(self):
        return self.codigo


# 10
class EdoLaptop(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "edo_laptop"

    def _str_(self):
        return self.nombre
    
    
    # 11
class ModeloLaptop(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        db_table = "modelo_laptop"

    def __str__(self):
        return self.nombre


# 12
class Empleado(models.Model):
    numero = models.AutoField(primary_key=True)
    nombrePila = models.CharField(max_length=50)
    primerApell = models.CharField(max_length=32)
    segundoApell = models.CharField(max_length=32, null=True, blank=True)

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)

    class Meta:
        db_table = "empleado"

    def __str__(self):
        return self.nombrePila


# 13
class Usuario(models.Model):
    numero = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=32, unique=True)
    contrasena = models.CharField(max_length=32)
    estado = models.BooleanField()

    empleado = models.OneToOneField(
        Empleado,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.usuario


# 14
class Linea(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    descripcion = models.CharField(max_length=32)
    estado = models.ForeignKey(EdoLinea, on_delete=models.CASCADE)

    class Meta:
        db_table = "linea"

    def __str__(self):
        return self.nombre


# 15
class EmpleadoLinea(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = "empleado_linea"
        unique_together = ("empleado", "linea", "fecha_inicio")


# 16
class Estacion(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=32)
    descripcion = models.CharField(max_length=64)

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "estacion"

    def __str__(self):
        return self.nombre


# 17
class EmpleadoEstacion(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    estacion = models.ForeignKey(
        Estacion,
        on_delete=models.CASCADE
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        db_table = "empleado_estacion"
        unique_together = ("empleado", "estacion", "fecha_inicio")


# 18
class OrdenProduccion(models.Model):
    folio = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()

    modelo_laptop = models.ForeignKey(
        ModeloLaptop,
        on_delete=models.CASCADE
    )

    estado = models.ForeignKey(
        EdoProduccion,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "orden_produccion"


# 19
class Laptop(models.Model):
    numero = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=256)

    orden = models.ForeignKey(
        OrdenProduccion,
        on_delete=models.CASCADE
    )

    modelo = models.ForeignKey(
        ModeloLaptop,
        on_delete=models.CASCADE
    )

    estado = models.ForeignKey(
        EdoLaptop,
        on_delete=models.CASCADE
    )

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    lote = models.ForeignKey(
        LoteLaptop,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "laptop"


# 20
class RegistroEnsamblaje(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    laptop = models.ForeignKey(
        Laptop,
        on_delete=models.CASCADE
    )

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "registro_ensamblaje"


# 21
class Paro(models.Model):
    numero = models.AutoField(primary_key=True)
    razon = models.CharField(max_length=256)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "paro"


# 22
class ModeloComponente(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    nombre = models.CharField(max_length=256)

    tipo_componente = models.ForeignKey(
        TipoComp,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "modelo_componente"


# 23
class OrdenMaterial(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "orden_material"


# 24
class DetalleMaterial(models.Model):
    orden = models.ForeignKey(
        OrdenMaterial,
        on_delete=models.CASCADE
    )

    modelo = models.ForeignKey(
        ModeloComponente,
        on_delete=models.CASCADE
    )
    cantidad = models.IntegerField()

    class Meta:
        db_table = "detalle_material"
        unique_together = ("orden", "modelo")


# 25
class Componente(models.Model):
    numero = models.AutoField(primary_key=True)
    num_serie = models.CharField(max_length=18)
    descripcion = models.CharField(max_length=256)
    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    orden_material = models.ForeignKey(
        OrdenMaterial,
        on_delete=models.CASCADE
    )

    registro_ensamblaje = models.ForeignKey(
        RegistroEnsamblaje,
        on_delete=models.CASCADE,
        null=True
    )

    modelo = models.ForeignKey(
        ModeloComponente,
        on_delete=models.CASCADE
    )

    lote = models.ForeignKey(
        LoteComp,
        on_delete=models.CASCADE
    )

    estado = models.ForeignKey(
        EdoComponente,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "componente"


# 26
class InspeccionCalidad(models.Model):
    numero = models.AutoField(primary_key=True)
    resultado = models.BooleanField()
    observaciones = models.CharField(max_length=256)
    fecha = models.DateField()
    hora = models.TimeField()

    laptop = models.ForeignKey(
        Laptop,
        on_delete=models.CASCADE
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE
    )

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "inspeccion_calidad"


# 27
class RegistroEmbalaje(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    
    laptop = models.ForeignKey(
        Laptop,
        on_delete=models.CASCADE
    )

    tipo = models.ForeignKey(
        TipoEmbalaje,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "registro_embalaje"