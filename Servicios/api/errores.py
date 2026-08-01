"""Traducción de los errores de MySQL a respuestas que se puedan leer.

Aquí se atrapa y se devuelve un 400 con el motivo en la clave "mensaje", que es
la que ya lee core.api.mensaje_error del cliente.

ES COMPARTIDO: lo usan todos los módulos de la API.
"""

from django.db import DatabaseError
from rest_framework.exceptions import ValidationError

MYSQL_LLAVE_DUPLICADA = 1062
MYSQL_FK_EN_USO = 1451        # borrar un padre que todavía tiene hijos
MYSQL_FK_INEXISTENTE = 1452   # apuntar a un padre que no existe
MYSQL_SIGNAL = 1644           # el SIGNAL SQLSTATE '45000' de triggers y procedimientos


def mensaje_de_base(error):
    """Traduce el error crudo de MySQL a algo que se pueda mostrar en pantalla."""

    codigo = error.args[0] if error.args else None
    texto = str(error.args[1]) if len(error.args) > 1 else str(error)

    if codigo == MYSQL_SIGNAL:
        # El trigger o el procedimiento ya traen el motivo redactado en español;
        # sólo se les quita el prefijo técnico "Error tg_Nombre:" / "Error sp_Nombre:".
        return texto.split(':', 1)[-1].strip()

    if codigo == MYSQL_FK_EN_USO:
        return 'No se puede eliminar: hay registros que todavía dependen de este.'

    if codigo == MYSQL_FK_INEXISTENTE:
        return 'Alguno de los datos relacionados no existe.'

    if codigo == MYSQL_LLAVE_DUPLICADA:
        return 'Ya existe un registro con esa llave.'

    return 'La base de datos rechazó la operación.'


def como_validacion(error):
    """El error de la base, envuelto para que DRF lo saque como un 400.

    Para las vistas que no son genéricas y no pueden usar ErroresDeBaseMixin."""
    return ValidationError({'mensaje': mensaje_de_base(error)})


class ErroresDeBaseMixin:
    """Devuelve 400 con el motivo cuando la base rechaza un alta, cambio o baja.

    Va SIEMPRE primero en la lista de bases, para que su perform_* se ejecute
    antes que el de la vista genérica de DRF."""

    def _intentar(self, accion, argumento):
        try:
            accion(argumento)
        except DatabaseError as error:
            raise como_validacion(error)

    def perform_create(self, serializer):
        self._intentar(super().perform_create, serializer)

    def perform_update(self, serializer):
        self._intentar(super().perform_update, serializer)

    def perform_destroy(self, instance):
        self._intentar(super().perform_destroy, instance)
