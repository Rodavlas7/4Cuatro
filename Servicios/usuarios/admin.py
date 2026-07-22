from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import (
    Empleado,
    Linea,
    Estacion,
    EmpleadoLinea,
    EmpleadoEstacion
)


class EmpleadoEstacionForm(forms.ModelForm):

    class Meta:
        model = EmpleadoEstacion
        fields = "__all__"


    def clean(self):
        cleaned_data = super().clean()

        empleado = cleaned_data.get("empleado")
        estacion = cleaned_data.get("estacion")

        if empleado and estacion:

            linea_actual = EmpleadoLinea.objects.filter(
                empleado=empleado,
                fecha_fin__isnull=True
            ).first()

            if linea_actual:

                if estacion.linea_id != linea_actual.linea_id:
                    raise ValidationError(
                        "La estación seleccionada no pertenece a la línea actual del empleado."
                    )

        return cleaned_data
    
    
class EmpleadoLineaInline(admin.TabularInline):
    model = EmpleadoLinea
    extra = 1


class EmpleadoEstacionInline(admin.TabularInline):
    model = EmpleadoEstacion
    form = EmpleadoEstacionForm
    extra = 1
    
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):

    list_display = [
        "numero",
        "nombrepila",
        "primerapell",
        "segundoapell",
        "turno",
        "rol"
    ]

    inlines = [
        EmpleadoLineaInline,
        EmpleadoEstacionInline
    ]