"""Modelos del dashboard de administrador.

TODOS son de sólo lectura y TODOS mapean una vista SQL de DB/vistas.sql. Aquí
no se crea, no se modifica y no se borra nada: para eso están las apps de cada
módulo (produccion, calidad, componentes...), que sí escriben a sus tablas.

Por eso esta app existe aparte en lugar de repartir estos modelos entre las
otras: son de otra naturaleza. Las de módulo exponen renglones tal cual; éstas
ya vienen contadas y agrupadas por la base.

Igual que el resto del proyecto, van con managed = False: las vistas las crea
DB/vistas.sql, no las migraciones de Django.

La columna `clave`
------------------
Django exige una llave primaria para mapear cualquier tabla o vista. Las vistas
agrupadas no tienen una columna única natural, así que en la propia vista se
arma una pegando las columnas del GROUP BY (por ejemplo '2026-07-20|LIN001').
No significa nada en el negocio; es sólo el ancla del ORM. No la muestres en
pantalla ni la uses para enlazar.
"""

from django.db import models


# ==================================================
# S E R I E S   P O R   D Í A
# ==================================================
#
# Estas tres agrupan por día. El rango que el admin elige en pantalla NO vive
# en la vista (en MySQL una vista no recibe parámetros): entra como un WHERE
# desde views.py. Un mismo renglón sirve para la tarjeta (suma del rango) y
# para la barra (un día).


class ProduccionDiaria(models.Model):
    """Laptops producidas por día, línea y modelo.

    Producida = embalada. Es el criterio de tg_Registrar_Embalaje,
    y la fecha sale de registro_embalaje porque la tabla laptop no guarda
    ninguna."""

    clave = models.CharField(primary_key=True, max_length=64)
    fecha = models.DateField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_produccion_diaria'


class CalidadDiaria(models.Model):
    """Inspecciones por día y línea, con los tres resultados ya en columnas.

    Los códigos son los de siempre: 1 aprobada, 0 rechazada, 2 continuar
    ensamblaje."""

    clave = models.CharField(primary_key=True, max_length=64)
    fecha = models.DateField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    aprobadas = models.IntegerField(blank=True, null=True)
    rechazadas = models.IntegerField(blank=True, null=True)
    continuar = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_calidad_diaria'


class ParosDiaria(models.Model):
    """Paros por día de inicio y línea, con abiertos y minutos perdidos.

    Un paro sin cerrar aporta 0 minutos: todavía no se sabe cuánto duró."""

    clave = models.CharField(primary_key=True, max_length=64)
    fecha = models.DateField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    abiertos = models.IntegerField(blank=True, null=True)
    minutos = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_paros_diaria'


# ==================================================
# F O T O   D E   A H O R A
# ==================================================


class ResumenPlanta(models.Model):
    """Los conteos que no dependen de fechas, en un solo renglón.

    La vista siempre devuelve exactamente una fila, con clave = 1."""

    clave = models.IntegerField(primary_key=True)

    lineas_totales = models.IntegerField(blank=True, null=True)
    lineas_activas = models.IntegerField(blank=True, null=True)
    lineas_inactivas = models.IntegerField(blank=True, null=True)
    lineas_en_paro = models.IntegerField(blank=True, null=True)
    lineas_en_mantenimiento = models.IntegerField(blank=True, null=True)
    lineas_dadas_de_baja = models.IntegerField(blank=True, null=True)

    ordenes_pendientes = models.IntegerField(blank=True, null=True)
    ordenes_proceso = models.IntegerField(blank=True, null=True)
    ordenes_completadas = models.IntegerField(blank=True, null=True)
    ordenes_canceladas = models.IntegerField(blank=True, null=True)

    laptops_registradas = models.IntegerField(blank=True, null=True)
    laptops_en_ensamblaje = models.IntegerField(blank=True, null=True)
    laptops_aprobadas = models.IntegerField(blank=True, null=True)
    laptops_rechazadas = models.IntegerField(blank=True, null=True)
    laptops_embaladas = models.IntegerField(blank=True, null=True)
    laptops_totales = models.IntegerField(blank=True, null=True)

    comp_disponibles = models.IntegerField(blank=True, null=True)
    comp_en_uso = models.IntegerField(blank=True, null=True)
    comp_danados = models.IntegerField(blank=True, null=True)
    comp_mermados = models.IntegerField(blank=True, null=True)

    paros_abiertos = models.IntegerField(blank=True, null=True)

    empleados_activos = models.IntegerField(blank=True, null=True)
    usuarios_activos = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_resumen_planta'


