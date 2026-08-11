from django.urls import path

from . import views

app_name = 'trazabilidad'

urlpatterns = [
    path('', views.trazabilidadView, name='trazabilidad'),
    # Trazabilidad consolidada por Orden de Producción
    path('orden/<int:folio>/', views.TrazabilidadOrden.as_view(), name='trazabilidad_x_orden'),
    
    #Trazabilidad específica por Laptop
    path('laptop/<str:num_serie>/', views.trazabilidadLaptopView, name='trazabilidad_x_laptop'), 
    
    path('laptop/<str:num_serie>/pdf/', views.exportarLaptopPDFView, name='por_laptop_pdf'),
    
    
    path('reportes/', views.centroReportesView, name='centro_reportes'),
    path('reportes/calidad/excel/', views.exportarCalidadExcelView, name='reporte_calidad_excel'),
    path('reportes/embalaje/excel/', views.exportarEmbalajeExcelView, name='reporte_embalaje_excel'),
]

