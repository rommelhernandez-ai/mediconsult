from django import forms

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

    def clean(self):
        datos = super().clean()
        medico, fecha, hora = datos.get("medico"), datos.get("fecha"), datos.get("hora")
        if not (medico and fecha and hora):
            return datos

        horario = Horario.objects.filter(medico=medico, dia_semana=fecha.weekday()).first()
        if not horario or not (horario.hora_inicio <= hora < horario.hora_fin):
            self.add_error("hora", "El médico no tiene horario disponible a esa hora.")
        if Cita.objects.filter(medico=medico, fecha=fecha, hora=hora, estado="PROGRAMADA").exists():
            self.add_error("hora", "Ese horario ya está ocupado.")
        return datos
