from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib import messages
import requests

from .forms import get_choices_lineas, get_choices_estaciones
import requests
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages

import requests
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
from django.http import JsonResponse

# Se importa con alias porque las vistas de este módulo tienen su propio
# método get(); un `get` a secas adentro se leería como si fuera el método.
from core.api import fallo, get as api_get, lista, mensaje_error, objeto

from .forms import (
    get_choices_lineas,
    get_choices_estaciones,
    get_choices_roles,
    get_choices_turnos,
)

API_EMPLEADO = "http://127.0.0.1:8000/api/usuarios/Empleado/"


# ===============================
# LISTA (READ)
# ===============================
class ListaEmpleados(generic.View):
    template_name = "usuarios/empleados.html"

    url_api_listar = API_EMPLEADO + "Listar/"
    url_api_buscar = API_EMPLEADO + "Buscar/"
    url_api_actualizar = API_EMPLEADO + "Actualizar/"

    def get(self, request):

        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}


        # filtros
        buscar = request.GET.get("buscar", "").strip()
        rol = request.GET.get("rol", "")
        estado = request.GET.get("estado", "")
        linea = request.GET.get("linea", "")


        params = {}

        if buscar:
            params["buscar"] = buscar

        if rol:
            params["rol"] = rol

        if estado:
            params["estado"] = estado

        if linea:
            params["linea"] = linea



        # Si hay filtros usa Buscar
        if params:
            response = api_get(
                self.url_api_buscar,
                headers,
                params=params,
            )

        else:
            response = api_get(
                self.url_api_listar,
                headers,
            )


        empleados_lista = lista(response)


        empleados = []

        for e in empleados_lista:

            raw_resp = api_get(
                self.url_api_actualizar + f"{e['numero']}/",
                headers,
            )

            raw = objeto(raw_resp)

            empleados.append({
                **e,
                **raw
            })


        context = {

            "empleados": empleados,

            "lineas": get_choices_lineas(token),
            "estaciones": get_choices_estaciones(token),
            "roles": get_choices_roles(token),
            "turnos": get_choices_turnos(token),

            # conservar filtros
            "buscar": buscar,
            "rol": rol,
            "estado": estado,
            "linea": linea,
        }


        return render(
            request,
            self.template_name,
            context
        )

# ===============================
# CREAR (CREATE)
# ===============================
class CrearEmpleado(generic.View):
    url_api = API_EMPLEADO + "Registrar/"

    def post(self, request):
        token = request.session.get("token")

        rol = request.POST.get("rol")

        data = {
            "nombrepila": request.POST.get("nombrepila"),
            "primerapell": request.POST.get("primerapell"),
            "segundoapell": request.POST.get("segundoapell"),
            "rol": rol,
            "turno": request.POST.get("turno"),
        }
        
        if rol == "ADMIN":
            pass
        else:
            linea = request.POST.get("linea")
            if linea:
                data["linea"] = linea

            if rol != "SUPER":
                estacion = request.POST.get("estacion")
                if estacion:
                    data["estacion"] = estacion


        response = requests.post(
            self.url_api,
            headers={"Authorization": f"Bearer {token}"},
            data=data
        )

        if response.status_code == 201:
            resultado = response.json()

            messages.success(
                request,
                f"Empleado registrado correctamente. Número de empleado: {resultado.get('empleado')}"
            )
        else:
            error_data = response.json()
            mensaje = error_data.get(
                "mensaje",
                "No se pudo registrar el empleado."
            )
            messages.error(request, mensaje)

        return redirect("lista_empleados")

# ===============================
# DETALLE (READ individual, opcional)
# ===============================
class DetalleEmpleado(generic.View):
    def get(self, request, numero):
        token = request.session.get("token")
        response = api_get(
            API_EMPLEADO + f"Detalle/{numero}/",
            {"Authorization": f"Bearer {token}"},
        )
        if not fallo(response):
            return render(request, "usuarios/detalle_empleado.html", {"empleado": objeto(response)})

        messages.error(request, "No se pudo obtener el detalle del empleado.")
        return redirect("lista_empleados")

