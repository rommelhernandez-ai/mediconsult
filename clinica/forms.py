from django import forms
from django.utils import timezone

from .models import Cita, Horario, Medico, Paciente
from .servicios import obtener_festivos


class FormularioSimple(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            elif isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"


class PacienteForm(FormularioSimple):
    class Meta:
        model = Paciente
        fields = ["nombre", "apellidos", "fecha_nacimiento", "telefono", "correo"]
        widgets = {"fecha_nacimiento": forms.DateInput(attrs={"type": "date"})}


class MedicoForm(FormularioSimple):
    class Meta:
        model = Medico
        fields = ["nombre", "apellidos", "especialidad", "telefono", "activo"]


class HorarioForm(FormularioSimple):
    class Meta:
        model = Horario
        fields = ["medico", "dia_semana", "hora_inicio", "hora_fin"]
        widgets = {"hora_inicio": forms.TimeInput(attrs={"type": "time"}), "hora_fin": forms.TimeInput(attrs={"type": "time"})}


class CitaForm(FormularioSimple):
    class Meta:
        model = Cita
        fields = ["paciente", "medico", "fecha", "hora", "motivo"]
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"}), "hora": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medico"].queryset = Medico.objects.filter(activo=True).order_by("apellidos", "nombre")
        self.festivos_no_disponibles = False

    def clean(self):
        datos = super().clean()
        medico, fecha, hora = datos.get("medico"), datos.get("fecha"), datos.get("hora")
        if not (medico and fecha and hora):
            return datos

        ahora = timezone.localtime()
        if fecha < ahora.date() or (fecha == ahora.date() and hora <= ahora.time()):
            self.add_error("fecha", "No se pueden agendar citas en fechas u horas pasadas.")
            return datos

        festivos = obtener_festivos(fecha.year)
        self.festivos_no_disponibles = festivos is None
        if festivos and fecha in festivos:
            self.add_error("fecha", f"El {fecha:%d/%m/%Y} es día festivo ({festivos[fecha]}). No se agendan citas.")