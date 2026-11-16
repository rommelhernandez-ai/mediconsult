from django.contrib import admin

from .models import Medico, Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellidos", "telefono", "correo")
    search_fields = ("nombre", "apellidos")


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellidos", "especialidad", "activo")
    list_filter = ("especialidad", "activo")
    search_fields = ("nombre", "apellidos")