# ===============================
# EDITAR (UPDATE)
# ===============================
class EditarEmpleado(generic.View):

    def post(self, request, numero):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        rol = request.POST.get("rol")

        data = {
            "nombrepila": request.POST.get("nombrepila"),
            "primerapell": request.POST.get("primerapell"),
            "segundoapell": request.POST.get("segundoapell"),
            "rol": rol,
            "turno": request.POST.get("turno"),
        }

        if rol == "SUPER":
            data["linea"] = request.POST.get("linea")
            data["estacion"] = None

        if rol != "ADMIN" and rol != "SUPER":
            if request.POST.get("linea"):
                data["linea"] = request.POST.get("linea")
            if request.POST.get("estacion"):
                data["estacion"] = request.POST.get("estacion")

        response = requests.put(
            API_EMPLEADO + f"Actualizar/{numero}/",
            headers=headers,
            data=data
        )

        if response.status_code == 200:
            messages.success(
                request,
                f"Empleado No. {numero} actualizado correctamente."
            )
        else:
            error_data = response.json()
            messages.error(
                request,
                f"No se pudo actualizar el empleado No. {numero}. "
                + error_data.get("mensaje", "")
            )

        return redirect("lista_empleados")


# ===============================
# DESACTIVAR (baja lógica)
# ===============================
class DesactivarEmpleado(generic.View):

    def post(self, request, numero):
        token = request.session.get("token")

        response = requests.patch(
            API_EMPLEADO + f"Desactivar/{numero}/",
            headers={"Authorization": f"Bearer {token}"},
            data={"activo": False}
        )

        if response.status_code == 200:
            messages.success(
                request,
                f"Empleado No. {numero} desactivado correctamente."
            )
        else:
            messages.error(
                request,
                f"No se pudo desactivar el empleado No. {numero}."
            )

        return redirect("lista_empleados")
    

