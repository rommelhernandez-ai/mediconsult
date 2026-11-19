from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse

from .models import Medico, Paciente


class PacientesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="recepcion", password="clave-segura")
        self.client.force_login(self.usuario)
        self.paciente = Paciente.objects.create(
            nombre="Ana",
            apellidos="López",
            fecha_nacimiento="1990-05-10",
            telefono="5551234567",
            correo="ana@example.com",
        )
        Paciente.objects.create(
            nombre="Luis",
            apellidos="Pérez",
            fecha_nacimiento="1985-03-20",
            telefono="5559876543",
        )

    def test_busca_pacientes_por_nombre(self):
        respuesta = self.client.get(reverse("pacientes"), {"q": "Ana"})

        self.assertContains(respuesta, "Ana López")
        self.assertNotContains(respuesta, "Luis Pérez")

    def test_edita_paciente(self):
        respuesta = self.client.post(
            reverse("editar_paciente", args=[self.paciente.pk]),
            {
                "nombre": "Ana María",
                "apellidos": "López",
                "fecha_nacimiento": "1990-05-10",
                "telefono": "5550000000",
                "correo": "ana@example.com",
            },
        )

        self.assertRedirects(respuesta, reverse("pacientes"))
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, "Ana María")
        self.assertEqual(self.paciente.telefono, "5550000000")


class MedicosTests(TestCase):
    def setUp(self):
        self.grupo_administrador = Group.objects.get(name="Administrador")
        self.administrador = User.objects.create_user(username="admin_medicos", password="clave-segura")
        self.administrador.groups.add(self.grupo_administrador)
        self.medico = Medico.objects.create(
            nombre="Elena",
            apellidos="García",
            especialidad="PEDIATRIA",
            telefono="5551234567",
        )

    def test_administrador_busca_y_edita_medico(self):
        self.client.force_login(self.administrador)
        respuesta = self.client.get(reverse("medicos"), {"q": "Elena"})
        self.assertContains(respuesta, "Elena García")
        respuesta = self.client.get(reverse("medicos"), {"q": "Pediatría"})
        self.assertContains(respuesta, "Elena García")

        respuesta = self.client.post(
            reverse("editar_medico", args=[self.medico.pk]),
            {
                "nombre": "Elena",
                "apellidos": "García Ruiz",
                "especialidad": "PEDIATRIA",
                "telefono": "5550000000",
                "activo": "on",
            },
        )

        self.assertRedirects(respuesta, reverse("medicos"))
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.apellidos, "García Ruiz")
        self.assertEqual(self.medico.telefono, "5550000000")

    def test_recepcionista_no_puede_entrar_a_medicos_ni_editar(self):
        recepcionista = User.objects.create_user(username="recepcion", password="clave-segura")
        recepcionista.groups.add(Group.objects.get(name="Recepcionista"))
        self.client.force_login(recepcionista)

        respuesta = self.client.get(reverse("medicos"))
        self.assertEqual(respuesta.status_code, 403)

        respuesta = self.client.post(
            reverse("editar_medico", args=[self.medico.pk]),
            {"nombre": "No autorizado"},
        )
        self.assertEqual(respuesta.status_code, 403)
