"""
03 - Descarga GloFAS Historical para un día y la zona de Mato Grosso do Sul.

IMPORTANTE: el esquema de la API cambió en 2026. Este script usa los campos
vigentes documentados por CEMS/EWDS para GloFAS Historical v4:
  year/month/day, timespan=time_mean,
  average_river_discharge_in_the_last_24_hours.

Requiere cuenta y credenciales de CDS/EWDS configuradas para cdsapi.
Ejemplo:
  python scripts/03_download_glofas.py --date 2025-03-10
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import cdsapi

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "processed" / "glofas"
# North, West, South, East. Margen para incluir puntos de grilla cercanos al borde.
AREA = [-16.5, -58.7, -24.6, -50.4]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--product-type", default="consolidated", choices=["consolidated", "intermediate"])
    return p.parse_args()


def main():
    args = parse_args()
    d = date.fromisoformat(args.date)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"glofas_ms_{args.date}.nc"

    request = {
        "system_version": ["version_4_0"],
        "hydrological_model": ["lisflood"],
        "product_type": [args.product_type],
        "variable": ["average_river_discharge_in_the_last_24_hours"],
        "timespan": ["time_mean"],
        "year": [f"{d.year:04d}"],
        "month": [f"{d.month:02d}"],
        "day": [f"{d.day:02d}"],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }

    print(f"Solicitando GloFAS {args.date} para MS …")
    cdsapi.Client().retrieve("cems-glofas-historical", request).download(str(out))
    print(f"Guardado {out}")


if __name__ == "__main__":
    main()
