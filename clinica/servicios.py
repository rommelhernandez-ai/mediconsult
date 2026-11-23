from datetime import date

import requests

URL_FESTIVOS = "https://date.nager.at/api/v3/PublicHolidays/{anio}/MX"


def obtener_festivos(anio):
    """Consulta los días festivos de México en la API Nager.Date.

    Regresa un diccionario {fecha: nombre} o None si la API no responde.
    """
    try:
        respuesta = requests.get(URL_FESTIVOS.format(anio=anio), timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.RequestException:
        return None

    return {date.fromisoformat(festivo["date"]): festivo["localName"] for festivo in datos}