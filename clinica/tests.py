from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CitaForm
from .models import Cita, Horario, Medico, Paciente


class CuentasTests(TestCase):
    def test_paciente_puede_registrarse_y_se_inicia_sesion(self):
        respuesta = self.client.post(
            reverse("registro_paciente"),
            {
                "username": "ana_paciente",
                "first_name": "Ana",
                "last_name": "López",
                "email": "ana@example.com",
                "fecha_nacimiento": "1990-05-10",
                "telefono": "5551234567",
                "password1": "UnaClaveSegura2026!",
                "password2": "UnaClaveSegura2026!",
            },
        )

        self.assertRedirects(respuesta, reverse("inicio"))
        usuario = User.objects.get(username="ana_paciente")
        self.assertTrue(usuario.groups.filter(name="Paciente").exists())
        self.assertEqual(usuario.perfil_paciente.nombre, "Ana")
        self.assertEqual(respuesta.wsgi_request.user, usuario)
        self.assertContains(self.client.get(reverse("inicio")), "Paciente")

    def test_login_rechaza_un_rol_que_no_pertenece_a_la_cuenta(self):
        usuario = User.objects.create_user(username="recepcion", password="clave-segura")
        usuario.groups.add(Group.objects.get(name="Recepcionista"))

        respuesta = self.client.post(
            reverse("login"),
            {"username": "recepcion", "password": "clave-segura", "rol": "paciente"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.wsgi_request.user.is_authenticated)
        self.assertContains(respuesta, "Tu cuenta no tiene acceso con el rol seleccionado.")

    def test_paciente_solo_ve_sus_citas_y_no_puede_abrir_pacientes(self):
        usuario = User.objects.create_user(username="ana", password="clave-segura")
        usuario.groups.add(Group.objects.get(name="Paciente"))
        paciente = Paciente.objects.create(
            usuario=usuario,
            nombre="Ana",
            apellidos="López",
            fecha_nacimiento="1990-05-10",
            telefono="5551234567",
        )
        otro_paciente = Paciente.objects.create(
            nombre="Luis",
            apellidos="Pérez",
            fecha_nacimiento="1985-03-20",
            telefono="5559876543",
        )
        medico = Medico.objects.create(
            nombre="Elena",
            apellidos="García",
            especialidad="GENERAL",
            telefono="5550000000",
        )
        fecha = timezone.localdate() + timedelta(days=1)
        Cita.objects.create(
            paciente=paciente,
            medico=medico,
            fecha=fecha,
            hora="10:00",
            motivo="Consulta privada",
        )
        Cita.objects.create(
            paciente=otro_paciente,
            medico=medico,
            fecha=fecha,
            hora="11:00",
            motivo="Otra consulta",
        )
        self.client.force_login(usuario)

        respuesta = self.client.get(reverse("agenda"))

        self.assertContains(respuesta, "Ana López")
        self.assertNotContains(respuesta, "Luis Pérez")
        self.assertEqual(self.client.get(reverse("pacientes")).status_code, 403)
        Medico.objects.create(
            nombre="Luis",
            apellidos="Pérez",
            especialidad="PEDIATRIA",
            telefono="5551111111",
            activo=False,
        )
        medicos = self.client.get(reverse("medicos"))
        self.assertContains(medicos, "Elena García")
        self.assertNotContains(medicos, "Luis Pérez")

    def test_medico_solo_ve_su_agenda(self):
        usuario = User.objects.create_user(username="elena", password="clave-segura")
        usuario.groups.add(Group.objects.get(name="Médico"))
        medico = Medico.objects.create(
            usuario=usuario,
            nombre="Elena",
            apellidos="García",
            especialidad="GENERAL",
            telefono="5550000000",
        )
        otro_medico = Medico.objects.create(
            nombre="Luis",
            apellidos="Pérez",
            especialidad="PEDIATRIA",
            telefono="5551111111",
        )
        paciente = Paciente.objects.create(
            nombre="Ana",
            apellidos="López",
            fecha_nacimiento="1990-05-10",
            telefono="5551234567",
        )
        fecha = timezone.localdate() + timedelta(days=1)
        Cita.objects.create(
            paciente=paciente,
            medico=medico,
            fecha=fecha,
            hora="10:00",
            motivo="Consulta de Elena",
        )
        Cita.objects.create(
            paciente=paciente,
            medico=otro_medico,
            fecha=fecha,
            hora="11:00",
            motivo="Consulta de Luis",
        )
        acceso = self.client.post(
            reverse("login"),
            {"username": "elena", "password": "clave-segura", "rol": "medico"},
        )
        self.assertRedirects(acceso, reverse("inicio"))
        respuesta = self.client.get(reverse("agenda"))

        self.assertContains(respuesta, "Médico")
        self.assertContains(respuesta, "Dr(a). Elena García")
        self.assertNotContains(respuesta, "Dr(a). Luis Pérez")
        self.assertEqual(self.client.get(reverse("pacientes")).status_code, 403)


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

    def test_registrar_medico_crea_credenciales_para_iniciar_sesion(self):
        self.client.force_login(self.administrador)
        respuesta = self.client.post(
            reverse("medicos"),
            {
                "nombre": "Sofía",
                "apellidos": "Ramírez",
                "especialidad": "GENERAL",
                "telefono": "5554443322",
                "activo": "on",
                "usuario_login": "sofia_medica",
                "contrasena": "S7!qL9#vP2@k",
                "confirmar_contrasena": "S7!qL9#vP2@k",
            },
        )

        self.assertRedirects(respuesta, reverse("medicos"))
        medico = Medico.objects.get(nombre="Sofía")
        self.assertEqual(medico.usuario.username, "sofia_medica")
        self.assertTrue(medico.usuario.check_password("S7!qL9#vP2@k"))
        self.assertTrue(medico.usuario.groups.filter(name="Médico").exists())

        acceso = self.client.post(
            reverse("login"),
            {
                "username": "sofia_medica",
                "password": "S7!qL9#vP2@k",
                "rol": "medico",
            },
        )
        self.assertRedirects(acceso, reverse("inicio"))
        self.assertContains(self.client.get(reverse("agenda")), "Médico")

    def test_rechaza_registro_medico_si_las_contrasenas_no_coinciden(self):
        self.client.force_login(self.administrador)
        respuesta = self.client.post(
            reverse("medicos"),
            {
                "nombre": "Sofía",
                "apellidos": "Ramírez",
                "especialidad": "GENERAL",
                "telefono": "5554443322",
                "activo": "on",
                "usuario_login": "sofia_medica",
                "contrasena": "S7!qL9#vP2@k",
                "confirmar_contrasena": "OtraClaveSegura2026!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="sofia_medica").exists())
        self.assertContains(respuesta, "Las contraseñas no coinciden.")

    def test_administrador_puede_cambiar_usuario_y_contrasena_del_medico(self):
        usuario = User.objects.create_user(
            username="dra_elena",
            password="V1eja!Q8#rX3",
            first_name="Elena",
            last_name="García",
        )
        usuario.groups.add(Group.objects.get(name="Médico"))
        self.medico.usuario = usuario
        self.medico.save()
        self.client.force_login(self.administrador)
        url_edicion = reverse("editar_medico", args=[self.medico.pk])

        respuesta = self.client.get(url_edicion)
        self.assertContains(respuesta, 'value="dra_elena"')

        respuesta = self.client.post(
            url_edicion,
            {
                "nombre": "Elena",
                "apellidos": "García",
                "especialidad": "PEDIATRIA",
                "telefono": "5551234567",
                "activo": "on",
                "usuario_login": "elena_consultorio",
                "contrasena": "Q8!vR4#mT2@x",
                "confirmar_contrasena": "Q8!vR4#mT2@x",
            },
        )
        self.assertRedirects(respuesta, reverse("medicos"))

        usuario.refresh_from_db()
        self.assertEqual(usuario.username, "elena_consultorio")
        self.assertTrue(usuario.check_password("Q8!vR4#mT2@x"))

        respuesta = self.client.post(
            url_edicion,
            {
                "nombre": "Elena",
                "apellidos": "García",
                "especialidad": "PEDIATRIA",
                "telefono": "5551234567",
                "activo": "on",
                "usuario_login": "elena_consultorio",
                "contrasena": "",
                "confirmar_contrasena": "",
            },
        )
        self.assertRedirects(respuesta, reverse("medicos"))
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password("Q8!vR4#mT2@x"))

        self.client.logout()
        acceso = self.client.post(
            reverse("login"),
            {
                "username": "elena_consultorio",
                "password": "Q8!vR4#mT2@x",
                "rol": "medico",
            },
        )
        self.assertRedirects(acceso, reverse("inicio"))

    def test_administrador_busca_y_edita_medico(self):
        self.client.force_login(self.administrador)
        respuesta = self.client.get(reverse("medicos"), {"q": "Elena"})
        self.assertContains(respuesta, "Elena García")
        respuesta = self.client.get(reverse("medicos"), {"q": "Pediatría"})
        self.assertContains(respuesta, "Elena García")
        respuesta = self.client.get(reverse("editar_medico", args=[self.medico.pk]))
        self.assertContains(respuesta, "Editar médico")
        self.assertContains(respuesta, "Guardar")
        self.assertContains(respuesta, 'value="Elena"')

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

    def test_recepcionista_puede_ver_medicos_pero_no_editarlos(self):
        recepcionista = User.objects.create_user(username="recepcion", password="clave-segura")
        recepcionista.groups.add(Group.objects.get(name="Recepcionista"))
        self.client.force_login(recepcionista)
        medico_inactivo = Medico.objects.create(
            nombre="Luis",
            apellidos="Pérez",
            especialidad="PEDIATRIA",
            telefono="5551111111",
            activo=False,
        )

        respuesta = self.client.get(reverse("medicos"))
        self.assertContains(respuesta, "Elena García")
        self.assertContains(respuesta, "Luis Pérez")
        self.assertNotContains(respuesta, "Registrar médico")

        respuesta = self.client.post(
            reverse("editar_medico", args=[self.medico.pk]),
            {"nombre": "No autorizado"},
        )
        self.assertEqual(respuesta.status_code, 403)

        respuesta = self.client.post(
            reverse("medicos"),
            {
                "nombre": "No autorizado",
                "apellidos": "No autorizado",
                "especialidad": "GENERAL",
                "telefono": "5550000000",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 403)

        paciente = Paciente.objects.create(
            nombre="Ana",
            apellidos="López",
            fecha_nacimiento="1990-05-10",
            telefono="5551234567",
        )
        fecha = timezone.localdate() + timedelta(days=1)
        Cita.objects.create(
            paciente=paciente,
            medico=self.medico,
            fecha=fecha,
            hora="10:00",
            motivo="Consulta uno",
        )
        Cita.objects.create(
            paciente=paciente,
            medico=medico_inactivo,
            fecha=fecha,
            hora="11:00",
            motivo="Consulta dos",
        )
        agenda = self.client.get(reverse("agenda"))
        self.assertContains(agenda, "Elena García")
        self.assertContains(agenda, "Luis Pérez")

        respuesta = self.client.post(
            reverse("agregar_horario"),
            {"medico": self.medico.pk, "dia_semana": 0, "hora_inicio": "09:00", "hora_fin": "10:00"},
        )
        self.assertEqual(respuesta.status_code, 403)


class CitasTests(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            nombre="Juan",
            apellidos="Pérez López",
            fecha_nacimiento="1990-03-15",
            telefono="6641234567",
        )
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellidos="Méndez Ortiz",
            especialidad="PEDIATRIA",
            telefono="6645552222",
        )
        hoy = timezone.localdate()
        dias_para_miercoles = (2 - hoy.weekday()) % 7 or 7
        self.proximo_miercoles = hoy + timedelta(days=dias_para_miercoles)
        Horario.objects.create(medico=self.medico, dia_semana=2, hora_inicio="09:00", hora_fin="12:00")
        Horario.objects.create(medico=self.medico, dia_semana=2, hora_inicio="15:00", hora_fin="19:00")

        simulador = patch("clinica.forms.obtener_festivos", return_value={})
        self.festivos_api = simulador.start()
        self.addCleanup(simulador.stop)

    def datos_cita(self, **cambios):
        datos = {
            "paciente": self.paciente.pk,
            "medico": self.medico.pk,
            "fecha": self.proximo_miercoles,
            "hora": "16:00",
            "motivo": "Revisión general",
        }
        datos.update(cambios)
        return datos

    def test_acepta_cita_en_segundo_horario_del_dia(self):
        formulario = CitaForm(self.datos_cita())
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_rechaza_cita_en_fecha_pasada(self):
        formulario = CitaForm(self.datos_cita(fecha="2025-01-01", hora="10:00"))
        self.assertFalse(formulario.is_valid())
        self.assertIn("fecha", formulario.errors)

    def test_rechaza_medico_inactivo(self):
        self.medico.activo = False
        self.medico.save()
        formulario = CitaForm(self.datos_cita())
        self.assertFalse(formulario.is_valid())
        self.assertIn("medico", formulario.errors)

    def test_rechaza_cita_en_dia_festivo(self):
        self.festivos_api.return_value = {self.proximo_miercoles: "Día festivo de prueba"}
        formulario = CitaForm(self.datos_cita())
        self.assertFalse(formulario.is_valid())
        self.assertIn("fecha", formulario.errors)

    def test_agenda_aunque_falle_la_api_de_festivos(self):
        self.festivos_api.return_value = None
        formulario = CitaForm(self.datos_cita())
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertTrue(formulario.festivos_no_disponibles)