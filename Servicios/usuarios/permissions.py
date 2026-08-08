from rest_framework.permissions import BasePermission


# ==================================================
# PERMISOS POR ROL
# ==================================================

PERMISOS_ROL = {

    "ADMIN": [
        "usuarios", 
        "empleados",
        "lineas",
        "estaciones",
        "componentes",
        "orden_material",
        "orden_produccion",
        "laptops",
        "ensamblaje",
        "calidad",
        "paro",
        "embalaje",
        "trazabilidad",
        "reportes"
    ],


    "SUPER": [
        "componentes",
        "orden_material",
        "orden_produccion",
        "laptops",
        "ensamblaje",
        "calidad",
        "paro",
        "embalaje",
        "consultas"
    ],


    # El operador de calidad no solo inspecciona: en su línea también registra el
    # ensamblaje y marca las piezas que fallan (panel de calidad, flujo guiado).
    # Para eso necesita leer los registros de ensamblaje de su línea, la laptop y
    # su BOM, y montar o desmontar componentes. Sin estos tres módulos esas
    # llamadas responden 403 y el flujo se queda sin datos.
    "OPCALI": [
        "calidad",
        "consultas",
        "ensamblaje",
        "laptops",
        "componentes"
    ]

}



# ==================================================
# PERMISO GENERAL
# ==================================================

class TienePermisoModulo(BasePermission):
    message = "No cuenta con las credenciales para acceder."

    def has_permission(self, request, view):
        # Verifica que tenga sesión/token
        if not request.user.is_authenticated:
            return False

        # Obtener empleado
        empleado = getattr(
            request.user,
            "empleado",
            None
        )

        if not empleado:
            return False

        # Obtener rol
        rol = empleado.rol.codigo

        # Obtener módulo de la vista
        modulo = getattr(
            view,
            "modulo",
            None
        )
        if not modulo:
            return False

        # Revisar permisos
        permisos = PERMISOS_ROL.get(
            rol,
            []
        )

        return modulo in permisos