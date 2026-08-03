from datetime import date, timedelta
from secrets import token_hex

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lineas.models import Estacion, Linea

from usuarios import models, serializers

from .models import Sesion, Usuario, Empleado, VistaEmpleado, VistaUsuario, EmpleadoEstacion, EmpleadoLinea
from .serializers import LoginSerializer, ListEmpleadoSerializer, DetailEmpleadoSerializer, UpdateEmpleadoSerializer, BajaEmpleadoSerializer
from usuarios.permissions import TienePermisoModulo
from .models import Rol, Turno
from .serializers import RolSerializer, TurnoSerializer

from django.db.models import Q
#################################
# MARLENE MARLENE MARLENE AHORA EN POSTMAN usa "Bearer tu_token", en la parte donde tienes que poner tu token
###########################


def debe_asignar_linea(rol_codigo):
    return rol_codigo != "ADMIN"


def debe_asignar_estacion(rol_codigo):
    return rol_codigo not in {"ADMIN", "SUPER"}

# Create your views here.
''' AQUI ESTAN LOS VIEWS DE:
│   - Empleado         
│   - Usuario           
│   - Rol           
│   - Turno        
│   - EmpleadoLinea  
│   - EmpleadoEstacion 
'''
# Create your models here.


#rol
class ListaRolesAPIView(APIView):
    permission_classes = [AllowAny]
    modulo = "usuarios"

    def get(self, request):
        roles = Rol.objects.all()
        serializer = RolSerializer(roles, many=True)
        return Response(serializer.data)

#turno
class ListaTurnosAPIView(APIView):
    permission_classes = [AllowAny]
    modulo = "usuarios"

    def get(self, request):
        turnos = Turno.objects.all()
        serializer = TurnoSerializer(turnos, many=True)
        return Response(serializer.data)


