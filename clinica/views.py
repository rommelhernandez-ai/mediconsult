import unicodedata

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CitaForm,
    HorarioForm,
    InicioSesionForm,
    MedicoForm,
    PacienteForm,
    RegistroPacienteForm,
)
from .models import Cita, Horario, Medico, Paciente
from .permissions import administrador_requerido, rol_actual, roles_requeridos


class InicioSesionView(LoginView):
    template_name = "clinica/login.html"
    authentication_form = InicioSesionForm

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        self.request.session["rol_activo"] = form.cleaned_data["rol"]
        return respuesta


def texto_normalizado(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(caracter)
    )


def buscar_pacientes(termino):
    pacientes = Paciente.objects.order_by("apellidos", "nombre")
    if termino:
        pacientes = pacientes.filter(
            Q(nombre__icontains=termino)
            | Q(apellidos__icontains=termino)
            | Q(telefono__icontains=termino)
            | Q(correo__icontains=termino)
        )
    return pacientes


def buscar_medicos(termino):
    medicos = Medico.objects.prefetch_related("horarios").order_by("apellidos", "nombre")
    if termino:
        termino_normalizado = texto_normalizado(termino)
        especialidades = [
            codigo
            for codigo, etiqueta in Medico.ESPECIALIDADES
            if termino_normalizado in texto_normalizado(etiqueta)
        ]
        medicos = medicos.filter(
            Q(nombre__icontains=termino)
            | Q(apellidos__icontains=termino)
            | Q(especialidad__icontains=termino)
            | Q(especialidad__in=especialidades)
            | Q(telefono__icontains=termino)
        )
    return medicos


def guardar_medico_y_cuenta(formulario):
    with transaction.atomic():
        medico = formulario.save(commit=False)
        usuario_login = formulario.cleaned_data.get("usuario_login", "")
        if usuario_login:
            usuario = medico.usuario
            if usuario is None:
                usuario = User.objects.create_user(
                    username=usuario_login,
                    password=formulario.cleaned_data["contrasena"],
                    first_name=medico.nombre,
                    last_name=medico.apellidos,
                )
            else:
                usuario.username = usuario_login
                usuario.first_name = medico.nombre
                usuario.last_name = medico.apellidos
                contrasena = formulario.cleaned_data.get("contrasena")
                if contrasena:
                    usuario.set_password(contrasena)
                usuario.save()
            usuario.groups.add(Group.objects.get(name="Médico"))
            medico.usuario = usuario
        medico.save()
        formulario.save_m2m()
    return medico


@login_required
@roles_requeridos("administrador", "recepcionista", "paciente", "medico")
def inicio(request):
    citas = Cita.objects.select_related("paciente", "medico").filter(
        fecha__gte=timezone.localdate(), estado="PROGRAMADA"
    )
    rol = rol_actual(request)
    if rol == "paciente":
        citas = citas.filter(paciente__usuario=request.user)
    elif rol == "medico":
        citas = citas.filter(medico__usuario=request.user)
    return render(request, "clinica/inicio.html", {
        "citas": citas[:10],
        "pacientes_total": Paciente.objects.count(),
        "medicos_total": Medico.objects.filter(activo=True).count(),
        "mostrar_resumen": rol in ("administrador", "recepcionista"),
    })


@login_required
@roles_requeridos("administrador", "recepcionista")
def pacientes(request):
    formulario = PacienteForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Paciente registrado.")
        return redirect("pacientes")
    termino = request.GET.get("q", "").strip()
    return render(request, "clinica/pacientes.html", {
        "formulario": formulario,
        "pacientes": buscar_pacientes(termino),
        "termino": termino,
    })


@login_required
@roles_requeridos("administrador", "recepcionista")
def editar_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    formulario = PacienteForm(request.POST or None, instance=paciente)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Paciente actualizado.")
        return redirect("pacientes")
    termino = request.GET.get("q", "").strip()
    return render(request, "clinica/pacientes.html", {
        "formulario": formulario,
        "pacientes": buscar_pacientes(termino),
        "termino": termino,
        "paciente_edicion": paciente,
    })


