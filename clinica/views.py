import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CitaForm, HorarioForm, MedicoForm, PacienteForm
from .models import Cita, Horario, Medico, Paciente
from .permissions import administrador_requerido


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


@login_required
def inicio(request):
    citas = Cita.objects.select_related("paciente", "medico").filter(
        fecha__gte=timezone.localdate(), estado="PROGRAMADA"
    )
    return render(request, "clinica/inicio.html", {
        "citas": citas[:10],
        "pacientes_total": Paciente.objects.count(),
        "medicos_total": Medico.objects.filter(activo=True).count(),
    })


@login_required
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
@administrador_requerido
def medicos(request):
    formulario = MedicoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Médico registrado.")
        return redirect("medicos")
    termino = request.GET.get("q", "").strip()
    return render(request, "clinica/medicos.html", {
        "formulario": formulario,
        "medicos": buscar_medicos(termino),
        "horario_form": HorarioForm(),
        "termino": termino,
    })


@login_required
@administrador_requerido
def editar_medico(request, medico_id):
    medico = get_object_or_404(Medico, pk=medico_id)
    formulario = MedicoForm(request.POST or None, instance=medico)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Médico actualizado.")
        return redirect("medicos")
    termino = request.GET.get("q", "").strip()
    return render(request, "clinica/medicos.html", {
        "formulario": formulario,
        "medicos": buscar_medicos(termino),
        "horario_form": HorarioForm(),
        "termino": termino,
        "medico_edicion": medico,
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
def agenda(request):
    formulario = CitaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Cita agendada.")
        if formulario.festivos_no_disponibles:
            messages.warning(request, "No se pudo consultar el calendario de días festivos. Verifica la fecha manualmente.")
        return redirect("agenda")
    citas = Cita.objects.select_related("paciente", "medico").order_by("fecha", "hora")
    filtro_fecha = request.GET.get("fecha")
    if filtro_fecha:
        citas = citas.filter(fecha=filtro_fecha)
    return render(request, "clinica/agenda.html", {"formulario": formulario, "citas": citas, "filtro_fecha": filtro_fecha})


@login_required
def cambiar_estado(request, cita_id, estado):
    if request.method == "POST" and estado in ("ATENDIDA", "CANCELADA"):
        cita = get_object_or_404(Cita, pk=cita_id)
        cita.estado = estado
        cita.save(update_fields=["estado"])
        messages.success(request, "Estado de la cita actualizado.")
    return redirect("agenda")
