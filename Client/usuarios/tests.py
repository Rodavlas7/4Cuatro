from django.http import HttpRequest
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from usuarios.forms import filtrar_lineas_por_rol
from usuarios.views import debe_asignar_estacion, debe_asignar_linea


class AsignacionesPorRolTests(SimpleTestCase):
    def test_supervisor_asigna_linea_y_no_estacion(self):
        self.assertTrue(debe_asignar_linea("SUPER"))
        self.assertFalse(debe_asignar_estacion("SUPER"))

    def test_operario_asigna_linea_y_estacion(self):
        self.assertTrue(debe_asignar_linea("OPENSA"))
        self.assertTrue(debe_asignar_estacion("OPENSA"))

    def test_admin_no_asigna_nada(self):
        self.assertFalse(debe_asignar_linea("ADMIN"))
        self.assertFalse(debe_asignar_estacion("ADMIN"))


class FiltroLineasPorRolTests(SimpleTestCase):
    def test_opcali_muestra_cualquier_linea(self):
        lineas = [
            {"codigo": "L1", "nombre": "Línea 1", "tipo_codigo": "ENSA"},
            {"codigo": "L2", "nombre": "Línea 2", "tipo_codigo": "EMBA"},
        ]

        self.assertEqual(filtrar_lineas_por_rol(lineas, "OPCALI"), lineas)

    def test_opemba_solo_lineas_de_embalaje(self):
        lineas = [
            {"codigo": "L1", "nombre": "Línea 1", "tipo_codigo": "ENSA"},
            {"codigo": "L2", "nombre": "Línea 2", "tipo_codigo": "EMBA"},
        ]

        filtradas = filtrar_lineas_por_rol(lineas, "OPEMBA")

        self.assertEqual(filtradas, [{"codigo": "L2", "nombre": "Línea 2", "tipo_codigo": "EMBA"}])

    def test_opensa_solo_lineas_de_ensamblaje(self):
        lineas = [
            {"codigo": "L1", "nombre": "Línea 1", "tipo_codigo": "ENSA"},
            {"codigo": "L2", "nombre": "Línea 2", "tipo_codigo": "EMBA"},
        ]

        filtradas = filtrar_lineas_por_rol(lineas, "OPENSA")

        self.assertEqual(filtradas, [{"codigo": "L1", "nombre": "Línea 1", "tipo_codigo": "ENSA"}])


class ConfirmacionEnVistasTests(SimpleTestCase):
    def test_formulario_editar_usuario_pide_confirmacion(self):
        request = HttpRequest()
        html = render_to_string(
            "usuarios/usuarios.html",
            {
                "usuarios": [],
                "empleados": [],
                "roles": [],
                "buscar": "",
                "rol": "",
                "estado": "",
            },
            request=request,
        )

        self.assertIn('data-confirm="¿Deseas guardar los cambios de este usuario?"', html)

    def test_formulario_editar_empleado_pide_confirmacion(self):
        request = HttpRequest()
        html = render_to_string(
            "usuarios/empleados.html",
            {
                "empleados": [],
                "lineas": [],
                "estaciones": [],
                "roles": [],
                "turnos": [],
                "buscar": "",
                "rol": "",
                "estado": "",
                "linea": "",
            },
            request=request,
        )

        self.assertIn('data-confirm="¿Deseas guardar los cambios de este empleado?"', html)