class StockComponentes(models.Model):
    """Inventario por modelo de componente, repartido en los cuatro estados.

    El umbral de "material bajo" no está en la vista: es decisión de pantalla,
    y lo aplica views.py con ?umbral=N."""

    modelo_codigo = models.CharField(primary_key=True, max_length=8)
    modelo_nombre = models.CharField(max_length=256, blank=True, null=True)
    fabricante = models.CharField(max_length=64, blank=True, null=True)
    tipo_codigo = models.CharField(max_length=8, blank=True, null=True)
    tipo_nombre = models.CharField(max_length=32, blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    disponibles = models.IntegerField(blank=True, null=True)
    en_uso = models.IntegerField(blank=True, null=True)
    danados = models.IntegerField(blank=True, null=True)
    mermados = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_stock_componentes'


class Actividad(models.Model):
    """Línea de tiempo de lo último que pasó, sacada de las cinco tablas que
    guardan fecha y hora (no hay tabla de bitácora en el proyecto).

    `tipo` es EMBALAJE, CALIDAD, ENSAMBLAJE, PARO u ORDEN, y `referencia` es el
    número de la laptop, del paro o el folio de la orden, según el tipo."""

    clave = models.CharField(primary_key=True, max_length=32)
    tipo = models.CharField(max_length=16, blank=True, null=True)
    titulo = models.CharField(max_length=64, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    detalle = models.CharField(max_length=256, blank=True, null=True)
    referencia = models.IntegerField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_actividad'


# ==================================================
# T R A Z A B I L I D A D   P O R   O R D E N
# ==================================================
#
# Las cuatro contestan lo mismo desde cuatro ángulos: "cuéntame todo lo que le
# pasó al folio N". Están separadas porque cada una tiene su granularidad (una
# orden, una laptop, un modelo de componente, un paro) y juntarlas obligaría a
# multiplicar renglones.


class TrazaOrden(models.Model):
    """El encabezado: la orden con su avance y el conteo de todo lo suyo."""

    folio = models.IntegerField(primary_key=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    cant_planificada = models.IntegerField(blank=True, null=True)
    cant_producida = models.IntegerField(blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
    lote_codigo = models.CharField(max_length=8, blank=True, null=True)
    lote_fecha = models.DateField(blank=True, null=True)

    avance = models.IntegerField(blank=True, null=True)

    laptops_totales = models.IntegerField(blank=True, null=True)
    laptops_registradas = models.IntegerField(blank=True, null=True)
    laptops_en_ensamblaje = models.IntegerField(blank=True, null=True)
    laptops_aprobadas = models.IntegerField(blank=True, null=True)
    laptops_rechazadas = models.IntegerField(blank=True, null=True)
    laptops_embaladas = models.IntegerField(blank=True, null=True)

    inspecciones = models.IntegerField(blank=True, null=True)
    inspecciones_rechazadas = models.IntegerField(blank=True, null=True)
    componentes_usados = models.IntegerField(blank=True, null=True)

    ensamblaje_inicio = models.DateField(blank=True, null=True)
    ensamblaje_fin = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_traza_orden'


class TrazaOrdenLaptop(models.Model):
    """Las laptops de la orden, una por renglón, con su paso por ensamblaje,
    calidad y embalaje.

    `ultimo_resultado` es el de la última inspección (1/0/2) o None si nunca
    pasó por calidad."""

    numero = models.IntegerField(primary_key=True)
    num_serie = models.CharField(max_length=50, blank=True, null=True)
    orden_folio = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    estado_codigo = models.CharField(max_length=8, blank=True, null=True)
    estado_nombre = models.CharField(max_length=32, blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    lote_codigo = models.CharField(max_length=8, blank=True, null=True)

    ensamblajes = models.IntegerField(blank=True, null=True)
    ensamblaje_inicio = models.DateField(blank=True, null=True)
    ensamblaje_fin = models.DateField(blank=True, null=True)
    componentes = models.IntegerField(blank=True, null=True)
    inspecciones = models.IntegerField(blank=True, null=True)
    ultimo_resultado = models.IntegerField(blank=True, null=True)
    embalaje_fecha = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_traza_orden_laptops'


class TrazaOrdenComponente(models.Model):
    """Qué material se consumió en la orden, por modelo y lote.

    Sólo cuenta lo que de verdad quedó montado en una laptop de la orden, no
    lo que anda en inventario."""

    clave = models.CharField(primary_key=True, max_length=64)
    orden_folio = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=256, blank=True, null=True)
    fabricante = models.CharField(max_length=64, blank=True, null=True)
    tipo_nombre = models.CharField(max_length=32, blank=True, null=True)
    lote_codigo = models.CharField(max_length=12, blank=True, null=True)
    piezas = models.IntegerField(blank=True, null=True)
    laptops = models.IntegerField(blank=True, null=True)
    mermados = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_traza_orden_componentes'


class TrazaOrdenParo(models.Model):
    """Los paros que le pegaron a la orden.

    No hay vínculo formal entre paro y orden en la base: se cruzan por línea y
    fecha. Es una aproximación, y por eso en pantalla se llama "paros de sus
    líneas" y no "paros de la orden"."""

    clave = models.CharField(primary_key=True, max_length=32)
    orden_folio = models.IntegerField(blank=True, null=True)
    numero = models.IntegerField(blank=True, null=True)
    razon = models.CharField(max_length=256, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    abierto = models.IntegerField(blank=True, null=True)
    minutos = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_traza_orden_paros'
