"""Asignación de empleados a líneas (tabla empleado_linea).

Vive aquí y no dentro de una vista porque la usan dos módulos: la edición de
empleados y la pantalla de supervisores de una línea (panel de administrador).

empleado_linea es M a M en los dos sentidos: una línea puede tener varios
empleados y un empleado puede estar en varias líneas. Quien decide cuántas le
tocan a cada quien es la vista, no la tabla:

- A un supervisor se le SUMAN líneas: puede llevar más de una.
- A los demás roles se les cambia la línea, o sea que antes de asignarles la
  nueva se cierran las que traían.

Dos reglas de la tabla que hay que respetar desde cualquiera de los dos lados:

- La llave primaria es (empleado, linea, fecha_inicio). Volver a asignar el
  mismo día una línea que se quitó ese mismo día no cabe como renglón nuevo:
  hay que reabrir el que ya está.
- Vigente = fecha_fin nula. Quitar una línea le pone fecha_fin en lugar de
  borrar el renglón, para no perder quién estaba dónde y desde cuándo.
"""

from django.utils import timezone

from .models import EmpleadoLinea


def vigentes(empleado):
    """Asignaciones abiertas del empleado (las que no tienen fecha_fin)."""
    return EmpleadoLinea.objects.filter(
        empleado=empleado,
        fecha_fin__isnull=True
    )


def tiene_linea(empleado, linea_codigo):
    return vigentes(empleado).filter(linea_id=linea_codigo).exists()


def asignar(empleado, linea_codigo):
    """Deja al empleado asignado a esa línea desde hoy, sin tocar las demás.

    Devuelve True si hubo cambio y False si ya la tenía, para que quien llama
    pueda avisar lo que de verdad pasó."""

    if tiene_linea(empleado, linea_codigo):
        return False

    hoy = timezone.now().date()

    del_mismo_dia = EmpleadoLinea.objects.filter(
        empleado=empleado,
        linea_id=linea_codigo,
        fecha_inicio=hoy
    ).first()

    if del_mismo_dia is not None:
        del_mismo_dia.fecha_fin = None
        del_mismo_dia.save(update_fields=['fecha_fin'])
        return True

    EmpleadoLinea.objects.create(
        empleado=empleado,
        linea_id=linea_codigo,
        fecha_inicio=hoy
    )

    return True


def cerrar_todas(empleado):
    """Cierra hoy todas las asignaciones vigentes del empleado."""
    return vigentes(empleado).update(fecha_fin=timezone.now().date())


def quitar(empleado_numero, linea_codigo):
    """Cierra hoy la asignación vigente de ese empleado en esa línea.

    Devuelve cuántos renglones se cerraron: 0 quiere decir que no estaba
    asignado, y quien llama decide si eso es un 404."""
    return EmpleadoLinea.objects.filter(
        empleado_id=empleado_numero,
        linea_id=linea_codigo,
        fecha_fin__isnull=True
    ).update(fecha_fin=timezone.now().date())
