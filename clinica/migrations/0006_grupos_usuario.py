from django.db import migrations


def crear_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="Administrador")
    Group.objects.using(schema_editor.connection.alias).get_or_create(name="Recepcionista")


class Migration(migrations.Migration):

    dependencies = [
        ("clinica", "0005_cita"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, migrations.RunPython.noop),
    ]
