"""
Cliente ligero para la API Tempus 3 del Instituto Nacional de Estadística (INE).

El INE ofrece su base de datos estadística a través de un servicio JSON denominado
**wstempus**.  La función `DATOS_TABLA` permite obtener todos los datos de una
tabla a partir de su identificador numérico【293243866024462†L33-L45】.  Estos
identificadores se extraen del parámetro `t` presente en las URL de las
tablas de INEbase (por ejemplo, en
`https://www.ine.es/jaxiT3/Tabla.htm?t=50902` el identificador es `50902`).

La API admite distintos parámetros:

* `nult` para solicitar únicamente los últimos `n` periodos de la serie【293243866024462†L46-L51】.
* `tip` para indicar la periodicidad de interés: `M` (mensual), `T` (trimestral),
  `A` (anual) o combinaciones como `AM`【209883142194744†L42-L45】.
* `tv` para filtrar por variables concretas.  Cada variable y valor se
  especifica como `varId:valorId`, pudiendo repetirse tantas veces como
  filtros se deseen【293243866024462†L54-L96】.  Para conocer los valores
  disponibles de una variable se puede utilizar la función
  `VALORES_GRUPOSTABLA`【287621410694593†L86-L93】.

Este módulo implementa una función `get_table_data` que encapsula las
peticiones HTTP y devuelve la respuesta en formato JSON.  También se
incluye una función `json_to_dataframe` que convierte el JSON en un
`pandas.DataFrame` y realiza algunas transformaciones útiles (renombrado
de columnas, conversión de fechas, etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd
import requests
from dateutil import parser as date_parser


BASE_URL = "https://servicios.ine.es/wstempus/js"


class INEAPIError(Exception):
    """Excepción personalizada para errores en las peticiones al INE."""
    pass


def get_table_data(
    table_id: str,
    language: str = "ES",
    nult: Optional[int] = None,
    tip: Optional[str] = None,
    tv: Optional[List[str]] = None,
    timeout: int = 30,
) -> List[Dict[str, Any]]:
    """
    Descarga los datos de una tabla del INE en formato JSON.

    Parameters
    ----------
    table_id : str
        Identificador numérico de la tabla (parámetro `t` en la URL de INEbase).
    language : str, default 'ES'
        Idioma en el que se solicita la respuesta (`ES` para español o `EN` para
        inglés).  La URL final tendrá la forma
        `https://servicios.ine.es/wstempus/js/{language}/DATOS_TABLA/{table_id}`【293243866024462†L33-L45】.
    nult : int, optional
        Número de últimos registros a obtener.  Si se omite, se devuelven
        todos los periodos disponibles【293243866024462†L46-L51】.
    tip : str, optional
        Periodicidad de la serie.  Las tablas pueden contener datos
        mensuales, trimestrales y anuales, por lo que este parámetro permite
        seleccionar únicamente el tipo deseado (por ejemplo `M` o `T`).
    tv : list of str, optional
        Filtros sobre variables.  Cada elemento debe tener el formato
        `varId:valorId`.  La API admite múltiples parámetros `tv` para
        filtrar distintos valores【293243866024462†L54-L96】.
    timeout : int, default 30
        Tiempo máximo en segundos a esperar la respuesta del servidor.

    Returns
    -------
    list of dict
        Respuesta JSON de la API decodificada como lista de diccionarios.

    Raises
    ------
    INEAPIError
        Si la respuesta del servidor no es satisfactoria.
    """
    endpoint = f"{BASE_URL}/{language}/DATOS_TABLA/{table_id}"
    params = {}
    if nult is not None:
        params["nult"] = nult
    if tip:
        params["tip"] = tip
    # La API requiere un parámetro tv por cada filtro, por lo que generamos
    # una lista de tuplas en lugar de un único valor separado por comas.
    tv_params = []
    if tv:
        for value in tv:
            tv_params.append(("tv", value))

    try:
        # Construimos una lista de parámetros [(clave, valor)] para que
        # requests incluya parámetros repetidos (varios 'tv').
        all_params: List[tuple] = []
        for key, val in params.items():
            all_params.append((key, val))
        for tv_param in tv_params:
            all_params.append(tv_param)
        response = requests.get(
            endpoint,
            params=all_params,
            timeout=timeout,
        )
    except Exception as exc:
        raise INEAPIError(f"Error al realizar la solicitud: {exc}") from exc

    if response.status_code != 200:
        raise INEAPIError(
            f"Respuesta no satisfactoria: {response.status_code} {response.text[:200]}"
        )

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise INEAPIError(f"No se pudo decodificar la respuesta JSON: {exc}") from exc
    return data


def json_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convierte la respuesta JSON del INE en un DataFrame de pandas.

    La estructura devuelta por la API es una lista de diccionarios con las
    siguientes claves principales:

    * `DATA`: lista de registros, cada uno con un campo `Valor` y un
      identificador de serie (`Id`) más un diccionario de dimensiones.
    * `METADATA`: información sobre las variables y valores empleados en la
      tabla (no se utiliza directamente en esta función).

    Esta función recorre los registros de `DATA` y extrae:

    * `Fecha`: se convierte a un objeto `datetime` utilizando `dateutil`.
    * `Valor`: se fuerza a `float` siempre que sea posible.
    * Otras dimensiones: se dejan como columnas de tipo `object`.

    Parameters
    ----------
    data : list of dict
        Respuesta JSON devuelta por `get_table_data`.

    Returns
    -------
    pandas.DataFrame
        DataFrame con una fila por observación y columnas para cada
        dimensión, además de `Valor`.
    """
    records = []
    for obs in data:
        # Cada registro contiene claves para las dimensiones (por ejemplo
        # "Comunidad" o "Periodo") y el campo "Valor".
        record: Dict[str, Any] = {}
        for k, v in obs.items():
            # Ignoramos las claves de metadatos
            if k in {"NombreSerie", "Id"}:
                continue
            if k == "Valor":
                # Algunos valores llegan como cadenas vacías
                try:
                    record[k] = float(v)
                except (TypeError, ValueError):
                    record[k] = None
            elif k.lower() in {"fecha", "periodo"}:
                # Convertimos formatos como 2025M09 a un datetime
                record["Fecha"] = _parse_period(v)
            else:
                record[k] = v
        records.append(record)
    df = pd.DataFrame.from_records(records)
    # Reordenamos columnas para que Fecha quede la primera
    cols = list(df.columns)
    if "Fecha" in cols:
        cols.insert(0, cols.pop(cols.index("Fecha")))
        df = df[cols]
    return df