#----------------------------------------------------------------------------------------------
#           U S U A R I O S     V I E W S
#----------------------------------------------------------------------------------------------
#Login
class LoginAPIView(APIView):

    permission_classes = [AllowAny]
    def get(self, request):
        return Response(
            {
                "mensaje": "Utiliza el método POST para iniciar sesión."
            }
        )

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = serializer.validated_data['usuario']
        contrasena = serializer.validated_data['contrasena']


        # Buscar usuario
        try:

            usuario_db = Usuario.objects.get(
                usuario=usuario
            )
        except Usuario.DoesNotExist:
            return Response(
                {
                    "mensaje": "Usuario o contraseña incorrectos"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar estado del usuario
        if not usuario_db.estado:
            return Response(
                {
                    "mensaje": "El usuario se encuentra desactivado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Verificar contraseña
        if not check_password(
            contrasena,
            usuario_db.contrasena
        ):
            return Response(
                {
                    "mensaje": "Usuario o contraseña incorrectos"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ==================================================
        # VALIDAR EMPLEADO Y ROL
        # ==================================================
        try:
            empleado = usuario_db.empleado
        except Empleado.DoesNotExist:
            return Response(
                {
                    "mensaje": "El usuario no tiene un empleado asignado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if not empleado.rol:
            return Response(
                {
                    "mensaje": "El empleado no tiene un rol asignado"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener código del rol
        rol = empleado.rol.codigo

        # ROLES QUE PUEDEN USAR EL SISTEMA
        roles_permitidos = [
            "ADMIN",
            "SUPER",
            "OPCALI"
        ]
        if rol not in roles_permitidos:
            return Response(
                {
                    "mensaje": "Este rol no tiene acceso al sistema"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # GENERAR TOKEN
        token = token_hex(32)

        ahora = timezone.now()
        expiracion = ahora + timedelta(hours=10)

        # Limpiar sólo las sesiones ya vencidas: si se borraran todas, iniciar
        # sesión en la API tumbaría el token que el cliente ya tenía guardado
        # (y al revés), porque ambos usan este mismo endpoint.
        Sesion.objects.filter(
            usuario=usuario_db,
            fecha_expiracion__lt=ahora
        ).delete()

        # Crear nueva sesión
        Sesion.objects.create(
            usuario=usuario_db,
            token=token,
            fecha_inicio=ahora,
            fecha_expiracion=expiracion
        )

        # YA CUANDO INICIA SESION CHIDO
        return Response(
            {
                "mensaje": "Inicio de sesión exitoso",
                "usuario": usuario_db.usuario,
                "empleado": empleado.numero,
                "nombre": f"{empleado.nombrepila} {empleado.primerapell}",      
                "rol": rol,
                "token": token
            },
            status=status.HTTP_200_OK
        )

# . . . . . . . . REGISTRAR

class RegistroUsuarioAPIView(APIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]
    modulo = "usuarios"
     
    def post(self, request):

        serializer = serializers.CreateUsuarioSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        empleado = serializer.validated_data["empleado"]

        if Usuario.objects.filter(empleado=empleado).exists():
            return Response(
                {
                    "mensaje": "El empleado ya tiene un usuario asignado"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if Usuario.objects.filter(
            usuario=serializer.validated_data["usuario"]
        ).exists():
            return Response(
                {
                    "mensaje": "El nombre de usuario ya existe"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario = serializer.save()

        return Response(
            {
                "mensaje": "Usuario registrado correctamente",
                "usuario": {
                    "numero": usuario.numero,
                    "usuario": usuario.usuario
                }
            },
            status=status.HTTP_201_CREATED
        )
# . . . . . . . . LISTAR
class ListaUsuariosAPIView(APIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "usuarios"

    def get(self, request):

        usuarios = VistaUsuario.objects.all()

        serializer = serializers.ListUsuarioSerializer(
            usuarios,
            many=True
        )

        return Response(serializer.data)

#Detalle usuario
class DetailUsuarioAPIView(APIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "usuarios"

    def get(self, request, numero):

        try:
            usuario = VistaUsuario.objects.get(numero=numero)

        except VistaUsuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.DetailUsuarioSerializer(usuario)

        return Response(serializer.data)
    
# . . . . . .  . . . Actualizar
class UpdateUsuarioAPIView(APIView):

    permission_classes = [
        AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
    ]
    modulo = "usuarios" 

    def put(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializers.UpdateUsuarioSerializer(
            usuario,
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.data.get("contrasena"):
            admin_password = request.data.get("admin_password")

            if not admin_password:
                return Response(
                    {
                        "admin_password": [
                            "Se requiere la contraseña del administrador para cambiar la contraseña."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not request.user or not hasattr(request.user, "empleado") or request.user.empleado is None:
                return Response(
                    {
                        "mensaje": "No se pudo verificar el administrador."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            if request.user.empleado.rol_id != "ADMIN":
                return Response(
                    {
                        "mensaje": "Solo un administrador puede autorizar el cambio de contraseña."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            if not check_password(admin_password, request.user.contrasena):
                return Response(
                    {
                        "admin_password": [
                            "Contraseña de administrador incorrecta."
                        ]
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer.save()

        return Response(
            {
                "mensaje": "Usuario actualizado correctamente"
            }
        )
        


# . . . . . .  . . . BAJA LOGICA
class BajaUsuarioAPIView(APIView):

    permission_classes = [
        AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
    ]
    modulo = "usuarios" 

    def patch(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if not usuario.estado:
            return Response(
                {
                    "mensaje": "El usuario ya se encuentra desactivado"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.estado = False
        usuario.save()

        return Response(
            {
                "mensaje": "Usuario desactivado correctamente"
            }
        )
        
# . . . . . .  . . .  REACTIVAR USURAIO
class ReactivarUsuarioAPIView(APIView):

    permission_classes = [
        AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
    ]
    modulo = "usuarios" 

    def patch(self, request, numero):

        try:
            usuario = Usuario.objects.get(
                numero=numero
            )

        except Usuario.DoesNotExist:

            return Response(
                {
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if usuario.estado:
            return Response(
                {
                    "mensaje": "El usuario ya se encuentra activo"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usuario.estado = True
        usuario.save()

        return Response(
            {
                "mensaje": "Usuario reactivado correctamente"
            }
        )

#---------------------------------------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------        E M P L E A D O     V I E W S       -------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------


#. . . . . .  . REGISTRO

class RegistroEmpleadoAPIView(APIView):
    
    permission_classes = [
        AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
    ]
    modulo = "empleados" 

    @transaction.atomic
    def post(self, request):
        
        rol_id = request.data.get("rol")
        linea_id = request.data.get("linea")
        estacion_id = request.data.get("estacion")

        es_admin = rol_id == "ADMIN"
        debe_linea = debe_asignar_linea(rol_id)
        debe_estacion = debe_asignar_estacion(rol_id)

        if es_admin:
            linea = None
            estacion = None
        else:
            if not linea_id:
                return Response(
                    {
                        "mensaje": "Debe seleccionar una línea"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                linea = Linea.objects.get(pk=linea_id)
            except Linea.DoesNotExist:
                return Response(
                    {
                        "mensaje": "La línea seleccionada no existe"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if debe_estacion:
                if not estacion_id:
                    return Response(
                        {
                            "mensaje": "Debe seleccionar una estación"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    estacion = Estacion.objects.get(pk=estacion_id)
                except Estacion.DoesNotExist:
                    return Response(
                        {
                            "mensaje": "La estación seleccionada no existe"
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

                if estacion.linea_id != linea.codigo:
                    return Response(
                        {
                            "mensaje": "La estación no pertenece a la línea seleccionada"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                estacion = None

#registrar empleado

        empleado_serializer = serializers.CreateEmpleadoSerializer(
            data=request.data
        )


        if not empleado_serializer.is_valid():

            return Response(
                empleado_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        empleado = empleado_serializer.save()


        # Si es Admin, no se asigna línea ni estación: se guarda el empleado y se termina aquí.
        if es_admin:
            return Response(
                {
                    "mensaje": "Empleado registrado correctamente",
                    "empleado": empleado.numero,
                    "linea": None,
                    "estacion": None
                },
                status=status.HTTP_201_CREATED
            )


        if debe_linea:
            linea_data = {
                "empleado": empleado.numero,
                "linea": linea.codigo,
                "fecha_inicio": date.today()
            }

            try:
                EmpleadoLinea.objects.get(
                    empleado=empleado,
                    linea_id=linea.codigo,
                    fecha_inicio=date.today()
                )
            except EmpleadoLinea.DoesNotExist:
                linea_serializer = serializers.CreateEmpleadoLineaSerializer(
                    data=linea_data
                )

                if not linea_serializer.is_valid():
                    return Response(
                        linea_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    linea_serializer.save()
                except IntegrityError:
                    return Response(
                        {
                            "mensaje": "Ya existe una asignación de línea activa para este empleado con la misma fecha."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if debe_estacion and estacion is not None:
            estacion_data = {
                "empleado": empleado.numero,
                "estacion": estacion.codigo,
                "fecha_inicio": date.today()
            }

            try:
                EmpleadoEstacion.objects.get(
                    empleado=empleado,
                    estacion_id=estacion.codigo,
                    fecha_inicio=date.today()
                )
            except EmpleadoEstacion.DoesNotExist:
                estacion_serializer = serializers.CreateEmpleadoEstacionSerializer(
                    data=estacion_data
                )

                if not estacion_serializer.is_valid():
                    return Response(
                        estacion_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    estacion_serializer.save()
                except IntegrityError:
                    return Response(
                        {
                            "mensaje": "Ya existe una asignación de estación activa para este empleado con la misma fecha."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

        return Response(
            {
                "mensaje": "Empleado registrado correctamente",
                "empleado": empleado.numero,
                "linea": linea.nombre if linea else None,
                "estacion": estacion.nombre if estacion else None
            },
            status=status.HTTP_201_CREATED
        )
        

#. . . . . .  . LISTA
class ListaEmpleadosAPIView(APIView):
    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request):

        empleados = VistaEmpleado.objects.all()

        serializer = ListEmpleadoSerializer(
            empleados,
            many=True
        )

        return Response(serializer.data)
    
    
#. . . . . .  . DETAIL
class DetailEmpleadoAPIView(APIView):
    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request, numero):

        try:
            empleado = VistaEmpleado.objects.get(numero=numero)

        except VistaEmpleado.DoesNotExist:
            return Response(
                {"mensaje": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailEmpleadoSerializer(empleado)

        return Response(serializer.data)
    
#. . . . . .  . Update
class UpdateEmpleadoAPIView(APIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "empleados"
    
    def get(self, request, numero):
        try:
            empleado = Empleado.objects.get(numero=numero)
        except Empleado.DoesNotExist:
            return Response(
                {"mensaje": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "numero": empleado.numero,
            "nombrepila": empleado.nombrepila,
            "primerapell": empleado.primerapell,
            "segundoapell": empleado.segundoapell,
            "rol": empleado.rol_id,
            "turno": empleado.turno_id,
        })


    def put(self, request, numero):

        try:
            empleado = Empleado.objects.get(
                numero=numero
            )

        except Empleado.DoesNotExist:

            return Response(
                {
                    "mensaje": "Empleado no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )


        serializer = serializers.UpdateEmpleadoSerializer(
            empleado,
            data=request.data,
            partial=True
        )


        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


        # Guardar datos normales del empleado
        empleado = serializer.save()


        # Si el rol resultante es Administrador, no debe tener línea ni estación:
        # cerramos cualquier asignación activa y no procesamos cambios nuevos.
        if empleado.rol_id == "ADMIN":

            EmpleadoLinea.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).update(
                fecha_fin=timezone.now().date()
            )

            EmpleadoEstacion.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).update(
                fecha_fin=timezone.now().date()
            )

            return Response(
                {
                    "mensaje": "Empleado actualizado correctamente"
                },
                status=status.HTTP_200_OK
            )

        if empleado.rol_id == "SUPER":
            EmpleadoEstacion.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).update(
                fecha_fin=timezone.now().date()
            )

        # ===============================
        # CAMBIO DE LINEA
        # ===============================

        linea = request.data.get("linea")

        if linea and debe_asignar_linea(empleado.rol_id):
            asignacion_activa = EmpleadoLinea.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).first()

            if asignacion_activa is None or asignacion_activa.linea_id != linea:
                EmpleadoLinea.objects.filter(
                    empleado=empleado,
                    fecha_fin__isnull=True
                ).update(
                    fecha_fin=timezone.now().date()
                )

                EmpleadoLinea.objects.create(
                    empleado=empleado,
                    linea_id=linea,
                    fecha_inicio=timezone.now().date()
                )

        # ===============================
        # CAMBIO DE ESTACION
        # ===============================

        estacion = request.data.get("estacion")

        if estacion and debe_asignar_estacion(empleado.rol_id):
            asignacion_activa = EmpleadoEstacion.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).first()

            if asignacion_activa is None or asignacion_activa.estacion_id != estacion:
                EmpleadoEstacion.objects.filter(
                    empleado=empleado,
                    fecha_fin__isnull=True
                ).update(
                    fecha_fin=timezone.now().date()
                )

                EmpleadoEstacion.objects.create(
                    empleado=empleado,
                    estacion_id=estacion,
                    fecha_inicio=timezone.now().date()
                )


        return Response(
            {
                "mensaje": "Empleado actualizado correctamente"
            },
            status=status.HTTP_200_OK
        )
    
    
#. . . . . .  . DELETE 

# chavalines, no os preocupeis, es la desactivación de empleado, es decir, cambia el estado activo a False para conservar trazabilidad histórica
class BajaEmpleadoView(generics.UpdateAPIView):
    permission_classes = [
            AllowAny
            #IsAuthenticated,
            #TienePermisoModulo
        ]
    modulo = "empleados" 
    queryset = Empleado.objects.all()
    serializer_class = BajaEmpleadoSerializer
    lookup_field = "numero"
    
    
    

class ReactivarEmpleadoAPIView(APIView):

    def patch(self, request, numero):

        try:
            empleado = Empleado.objects.get(numero=numero)

            empleado.activo = True
            empleado.save()

            return Response({
                "mensaje": "Empleado reactivado correctamente"
            }, status=status.HTTP_200_OK)

        except Empleado.DoesNotExist:
            return Response({
                "mensaje": "Empleado no encontrado"
            }, status=status.HTTP_404_NOT_FOUND)



    

    
#Buscar empleados lineas
class BuscarEmpleadoLineaView(generics.ListAPIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "usuarios"

    serializer_class = serializers.ListEmpleadoLineaSerializer


    def get_queryset(self):

        queryset = EmpleadoLinea.objects.filter(
            fecha_fin__isnull=True
        )

        buscar = self.request.GET.get("buscar")


        if buscar:

            queryset = queryset.filter(

                Q(empleado__nombrepila__icontains=buscar) |
                Q(empleado__primerapell__icontains=buscar) |
                Q(linea__nombre__icontains=buscar)

            )
        


        return queryset
    
    
#buscar empleado estacion
class BuscarEmpleadoEstacionView(generics.ListAPIView):

    permission_classes = [
        AllowAny
        #IsAuthenticated,
        #TienePermisoModulo
    ]

    modulo = "usuarios"


    serializer_class = serializers.ListEmpleadoEstacionSerializer


    def get_queryset(self):

        queryset = EmpleadoEstacion.objects.filter(
            fecha_fin__isnull=True
        )


        buscar = self.request.GET.get("buscar")


        if buscar:

            queryset = queryset.filter(

                Q(empleado__nombrepila__icontains=buscar) |
                Q(empleado__primerapell__icontains=buscar) |
                Q(estacion__nombre__icontains=buscar)

            )


        return queryset
    


class EmpleadosCalidadPorLineaAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        TienePermisoModulo
    ]
    modulo = "empleados"

    def get(self, request, linea_id):
        asignaciones = EmpleadoLinea.objects.filter(
            linea_id=linea_id,
            fecha_fin__isnull=True,
            empleado__rol__codigo="OPCALI"
        ).select_related("empleado")

        data = [
            {
                "numero": a.empleado.numero,
                "nombre": f"{a.empleado.nombrepila} {a.empleado.primerapell}",
            }
            for a in asignaciones
        ]
        return Response(data)
    
    
    
# Buscar usuario
class BuscarUsuarioView(generics.ListAPIView):

    permission_classes = [
        AllowAny
        # IsAuthenticated,
        # TienePermisoModulo
    ]

    modulo = "usuarios"

    serializer_class = serializers.ListUsuarioSerializer

    def get_queryset(self):

        queryset = VistaUsuario.objects.all()

        buscar = self.request.GET.get("buscar")
        rol = self.request.GET.get("rol")
        estado = self.request.GET.get("estado")

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(usuario__icontains=buscar) |
                Q(empleado_nombre__icontains=buscar)
            )

        if rol:
            queryset = queryset.filter(
                rol_nombre__iexact=rol
            )

        if estado:
            queryset = queryset.filter(
                estado_usuario__iexact=estado
            )

        return queryset
    


# Buscar empleado
class BuscarEmpleadoView(generics.ListAPIView):

    permission_classes = [
        AllowAny
        # IsAuthenticated,
        # TienePermisoModulo
    ]

    modulo = "empleados"

    serializer_class = serializers.ListEmpleadoSerializer

    def get_queryset(self):

        queryset = VistaEmpleado.objects.all()

        buscar = self.request.GET.get("buscar")
        rol = self.request.GET.get("rol")
        estado = self.request.GET.get("estado")
        linea = self.request.GET.get("linea")  # NUEVO

        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(nombre_completo__icontains=buscar) |
                Q(rol_nombre__icontains=buscar) |
                Q(turno_nombre__icontains=buscar) |
                Q(linea_nombre__icontains=buscar)  # NUEVO
            )

        if rol:
            queryset = queryset.filter(
                rol_codigo=rol
            )

        if estado:
            queryset = queryset.filter(
                estado_empleado__iexact=estado
            )

        if linea:
            queryset = queryset.filter(
                linea_codigo=linea
            )

        return queryset