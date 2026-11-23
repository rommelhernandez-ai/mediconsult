from time import perf_counter

from django.core.management.base import BaseCommand

from clinica.servicios import obtener_festivos


class Command(BaseCommand):
    help = "Mide cuánto tarda la consulta de días festivos (API Nager.Date)."

    def handle(self, *args, **options):
        tiempos = []
        for intento in range(1, 6):
            inicio = perf_counter()
            obtener_festivos(2026)
            milisegundos = (perf_counter() - inicio) * 1000
            tiempos.append(milisegundos)
            self.stdout.write(f"Consulta {intento}: {milisegundos:.1f} ms")

        promedio = sum(tiempos) / len(tiempos)
        self.stdout.write(self.style.SUCCESS(f"Promedio: {promedio:.1f} ms"))