@login_required
@roles_requeridos("administrador", "recepcionista", "paciente")
def medicos(request):
    rol = rol_actual(request)
    if request.method == "POST" and rol != "administrador":
        raise PermissionDenied
    formulario = MedicoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        guardar_medico_y_cuenta(formulario)
        messages.success(request, "Médico registrado.")
        return redirect("medicos")
    termino = request.GET.get("q", "").strip()
    listado_medicos = buscar_medicos(termino)
    if rol == "paciente":
        listado_medicos = listado_medicos.filter(activo=True)
    return render(request, "clinica/medicos.html", {
        "formulario": formulario,
        "medicos": listado_medicos,
        "horario_form": HorarioForm(),
        "termino": termino,
        "puede_editar_medicos": rol == "administrador",
        "titulo_medicos": "Médicos disponibles" if rol == "paciente" else "Médicos y horarios",
    })


@login_required
@administrador_requerido
def editar_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id)
    formulario = MedicoForm(request.POST or None, instance=medico)
    if request.method == "POST" and formulario.is_valid():
        guardar_medico_y_cuenta(formulario)
        messages.success(request, "Médico actualizado.")
        return redirect("medicos")
    termino = request.GET.get("q", "").strip()
    return render(request, "clinica/medicos.html", {
        "formulario": formulario,
        "medicos": buscar_medicos(termino),
        "horario_form": HorarioForm(),
        "termino": termino,
        "medico_edicion": medico,
        "puede_editar_medicos": True,
        "titulo_medicos": "Médicos y horarios",
    })


@login_required
@administrador_requerido
def agregar_horario(request):
    formulario = HorarioForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Horario guardado.")
    else:
        messages.error(request, "Revisa los datos del horario.")
    return redirect("medicos")


@login_required
@roles_requeridos("administrador", "recepcionista", "paciente", "medico")
def agenda(request):
    rol = rol_actual(request)
    if rol == "medico" and request.method == "POST":
        raise PermissionDenied
    formulario = CitaForm(
        request.POST or None,
        paciente_usuario=request.user if rol == "paciente" else None,
    )
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Cita agendada.")
        if formulario.festivos_no_disponibles:
            messages.warning(request, "No se pudo consultar el calendario de días festivos. Verifica la fecha manualmente.")
        return redirect("agenda")
    citas = Cita.objects.select_related("paciente", "medico").order_by("fecha", "hora")
    if rol == "paciente":
        citas = citas.filter(paciente__usuario=request.user)
    elif rol == "medico":
        citas = citas.filter(medico__usuario=request.user)
    filtro_fecha = request.GET.get("fecha")
    if filtro_fecha:
        citas = citas.filter(fecha=filtro_fecha)
    return render(request, "clinica/agenda.html", {
        "formulario": formulario,
        "citas": citas,
        "filtro_fecha": filtro_fecha,
        "puede_agendar": rol in ("administrador", "recepcionista", "paciente"),
        "puede_cambiar_estado": rol in ("administrador", "recepcionista", "medico"),
    })


@login_required
def cambiar_estado(request, cita_id, estado):
    if request.method == "POST" and estado in ("ATENDIDA", "CANCELADA"):
        rol = rol_actual(request)
        if rol not in ("administrador", "recepcionista", "medico"):
            raise PermissionDenied
        citas = Cita.objects.all()
        if rol == "medico":
            citas = citas.filter(medico__usuario=request.user)
        cita = get_object_or_404(citas, pk=cita_id)
        cita.estado = estado
        cita.save(update_fields=["estado"])
        messages.success(request, "Estado de la cita actualizado.")
    return redirect("agenda")


def registro_paciente(request):
    if request.user.is_authenticated:
        return redirect("inicio")
    formulario = RegistroPacienteForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        with transaction.atomic():
            usuario = formulario.save()
            usuario.groups.add(Group.objects.get(name="Paciente"))
            Paciente.objects.create(
                usuario=usuario,
                nombre=usuario.first_name,
                apellidos=usuario.last_name,
                fecha_nacimiento=formulario.cleaned_data["fecha_nacimiento"],
                telefono=formulario.cleaned_data["telefono"],
                correo=usuario.email,
            )
        login(request, usuario)
        request.session["rol_activo"] = "paciente"
        messages.success(request, "Tu cuenta de paciente está lista.")
        return redirect("inicio")
    return render(request, "clinica/registro.html", {"formulario": formulario})
