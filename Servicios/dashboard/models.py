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


class TiempoLineaDiaria(models.Model):
    """Cuánto tarda una laptop en cada línea, por día, línea y modelo.

    Sólo entran las pasadas ya cerradas: una que sigue abierta tiene un tiempo
    que todavía crece y movería el promedio con sólo recargar la pantalla.

    Para el promedio de un RANGO hay que dividir las sumas
    (minutos_turno / pasadas), no promediar los `promedio_*`: eso le daría el
    mismo peso a un día de 2 laptops que a uno de 200."""

    clave = models.CharField(primary_key=True, max_length=64)
    fecha = models.DateField(blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)

    pasadas = models.IntegerField(blank=True, null=True)
    laptops = models.IntegerField(blank=True, null=True)

    minutos_brutos = models.IntegerField(blank=True, null=True)
    minutos_turno = models.IntegerField(blank=True, null=True)
    promedio_brutos = models.IntegerField(blank=True, null=True)
    promedio_turno = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_dash_tiempo_linea_diaria'


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
# T I E M P O   E N   L Í N E A
# ==================================================
#
# Todo lo de aquí abajo trae los minutos POR PARTIDA DOBLE, y así se muestran en
# pantalla:
#
#   *_brutos  El reloj de pared, sin quitarle nada.
#   *_turno   Lo mismo pero descontando lo que cayó fuera del horario de planta
#             (la tabla `turno`: hoy 06:00 a 22:00). Una laptop que se queda en
#             la línea del viernes a las 21:00 al lunes a las 07:00 no estuvo 3
#             días ensamblándose, estuvo 2 horas.
#
# Van los dos porque contestan cosas distintas: el bruto es lo que espera quien
# pidió la unidad, el de turno es contra lo que se mide a la línea. El recorte lo
# hace fn_Minutos_En_Turno en DB/vistas.sql, no Python.
#
# Una pasada sin cerrar cuenta hasta la hora del equipo, así que su número crece
# entre una consulta y otra. Es a propósito: es lo que deja ver cuánto lleva
# atorada una laptop que sigue en la línea.


class TiempoLinea(models.Model):
    """Una pasada: el paso de una laptop por una línea (un registro_ensamblaje).

    `abierto` en 1 quiere decir que la laptop sigue en esa línea y que sus
    minutos van corriendo contra la hora actual.

    La vista SQL también trae `inicio` y `fin` ya armados como DATETIME, pero
    aquí se declaran nada más las columnas sueltas de fecha y hora, que es como
    el resto del proyecto expone sus tiempos."""

    numero = models.IntegerField(primary_key=True)
    laptop_numero = models.IntegerField(blank=True, null=True)
    laptop_num_serie = models.CharField(max_length=50, blank=True, null=True)
    orden_folio = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)
    linea_codigo = models.CharField(max_length=8, blank=True, null=True)
    linea_nombre = models.CharField(max_length=32, blank=True, null=True)

    fecha_inicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)

    abierto = models.IntegerField(blank=True, null=True)
    minutos_brutos = models.IntegerField(blank=True, null=True)
    minutos_turno = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_tiempo_linea'


class TiempoLaptop(models.Model):
    """El acumulado de una laptop, sumando todas las líneas por las que pasó.

    Los dos pares NO miden lo mismo:

      minutos_*  Lo que estuvo DENTRO de una línea (la suma de sus pasadas).
      ciclo_*    Lo que tardó de punta a punta, de la primera línea a la última.

    La diferencia entre ambos es lo que la laptop pasó ESPERANDO entre líneas,
    normalmente esperando inspección. Ahí es donde se atoran las órdenes.

    Una laptop apenas registrada, sin ninguna pasada todavía, no aparece: la
    vista sale de vista_tiempo_linea."""

    laptop = models.IntegerField(primary_key=True)
    num_serie = models.CharField(max_length=50, blank=True, null=True)
    orden_folio = models.IntegerField(blank=True, null=True)
    modelo_codigo = models.CharField(max_length=8, blank=True, null=True)
    modelo_nombre = models.CharField(max_length=32, blank=True, null=True)

    pasos = models.IntegerField(blank=True, null=True)
    pasos_abiertos = models.IntegerField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)

    minutos_brutos = models.IntegerField(blank=True, null=True)
    minutos_turno = models.IntegerField(blank=True, null=True)
    ciclo_brutos = models.IntegerField(blank=True, null=True)
    ciclo_turno = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vista_tiempo_laptop'


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

    promedio_brutos = models.IntegerField(blank=True, null=True)
    promedio_turno = models.IntegerField(blank=True, null=True)

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

    # Los cuatro tiempos de TiempoLaptop, traídos con LEFT JOIN: vienen en None
    # si la laptop todavía no ha entrado a ninguna línea.
    minutos_brutos = models.IntegerField(blank=True, null=True)
    minutos_turno = models.IntegerField(blank=True, null=True)
    ciclo_brutos = models.IntegerField(blank=True, null=True)
    ciclo_turno = models.IntegerField(blank=True, null=True)

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