def _parse_period(value: str) -> datetime:
    """
    Convierte el identificador de periodo del INE a un `datetime`.

    Los periodos mensuales se representan como `YYYYMmm`, los trimestrales como
    `YYYYTq` y los anuales como `YYYY`.  Esta función interpreta esos
    formatos y devuelve el primer día del periodo.
    """
    value = str(value)
    if "M" in value:
        # Formato mensual, ej. 2025M09
        year, month = value.split("M")
        return datetime(int(year), int(month), 1)
    if "T" in value:
        # Formato trimestral, ej. 2025T3
        year, quarter = value.split("T")
        month = (int(quarter) - 1) * 3 + 1
        return datetime(int(year), month, 1)
    # Anual
    try:
        return datetime(int(value), 1, 1)
    except ValueError:
        # Si no se puede interpretar, se devuelve None
        return None


def filter_by_region(df: pd.DataFrame, region_name: str) -> pd.DataFrame:
    """
    Filtra un DataFrame obtenido con `json_to_dataframe` por el nombre de una
    Comunidad Autónoma.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame con al menos una columna que contenga la dimensión de
        comunidad.  La columna puede llamarse `Comunidades y Ciudades Autónomas` o
        similar dependiendo de la tabla.
    region_name : str
        Nombre de la comunidad que se desea conservar (por ejemplo, `Extremadura`).

    Returns
    -------
    pandas.DataFrame
        Subconjunto de `df` que solo contiene las filas de la comunidad
        especificada.  Si no se encuentra la columna de comunidad, se devuelve
        el DataFrame original.
    """
    # Buscamos la columna que contiene la comunidad autónoma
    candidates = [
        col
        for col in df.columns
        if "comunidad" in col.lower() or "autónom" in col.lower() or "ccaa" in col.lower()
    ]
    if not candidates:
        return df
    community_col = candidates[0]
    return df[df[community_col] == region_name].copy()
