"""Panel del Administrador.

Esta carpeta es del equipo que trabaja el panel de administrador. Las pantallas
del admin (producción, calidad, componentes, líneas, personal) viven todavía en
las apps originales del proyecto, porque son las que ya estaban construidas
cuando el cliente era uno solo; se llegan desde el sidebar de este panel.

El acceso lo cuida `core.middleware.AccesoPorRolMiddleware`: sólo el rol ADMIN
entra a /panel/admin/ y a las apps que le pertenecen.

Dónde está cada vista
---------------------
Este archivo se quedó vacío a propósito. Las dos pantallas propias del panel
crecieron lo suficiente para merecer su propio módulo, y así se ve de un vistazo
cuál es cuál:

    views_dashboard.py     la portada, con las estadísticas de la planta
    views_trazabilidad.py  la consulta de trazabilidad por orden de producción

Las dos leen de /api/dashboard/ (la app `dashboard` de Servicios), que es de sólo
lectura y sólo para ADMIN.
"""
