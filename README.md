# MediConsult

Sistema web para organizar las citas de un consultorio médico pequeño. Proyecto final de **Herramientas de Desarrollo de Software**, UABC.

**Integrantes:** Leonardo Rommel Hernández Cabanillas y Yosmar Zavala Quiroz.

## Funciones

- Inicio de sesión con roles de **Paciente**, **Médico**, **Recepcionista** y **Administrador**.
- Registro público de pacientes y consulta privada de sus propias citas.
- **Pacientes:** registrar, buscar y editar.
- **Médicos y horarios** (solo Administrador): registrar médicos, sus especialidades y sus días y horas de atención.
- **Agenda:** agendar citas y marcarlas como atendidas o canceladas.
- **Validaciones** al agendar: no se permiten fechas pasadas, horarios fuera de la atención del médico, horarios ocupados, médicos inactivos ni días festivos.
- **API externa:** consulta los días festivos de México con [Nager.Date](https://date.nager.at). Si la API no responde, el sistema sigue funcionando y muestra un aviso.

## Tecnologías

- Python 3.13 y Django 6.1
- SQLite (base de datos)
- Bootstrap 5 (interfaz)
- requests (consumo de la API)

## Instalación

Requisitos: Python 3.12 o superior y Git.

```
git clone https://github.com/rommelhernandez-ai/mediconsult.git
cd mediconsult
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Después abre http://127.0.0.1:8000/ e inicia sesión con el superusuario.

> En macOS o Linux, usa `python3 -m venv venv` y `source venv/bin/activate`.

## Roles

Los grupos **Administrador**, **Recepcionista**, **Paciente** y **Médico** se crean solos con `migrate`. Los pacientes pueden crear su propia cuenta desde **Regístrate como paciente** en la pantalla de acceso. Para registrar un médico, el administrador usa el formulario **Médicos** e indica el nombre de usuario y la contraseña inicial; el sistema crea y vincula su cuenta automáticamente. Las cuentas de recepción se crean desde **Usuarios** en Django Admin y se asignan al grupo **Recepcionista**.

1. Entra a http://127.0.0.1:8000/ con una cuenta de administrador.
2. Abre **Médicos** y registra al médico con las credenciales que usará para iniciar sesión.
3. Comparte con el médico el nombre de usuario y la contraseña inicial definidos en el formulario. Al editar el médico, el administrador puede cambiar el usuario y definir una contraseña nueva; si deja la contraseña vacía, se conserva la actual.

Los pacientes solo pueden consultar y agendar sus propias citas, y ver médicos activos. Los médicos ven únicamente su agenda y sus citas asignadas. Recepción puede consultar todos los pacientes, médicos, citas y agendas, además de gestionar pacientes y citas. Solo el administrador puede registrar o editar médicos y horarios.

## Pruebas y rendimiento

```
python manage.py test clinica
python manage.py medir_rendimiento
```

- `test` ejecuta las pruebas unitarias de la aplicación.
- `medir_rendimiento` mide el tiempo de la consulta de días festivos. Con la caché, el promedio bajó de 183.7 ms a 37.8 ms.

## Datos de demostración

```
python manage.py cargar_demo
```

Borra los datos de la clínica y carga médicos, horarios, pacientes y citas ficticios de demostración. No modifica los usuarios.

## Estructura

```
config/              Configuración general del proyecto
clinica/
├── models.py        Paciente, Médico, Horario y Cita
├── forms.py         Formularios y validaciones de citas
├── views.py         Lógica de cada página
├── servicios.py     Consulta a la API Nager.Date con caché
├── permissions.py   Reglas del rol Administrador
├── tests.py         Pruebas unitarias
├── templates/       Plantillas HTML
└── static/          Estilos (CSS)
```