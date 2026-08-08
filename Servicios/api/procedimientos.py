"""Llamadas a los procedimientos almacenados de DB/procedimientos.sql.

Por qué a mano y no por el ORM: los modelos son `managed = False` y esto no es
CRUD sobre una tabla, es una operación que la base resuelve entera. Django no
tiene nada que aportar en medio, así que se baja a cursor.

ES COMPARTIDO: lo usan todos los módulos de la API.
"""

from django.db import connection, transaction


def llamar(nombre, *argumentos):
    """Ejecuta el procedimiento y devuelve su SELECT de resumen como diccionario.

    Todos los procedimientos terminan con un SELECT de una sola fila (ver el
    encabezado de DB/procedimientos.sql: se usa SELECT y no parámetros OUT
    porque los OUT quedan en variables de sesión que habría que ir a consultar
    aparte).

    Los errores NO se atrapan aquí a propósito: suben como DatabaseError para
    que la vista los traduzca con api.errores. Así el mensaje del SIGNAL llega
    completo a quien sabe convertirlo en respuesta HTTP.
    """
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.callproc(nombre, argumentos)

        if cursor.description is None:
            return {}

        columnas = [c[0] for c in cursor.description]
        fila = cursor.fetchone()

        return dict(zip(columnas, fila)) if fila else {}
