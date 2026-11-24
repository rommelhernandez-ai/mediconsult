from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clinica.models import Cita, Horario, Medico, Paciente

LUNES, MARTES, MIERCOLES, JUEVES, VIERNES = range(5)


def dia_cercano(dia_semana, semanas=0):
    """Fecha del próximo día de la semana indicado; con semanas negativas, en el pasado."""
    hoy = timezone.localdate()
    dias = (dia_semana - hoy.weekday()) % 7 or 7
    return hoy + timedelta(days=dias, weeks=semanas)


class Command(BaseCommand):
    help = "Borra los datos de la clínica y carga datos ficticios de demostración."

    @transaction.atomic
    def handle(self, *args, **options):
        Cita.objects.all().delete()
        Horario.objects.all().delete()
        Medico.objects.all().delete()
        Paciente.objects.all().delete()

        laura = Medico.objects.create(nombre="Laura", apellidos="Méndez Ortiz", especialidad="PEDIATRIA", telefono="6645552222")
        carlos = Medico.objects.create(nombre="Carlos", apellidos="Ramírez Soto", especialidad="GENERAL", telefono="6645551111")
        sofia = Medico.objects.create(nombre="Sofía", apellidos="Herrera Luna", especialidad="GINECOLOGIA", telefono="6645553333")
        Medico.objects.create(nombre="Jorge", apellidos="Castillo Ruiz", especialidad="DERMATOLOGIA", telefono="6645554444", activo=False)

        horarios = [
            (laura, LUNES, 9, 14),
            (laura, MIERCOLES, 15, 19),
            (carlos, LUNES, 8, 14),
            (carlos, MARTES, 8, 14),
            (carlos, MIERCOLES, 8, 14),
            (carlos, JUEVES, 8, 14),
            (carlos, VIERNES, 8, 14),
            (sofia, MARTES, 10, 16),
            (sofia, JUEVES, 10, 16),
        ]
        for medico, dia, inicio, fin in horarios:
            Horario.objects.create(medico=medico, dia_semana=dia, hora_inicio=time(inicio), hora_fin=time(fin))

        juan = Paciente.objects.create(nombre="Juan", apellidos="Pérez López", fecha_nacimiento="1990-03-15", telefono="6641234567")
        maria = Paciente.objects.create(nombre="María", apellidos="García Ruiz", fecha_nacimiento="1985-08-22", telefono="6649876543", correo="maria@ejemplo.com")
        luis = Paciente.objects.create(nombre="Luis", apellidos="Hernández Mora", fecha_nacimiento="1978-01-03", telefono="6642221100")
        ana = Paciente.objects.create(nombre="Ana", apellidos="Torres Vega", fecha_nacimiento="2001-11-10", telefono="6645557788", correo="ana@ejemplo.com")
        diego = Paciente.objects.create(nombre="Diego", apellidos="Ramos Cruz", fecha_nacimiento="2015-06-30", telefono="6643339900")
        Paciente.objects.create(nombre="Valeria", apellidos="Soto Núñez", fecha_nacimiento="1995-04-18", telefono="6648884455", correo="valeria@ejemplo.com")

        citas = [
            (juan, laura, dia_cercano(MIERCOLES, -2), time(16), "Revisión general", "ATENDIDA"),
            (maria, carlos, dia_cercano(MARTES, -2), time(9), "Dolor de cabeza", "ATENDIDA"),
            (luis, carlos, dia_cercano(JUEVES, -2), time(11), "Chequeo de presión", "CANCELADA"),
            (ana, sofia, dia_cercano(MARTES), time(10, 30), "Consulta de control", "PROGRAMADA"),
            (diego, laura, dia_cercano(MIERCOLES), time(16), "Vacunación", "PROGRAMADA"),
            (juan, carlos, dia_cercano(VIERNES), time(9), "Seguimiento", "PROGRAMADA"),
        ]
        for paciente, medico, fecha, hora, motivo, estado in citas:
            Cita.objects.create(paciente=paciente, medico=medico, fecha=fecha, hora=hora, motivo=motivo, estado=estado)

        self.stdout.write(self.style.SUCCESS(
            f"Datos de demostración cargados: {Medico.objects.count()} médicos, "
            f"{Horario.objects.count()} horarios, {Paciente.objects.count()} pacientes "
            f"y {Cita.objects.count()} citas."
        ))