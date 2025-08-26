"""
Módulo para descargar y analizar el calendario de publicaciones del INE.

El INE publica un calendario anual de disponibilidades estadísticas en su
sección INEbase.  El calendario se puede descargar en formato iCal/ICS y
contiene, para cada operación estadística, la fecha de publicación prevista
【931099734450141†L16-L24】.  Este módulo descarga el fichero .ics y lo
convierte en una lista de eventos con su título y fecha.

Requiere la biblioteca `icalendar`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import requests
from icalendar import Calendar


class CalendarDownloadError(Exception):
    pass


@dataclass
class INEEvent:
    """Representa un evento de publicación extraído del calendario."""
    title: str
    date: datetime


def download_calendar(url: str, timeout: int = 30) -> Calendar:
    """
    Descarga un fichero .ics desde la URL indicada y devuelve un objeto `Calendar`.

    Parameters
    ----------
    url : str
        Dirección HTTP del fichero .ics.
    timeout : int, default 30
        Tiempo máximo de espera en segundos.

    Returns
    -------
    icalendar.Calendar
        Objeto de calendario parseado.
    """
    try:
        response = requests.get(url, timeout=timeout)
    except Exception as exc:
        raise CalendarDownloadError(f"No se pudo descargar el calendario: {exc}") from exc
    if response.status_code != 200:
        raise CalendarDownloadError(f"Respuesta no satisfactoria: {response.status_code}")
    return Calendar.from_ical(response.content)


def extract_events(cal: Calendar) -> List[INEEvent]:
    """
    Extrae todos los eventos de un objeto `Calendar` del INE.

    Parameters
    ----------
    cal : icalendar.Calendar
        Calendario previamente descargado y parseado.

    Returns
    -------
    list of INEEvent
        Lista con los eventos (publicaciones) contenidos en el calendario.
    """
    events: List[INEEvent] = []
    for component in cal.walk():
        if component.name == "VEVENT":
            title = str(component.get("SUMMARY"))
            dtstart = component.get("DTSTART").dt
            if isinstance(dtstart, datetime):
                date = dtstart
            else:
                # Si llega como fecha sin hora
                date = datetime.combine(dtstart, datetime.min.time())
            events.append(INEEvent(title=title, date=date))
    return events
