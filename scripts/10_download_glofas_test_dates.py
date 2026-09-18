#!/usr/bin/env python3
"""Baixa quatro datas de teste do GloFAS Historical v4 para Mato Grosso do Sul.

Datas: 08/02/2001, 08/02/2010, 08/02/2020 e 08/02/2025.
A requisição usa apenas a variável de descarga média diária e recorta a área de MS.

Requer:
  1) conta no Copernicus Early Warning Data Store (EWDS)
  2) licenca do dataset cems-glofas-historical aceita no EWDS
  3) %USERPROFILE%\\.cdsapirc configurado
  4) cdsapi >= 0.7.7

Os arquivos são gravados em data/processed/glofas/.
"""
from __future__ import annotations

from pathlib import Path
import sys
import cdsapi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "glofas"
OUT.mkdir(parents=True, exist_ok=True)

DATASET = "cems-glofas-historical"
DATES = ["2001-02-08", "2010-02-08", "2020-02-08", "2025-02-08"]
# North, West, South, East. Margem para incluir pontos de grade junto ao limite.
AREA_MS = [-16.85, -58.40, -24.35, -50.55]


def request_for(date_str: str) -> dict:
    y, m, d = date_str.split("-")
    return {
        "system_version": ["version_4_0"],
        "product_type": ["consolidated"],
        "hydrological_model": ["lisflood"],
        "variable": ["average_river_discharge_in_the_last_24_hours"],
        "timespan": ["time_mean"],
        "year": [y],
        "month": [m],
        "day": [d],
        "area": AREA_MS,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def main() -> int:
    print("Pulso Hídrico MS — teste GloFAS")
    print("Datas:", ", ".join(DATES))
    print("Área:", AREA_MS, "(N, W, S, E)")
    print()
    try:
        client = cdsapi.Client()
    except Exception as exc:
        print("ERRO ao iniciar cdsapi:", exc, file=sys.stderr)
        print("Configure primeiro o arquivo .cdsapirc. Veja CONFIGURAR_GLOFAS.txt", file=sys.stderr)
        return 2

    for date_str in DATES:
        target = OUT / f"glofas_ms_{date_str}.nc"
        if target.exists() and target.stat().st_size > 1024:
            print(f"[já existe] {target.name} ({target.stat().st_size/1024/1024:.1f} MB)")
            continue
        print(f"[baixando] {date_str}")
        try:
            client.retrieve(DATASET, request_for(date_str), str(target))
        except Exception as exc:
            print(f"ERRO em {date_str}: {exc}", file=sys.stderr)
            print("Se aparecer 'licence/terms', aceite a licenca do dataset no portal EWDS.", file=sys.stderr)
            return 3
        print(f"[ok] {target.name} ({target.stat().st_size/1024/1024:.1f} MB)")

    print("\nQuatro datas baixadas. Agora execute scripts/11_build_pulse_from_pin.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
