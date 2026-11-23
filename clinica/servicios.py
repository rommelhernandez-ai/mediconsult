from datetime import date

import requests
from django.core.cache import cache

URL_FESTIVOS = "https://date.nager.at/api/v3/PublicHolidays/{anio}/MX"
UN_DIA = 60 * 60 * 24


def obtener_festivos(anio):
    """Consulta los días festivos de México en la API Nager.Date.

    Regresa un diccionario {fecha: nombre} o None si la API no responde.
    El resultado se guarda en caché un día para no repetir la consulta.
    """
    clave = f"festivos_mx_{anio}"
    festivos = cache.get(clave)
    if festivos is not None:
        return festivos

    try:
        respuesta = requests.get(URL_FESTIVOS.format(anio=anio), timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException:
        return None

    festivos = {date.fromisoformat(festivo["date"]): festivo["localName"] for festivo in datos}
    cache.set(clave, festivos, UN_DIA)
    return festivos