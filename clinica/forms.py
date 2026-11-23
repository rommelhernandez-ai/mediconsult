from django import forms
from django.utils import timezone

from .models import Cita, Horario, Medico, Paciente


class FormularioSimple(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
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

    def clean(self):
        datos = super().clean()
        medico, fecha, hora = datos.get("medico"), datos.get("fecha"), datos.get("hora")
        if not (medico and fecha and hora):
            return datos

        ahora = timezone.localtime()
        if fecha < ahora.date() or (fecha == ahora.date() and hora <= ahora.time()):
            self.add_error("fecha", "No se pueden agendar citas en fechas u horas pasadas.")
            return datos

        atiende = Horario.objects.filter(
            medico=medico,
            dia_semana=fecha.weekday(),
            hora_inicio__lte=hora,
            hora_fin__gt=hora,
        ).exists()
        if not atiende:
            self.add_error("hora", "El médico no atiende ese día a esa hora.")

        ocupada = Cita.objects.filter(medico=medico, fecha=fecha, hora=hora, estado="PROGRAMADA")
        if self.instance.pk:
            ocupada = ocupada.exclude(pk=self.instance.pk)
        if ocupada.exists():
            self.add_error("hora", "Ese horario ya está ocupado.")
        return datos