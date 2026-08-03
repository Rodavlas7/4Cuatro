# middleware.py
from django.shortcuts import render
from django.conf import settings

class MantenimientoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtenemos la lista de rutas en mantenimiento (si no existe, usamos una lista vacía)
        maintenance_paths = getattr(settings, 'MAINTENANCE_PATHS', [])
        
        # Comprobamos si la URL actual que pide el usuario empieza con alguna ruta de nuestra lista
        is_under_maintenance = any(request.path.startswith(path) for path in maintenance_paths)

        if is_under_maintenance:
            # PRO-TIP: Excluimos el /admin/ por seguridad, aunque coincida por error
            if not request.path.startswith('/admin/'):
                # Retornamos la pantalla de mantenimiento con código 503 (Servicio no disponible)
                return render(request, 'especiales/mantenimiento.html', status=503)

        # Si el módulo no está en la lista, la petición sigue su curso normal
        response = self.get_response(request)
        return response