class ReactivarEmpleado(generic.View):

    def post(self, request, numero):

        token = request.session.get("token")

        response = requests.patch(
            API_EMPLEADO + f"Reactivar/{numero}/",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        if response.status_code == 200:
            messages.success(
                request,
                f"Empleado No. {numero} reactivado correctamente."
            )
        else:
            messages.error(
                request,
                f"No se pudo reactivar el empleado No. {numero}."
            )

        return redirect("lista_empleados")

# ===============================
# PUENTE: estaciones filtradas por línea (para el fetch del JS)
# ===============================
class EstacionesPorLinea(generic.View):
    def get(self, request, linea_id):
        token = request.session.get("token")
        rol_nombre = request.GET.get("rol", "")
        estaciones = get_choices_estaciones(token, linea_id, rol_nombre)
        return JsonResponse([{"codigo": c, "nombre": n} for c, n in estaciones], safe=False)
    
    
    
    




API_USUARIO = "http://127.0.0.1:8000/api/usuarios/Usuario/"


# ===============================
# LISTA USUARIOS
# ===============================
class ListaUsuarios(generic.View):
    template_name = "usuarios/usuarios.html"

    url_api_listar = API_USUARIO + "Listar/"
    url_api_buscar = API_USUARIO + "Buscar/"
    url_api_empleados = API_EMPLEADO + "Listar/"

    def get(self, request):

        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        buscar = request.GET.get("buscar", "")
        rol = request.GET.get("rol", "")
        estado = request.GET.get("estado", "")

        params = {}

        if buscar:
            params["buscar"] = buscar

        if rol:
            params["rol"] = rol

        if estado:
            params["estado"] = estado


        if params:
            response = api_get(
                self.url_api_buscar,
                headers,
                params=params,
            )
        else:
            response = api_get(
                self.url_api_listar,
                headers,
            )


        usuarios = lista(response)


        empleados_resp = api_get(
            self.url_api_empleados,
            headers,
        )

        empleados_lista = lista(empleados_resp)

        empleados = [
            e for e in empleados_lista
            if not e.get("usuario")
        ]


        context = {
            "usuarios": usuarios,
            "empleados": empleados,
            "roles": get_choices_roles(token),
            "buscar": buscar,
            "rol": rol,
            "estado": estado,
        }

        return render(request, self.template_name, context)
    
       
# ==================================================
# CREAR (CREATE)
# ==================================================
class CrearUsuario(generic.View):

    url_api = API_USUARIO + "Registrar/"

    def post(self, request):

        token = request.session.get("token")

        data = {

            "usuario": request.POST.get("usuario"),
            "contrasena": request.POST.get("contrasena"),
            "empleado": request.POST.get("empleado"),

        }

        response = requests.post(
            self.url_api,
            headers={
                "Authorization": f"Bearer {token}"
            },
            data=data
        )


        if response.status_code == 201:

            datos = response.json()

            usuario = datos.get("usuario", {})

            messages.success(
                request,
                f"{datos.get('mensaje')}. "
                f"Usuario: {usuario.get('usuario')} "
                f"(Número: {usuario.get('numero')})."
            )


        else:

            error = response.json()

            messages.error(
                request,
                error.get(
                    "mensaje",
                    "No se pudo registrar el usuario."
                )
            )


        return redirect("lista_usuarios")



# ==================================================
# DETALLE (READ INDIVIDUAL)
# ==================================================
class DetalleUsuario(generic.View):

    template_name = "usuarios/detalle_usuario.html"


    def get(self, request, numero):

        token = request.session.get("token")


        response = api_get(
            API_USUARIO + f"Detalle/{numero}/",
            {
                "Authorization": f"Bearer {token}"
            },
        )


        if not fallo(response):

            return render(
                request,
                self.template_name,
                {
                    "usuario": objeto(response)
                }
            )


        # No se puede hacer response.json() aquí: si la API no contestó,
        # `response` es None. mensaje_error() ya cubre los dos casos.
        messages.error(
            request,
            f"No se pudo obtener el usuario. {mensaje_error(response)}"
        )


        return redirect("lista_usuarios")



# ==================================================
# ACTUALIZAR (UPDATE)
# ==================================================
class EditarUsuario(generic.View):


    def post(self, request, numero):

        token = request.session.get("token")

        data = {
            "usuario": request.POST.get("usuario"),
        }

        contrasena = request.POST.get("contrasena")
        if contrasena:
            data["contrasena"] = contrasena
            admin_password = request.POST.get("admin_password")
            if admin_password:
                data["admin_password"] = admin_password

        response = requests.put(
            API_USUARIO + f"Actualizar/{numero}/",
            headers={
                "Authorization": f"Bearer {token}"
            },
            data=data
        )


        if response.status_code == 200:

            datos = response.json()

            messages.success(
                request,
                f"{datos.get('mensaje')}. Número de usuario: {numero}."
            )


        else:

            error = response.json()

            messages.error(
                request,
                error.get(
                    "mensaje",
                    "No se pudo actualizar el usuario."
                )
            )


        return redirect("lista_usuarios")



class DesactivarUsuario(generic.View):

    def post(self, request, numero):

        token = request.session.get("token")

        response = requests.patch(
            API_USUARIO + f"Desactivar/{numero}/",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        if response.status_code == 200:
            messages.success(
                request,
                "Usuario desactivado correctamente."
            )

        else:
            try:
                error = response.json()
                mensaje = error.get(
                    "mensaje",
                    "No se pudo desactivar el usuario."
                )
            except ValueError:
                mensaje = (
                    "Error al comunicarse con el servidor."
                )

            messages.error(
                request,
                mensaje
            )

        return redirect("lista_usuarios")

# ==================================================
# REACTIVAR USUARIO
# ==================================================
class ReactivarUsuario(generic.View):


    def post(self, request, numero):

        token = request.session.get("token")


        response = requests.patch(

            API_USUARIO + f"Reactivar/{numero}/",

            headers={
                "Authorization": f"Bearer {token}"
            }

        )


        if response.status_code == 200:

            datos = response.json()

            messages.success(
                request,
                f"{datos.get('mensaje')}. Número de usuario: {numero}."
            )


        else:

            error = response.json()

            messages.error(
                request,
                error.get(
                    "mensaje",
                    "No se pudo reactivar el usuario."
                )
            )


        return redirect("lista_usuarios")
    

