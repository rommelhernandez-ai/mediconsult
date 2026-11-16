from django.contrib import admin

from .models import Horario, Medico, Paciente

from .models import Cita, Horario, Medico, Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellidos", "telefono", "correo")
    search_fields = ("nombre", "apellidos")


class HorarioInline(admin.TabularInline):
    model = Horario
    extra = 1


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellidos", "especialidad", "activo")
    list_filter = ("especialidad", "activo")
    search_fields = ("nombre", "apellidos")
    inlines = [HorarioInline]



@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "paciente", "medico", "estado")
    list_filter = ("estado", "medico", "fecha")
    search_fields = ("paciente__nombre", "paciente__apellidos", "motivo")
    date_hierarchy = "fecha"