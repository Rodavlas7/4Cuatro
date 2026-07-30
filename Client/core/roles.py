"""Roles del sistema y a qué panel pertenece cada uno.

Este archivo es la única fuente de verdad sobre roles en el cliente. Los códigos
son los mismos que maneja la API (Servicios/usuarios/permissions.py); si allá se
agrega un rol, aquí se agrega su panel.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles. Cámbialo sólo
de acuerdo con el equipo.
"""

# Códigos de rol tal como los devuelve la API en el login.
ROL_ADMIN = 'ADMIN'
ROL_SUPERVISOR = 'SUPER'
ROL_CALIDAD = 'OPCALI'

ROLES_CON_ACCESO = (ROL_ADMIN, ROL_SUPERVISOR, ROL_CALIDAD)

# Nombre para mostrar en pantalla (el código no se le enseña al usuario).
NOMBRE_ROL = {
    ROL_ADMIN: 'Administrador',
    ROL_SUPERVISOR: 'Supervisor',
    ROL_CALIDAD: 'Operador de Calidad',
}

# Dashboard donde cae cada rol al iniciar sesión. Es también el destino al que
# se regresa a alguien que intentó entrar a un panel que no le toca.
PANEL_INICIO = {
    ROL_ADMIN: 'panel_admin:dashboard',
    ROL_SUPERVISOR: 'panel_supervisor:dashboard',
    ROL_CALIDAD: 'panel_calidad:dashboard',
}


def panel_inicio(rol):
    """Nombre de URL del dashboard que le corresponde al rol.

    Devuelve None si el rol es desconocido: quien llama decide qué hacer
    (normalmente mandar al login, porque sin panel no hay nada que mostrar)."""
    return PANEL_INICIO.get(rol)


def nombre_rol(rol):
    """Etiqueta legible del rol; si no se reconoce, se devuelve el código."""
    return NOMBRE_ROL.get(rol, rol or '')
