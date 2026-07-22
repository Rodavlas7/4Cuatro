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


    "OPCALI": [
        "calidad",
        "consultas"
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
        print("====================")
        print("USUARIO:", request.user.usuario)
        print("ROL:", rol)
        print("MODULO:", modulo)
        print("PERMISOS:", permisos)
        print("TIENE PERMISO:", modulo in permisos)
        print("====================")

        return modulo in permisos