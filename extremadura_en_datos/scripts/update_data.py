"""
Script de actualización de datos para Extremadura en Datos.

Este programa lee la lista de tablas que se encuentran en el Excel
`Datos Extremadura Mensual.xlsx` y descarga las series temporales
correspondientes a cada tabla utilizando la API Tempus 3 del INE.  Los
datos se filtran para la Comunidad Autónoma de Extremadura cuando
procede, se limpian y se guardan en ficheros CSV y JSON dentro de la
carpeta `data/`.

El script puede ejecutarse periódicamente (por ejemplo, mediante cron o
GitHub Actions) y acepta argumentos opcionales para limitar el número
de periodos descargados o para realizar pruebas sin descargar nada.

Uso:

```bash
python scripts/update_data.py --excel Datos\u00a0Extremadura\u00a0Mensual.xlsx --last 12
```

Dependencias: pandas, requests, dateutil (véase requirements.txt).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ine_api import get_table_data, json_to_dataframe, filter_by_region, INEAPIError


DEFAULT_REGION = "Extremadura"


def extract_table_id(url: str) -> Optional[str]:
    """Extrae el parámetro `t` de una URL de INEbase."""
    m = re.search(r"[?&]t=(\d+)", url)
    if m:
        return m.group(1)
    return None


def process_table(
    table_id: str,
    region: str,
    nult: Optional[int] = None,
    tip: Optional[str] = None,
) -> pd.DataFrame:
    """
    Descarga y procesa una tabla del INE para una comunidad autónoma.

    Parameters
    ----------
    table_id : str
        Identificador de la tabla (obtenido del Excel).
    region : str
        Nombre de la comunidad autónoma a filtrar (p. ej. 'Extremadura').
    nult : int, optional
        Número de últimas observaciones a descargar.  Si se omite se
        recupera la serie completa.
    tip : str, optional
        Periodicidad deseada (por ejemplo 'M' para tablas mensuales).

    Returns
    -------
    pandas.DataFrame
        DataFrame procesado con las columnas relevantes.  Incluye la
        columna `Valor` numérica y `Fecha` como índice.
    """
    # Descarga los datos completos o acotados
    try:
        data = get_table_data(table_id, nult=nult, tip=tip)
    except INEAPIError as exc:
        print(f"[ERROR] No se pudo descargar la tabla {table_id}: {exc}", file=sys.stderr)
        raise
    df = json_to_dataframe(data)
    # Filtrar por comunidad
    df = filter_by_region(df, region)
    # Establecer Fecha como índice si existe
    if "Fecha" in df.columns:
        df = df.set_index("Fecha").sort_index()
    return df


def save_dataset(df: pd.DataFrame, out_dir: Path, table_id: str) -> None:
    """Guarda un DataFrame en CSV y JSON en la carpeta indicada."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{table_id}.csv"
    json_path = out_dir / f"{table_id}.json"
    df.to_csv(csv_path)
    df.reset_index().to_json(json_path, orient="records", date_format="iso")
    print(f"[INFO] Guardado {table_id} en {csv_path} y {json_path}")


def main(args: argparse.Namespace) -> None:
    # Leer el Excel
    df_excel = pd.read_excel(args.excel, header=2)
    # Crear directorios de salida
    raw_dir = Path(args.output) / "raw"
    processed_dir = Path(args.output) / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    for _, row in df_excel.iterrows():
        url = row.get("URL")
        if not isinstance(url, str) or not url:
            continue
        table_id = extract_table_id(url)
        if not table_id:
            print(f"[WARN] No se encontró identificador en {url}")
            continue
        if args.dry_run:
            print(f"[DRY] Tabla {table_id} ({row.get('Métricas')}) se descargaría")
            continue
        try:
            # Determinar tip a partir de periodicidad
            periodicidad = str(row.get("Periodicidad", "")).strip().lower()
            tip = None
            if "mensual" in periodicidad:
                tip = "M"
            elif "trimestral" in periodicidad:
                tip = "T"
            # Descargar
            df_table = process_table(table_id, region=DEFAULT_REGION, nult=args.last, tip=tip)
            # Guardar datos crudos
            save_dataset(df_table, processed_dir, table_id)
        except Exception as exc:
            print(f"[ERROR] Error procesando la tabla {table_id}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actualiza los datos de la web Extremadura en Datos")
    parser.add_argument(
        "--excel",
        type=str,
        default="Datos Extremadura Mensual.xlsx",
        help="Ruta al fichero Excel con la lista de tablas",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data",
        help="Directorio donde se guardarán los datos descargados",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        help="Número de últimos periodos a descargar (opcional)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No descargar los datos; solo mostrar qué se haría",
    )
    args = parser.parse_args()
    main(args)
