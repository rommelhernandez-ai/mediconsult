from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Cita, Horario, Medico, Paciente
from .servicios import obtener_festivos


class InicioSesionForm(AuthenticationForm):
    def clean(self):
        datos = super().clean()
        usuario = self.get_user()
        if usuario and len(roles_disponibles(usuario)) != 1:
            raise ValidationError(
                "No se pudo determinar el rol de esta cuenta. Contacta al administrador."
            )
        return datos


def roles_disponibles(usuario):
    if usuario.is_superuser or usuario.groups.filter(name="Administrador").exists():
        return ("administrador",)

    roles = []
    if (
        usuario.groups.filter(name="Paciente").exists()
        and Paciente.objects.filter(usuario=usuario).exists()
    ):
        roles.append("paciente")
    if (
        usuario.groups.filter(name="Médico").exists()
        and Medico.objects.filter(usuario=usuario, activo=True).exists()
    ):
        roles.append("medico")
    if usuario.groups.filter(name="Recepcionista").exists():
        roles.append("recepcionista")

    return tuple(roles)


class RegistroPacienteForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico")
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    telefono = forms.CharField(label="Teléfono", max_length=15)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellidos",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"


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


class CrearCuentaForm(forms.Form):
    ROLES = (
        ("paciente", "Paciente"),
        ("medico", "Médico"),
        ("recepcionista", "Recepcionista"),
    )

    rol = forms.ChoiceField(label="Tipo de cuenta", choices=ROLES)
    nombre = forms.CharField(label="Nombre", max_length=100)
    apellidos = forms.CharField(label="Apellidos", max_length=100)
    usuario_login = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    correo = forms.EmailField(label="Correo electrónico", required=False)
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False)
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    especialidad = forms.ChoiceField(
        label="Especialidad",
        required=False,
        choices=[("", "Selecciona una especialidad"), *Medico.ESPECIALIDADES],
    )
    contrasena = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirmar_contrasena = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

        rol = self.data.get("rol") or self.initial.get("rol", "recepcionista")
        if rol == "paciente":
            self.fields["fecha_nacimiento"].required = True
            self.fields["telefono"].required = True
        elif rol == "medico":
            self.fields["especialidad"].required = True
            self.fields["telefono"].required = True

    def clean_usuario_login(self):
        usuario_login = self.cleaned_data["usuario_login"]
        if User.objects.filter(username__iexact=usuario_login).exists():
            raise ValidationError("Ese nombre de usuario ya está en uso.")
        return usuario_login

    def clean(self):
        datos = super().clean()
        contrasena = datos.get("contrasena")
        confirmar_contrasena = datos.get("confirmar_contrasena")
        if contrasena and confirmar_contrasena and contrasena != confirmar_contrasena:
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        if contrasena:
            usuario = User(
                username=datos.get("usuario_login", ""),
                first_name=datos.get("nombre", ""),
                last_name=datos.get("apellidos", ""),
            )
            try:
                validate_password(contrasena, user=usuario)
            except ValidationError as error:
                self.add_error("contrasena", error)
        return datos


class MedicoForm(FormularioSimple):
    usuario_login = forms.CharField(
        label="Usuario para iniciar sesión",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    contrasena = forms.CharField(
        label="Contraseña inicial",
        widget=forms.PasswordInput,
        help_text="En edición, déjala vacía para conservar la contraseña actual.",
    )
    confirmar_contrasena = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Medico
        fields = [
            "nombre",
            "apellidos",
            "especialidad",
            "telefono",
            "activo",
            "usuario_login",
            "contrasena",
            "confirmar_contrasena",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.usuario_id:
            self.fields["usuario_login"].initial = self.instance.usuario.username
            self.fields["contrasena"].required = False
            self.fields["confirmar_contrasena"].required = False
        elif self.instance.pk:
            self.fields["usuario_login"].required = False
            self.fields["contrasena"].required = False
            self.fields["confirmar_contrasena"].required = False

    def clean_usuario_login(self):
        usuario_login = self.cleaned_data.get("usuario_login", "")
        usuarios = User.objects.filter(username__iexact=usuario_login)
        if self.instance.usuario_id:
            usuarios = usuarios.exclude(pk=self.instance.usuario_id)
        if usuario_login and usuarios.exists():
            raise ValidationError("Ese nombre de usuario ya está en uso.")
        return usuario_login

    def clean(self):
        datos = super().clean()
        usuario_login = datos.get("usuario_login", "")
        contrasena = datos.get("contrasena")
        confirmar_contrasena = datos.get("confirmar_contrasena")
        tiene_cuenta = bool(self.instance.pk and self.instance.usuario_id)

        if usuario_login and not tiene_cuenta and not contrasena:
            self.add_error("contrasena", "Escribe una contraseña para crear el acceso.")
        if contrasena and not confirmar_contrasena:
            self.add_error("confirmar_contrasena", "Confirma la contraseña.")
        if confirmar_contrasena and not contrasena:
            self.add_error("contrasena", "Escribe la contraseña nueva.")
        if contrasena and confirmar_contrasena and contrasena != confirmar_contrasena:
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        if contrasena:
            usuario = User(
                username=usuario_login,
                first_name=datos.get("nombre", ""),
                last_name=datos.get("apellidos", ""),
            )
            try:
                validate_password(contrasena, user=usuario)
            except ValidationError as error:
                self.add_error("contrasena", error)
        return datos


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

    def __init__(self, *args, paciente_usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medico"].queryset = Medico.objects.filter(activo=True).order_by("apellidos", "nombre")
        if paciente_usuario is not None:
            self.fields["paciente"].queryset = Paciente.objects.filter(usuario=paciente_usuario)
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