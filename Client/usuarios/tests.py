from django.test import SimpleTestCase

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
