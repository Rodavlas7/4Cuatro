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

        buscar = request.GET.get("buscar", "").strip()

        if buscar:
            response = requests.get(self.url_api_buscar, headers=headers, params={"buscar": buscar})
        else:
            response = requests.get(self.url_api_listar, headers=headers)

        empleados_lista = response.json() if response.status_code == 200 else []

        empleados = []
        for e in empleados_lista:
            raw_resp = requests.get(self.url_api_actualizar + f"{e['numero']}/", headers=headers)
            raw = raw_resp.json() if raw_resp.status_code == 200 else {}
            empleados.append({**e, **raw})

        context = {
            "empleados": empleados,
            "lineas": get_choices_lineas(token),
            "estaciones": get_choices_estaciones(token),
            "roles": get_choices_roles(token),
            "turnos": get_choices_turnos(token),
            "buscar": buscar,
        }
        return render(request, self.template_name, context)

# ===============================
# CREAR (CREATE)
# ===============================
class CrearEmpleado(generic.View):
    url_api = API_EMPLEADO + "Registrar/"

    def post(self, request):
        token = request.session.get("token")
        data = {
            "nombrepila": request.POST.get("nombrepila"),
            "primerapell": request.POST.get("primerapell"),
            "segundoapell": request.POST.get("segundoapell"),
            "rol": request.POST.get("rol"),
            "turno": request.POST.get("turno"),
            "linea": request.POST.get("linea"),
            "estacion": request.POST.get("estacion"),
        }

        response = requests.post(
            self.url_api,
            headers={"Authorization": f"Bearer {token}"},
            data=data
        )

        if response.status_code == 201:
            empleado = response.json()

            messages.success(
                request,
                f"Empleado registrado correctamente. Número de empleado: {empleado.get('numero')}"
            )
        else:
            error_data = response.json()
            mensaje = error_data.get("mensaje", "No se pudo registrar el empleado.")
            messages.error(request, mensaje)

        return redirect("lista_empleados")


# ===============================
# DETALLE (READ individual, opcional)
# ===============================
class DetalleEmpleado(generic.View):
    def get(self, request, numero):
        token = request.session.get("token")
        response = requests.get(
            API_EMPLEADO + f"Detalle/{numero}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return render(request, "usuarios/detalle_empleado.html", {"empleado": response.json()})

        messages.error(request, "No se pudo obtener el detalle del empleado.")
        return redirect("lista_empleados")


# ===============================
# EDITAR (UPDATE)
# ===============================
class EditarEmpleado(generic.View):

    def post(self, request, numero):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        data = {
            "nombrepila": request.POST.get("nombrepila"),
            "primerapell": request.POST.get("primerapell"),
            "segundoapell": request.POST.get("segundoapell"),
            "rol": request.POST.get("rol"),
            "turno": request.POST.get("turno"),
        }
        if request.POST.get("linea"):
            data["linea"] = request.POST.get("linea")
        if request.POST.get("estacion"):
            data["estacion"] = request.POST.get("estacion")

        response = requests.put(
            API_EMPLEADO + f"Actualizar/{numero}/",
            headers=headers,
            data=data
        )

        if response.status_code != 200:
            error_data = response.json()
            messages.error(
                request,
                f"No se pudo actualizar el empleado No. {numero}. "
                + error_data.get("mensaje", "")
            )
            return redirect("lista_empleados")

        activo = request.POST.get("activo") == "true"
        estado_resp = requests.patch(
            API_EMPLEADO + f"Desactivar/{numero}/",
            headers=headers,
            data={"activo": activo}
        )

        if estado_resp.status_code == 200:
            messages.success(
                request,
                f"Empleado No. {numero} actualizado correctamente."
            )
        else:
            messages.warning(
                request,
                f"Empleado No. {numero} actualizado, pero no se pudo cambiar el estado."
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


# ===============================
# PUENTE: estaciones filtradas por línea (para el fetch del JS)
# ===============================
class EstacionesPorLinea(generic.View):
    def get(self, request, linea_id):
        token = request.session.get("token")
        estaciones = get_choices_estaciones(token, linea_id)
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

        buscar = request.GET.get("buscar", "").strip()

        if buscar:
            response = requests.get(
                self.url_api_buscar,
                headers=headers,
                params={"buscar": buscar}
            )
        else:
            response = requests.get(self.url_api_listar, headers=headers)

        usuarios = response.json() if response.status_code == 200 else []

        empleados_resp = requests.get(self.url_api_empleados, headers=headers)
        empleados = empleados_resp.json() if empleados_resp.status_code == 200 else []

        context = {
            "usuarios": usuarios,
            "empleados": empleados,
            "buscar": buscar,
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


        response = requests.get(
            API_USUARIO + f"Detalle/{numero}/",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )


        if response.status_code == 200:

            return render(
                request,
                self.template_name,
                {
                    "usuario": response.json()
                }
            )


        error = response.json()

        messages.error(
            request,
            error.get(
                "mensaje",
                "No se pudo obtener el usuario."
            )
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
            "contrasena": request.POST.get("contrasena"),
            "empleado": request.POST.get("empleado"),

        }


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
    
