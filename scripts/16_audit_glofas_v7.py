#!/usr/bin/env python3
"""Auditoria rápida dos quatro arquivos V7 e comparação com o backup V6, se existir."""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "docs" / "data" / "pulse"
OLD = ROOT / "data" / "audit" / "pulse_v6_nearest_pin"
DATES = ["2001-02-08", "2010-02-08", "2020-02-08", "2025-02-08"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def line(d):
    if not d:
        return "sem arquivo"
    s = d.get("summary", {})
    if d.get("network", {}).get("type") == "glofas_lisflood_v4":
        return (f"n={s.get('segments_with_discharge')} | zeros={s.get('zero_fraction')} | "
                f"P50={s.get('discharge_p50_m3s')} | P90={s.get('discharge_p90_m3s')} | "
                f"P95={s.get('discharge_p95_m3s')} | max={s.get('discharge_max_m3s')} m3/s")
    return (f"n={s.get('segments_with_discharge')} | mediana={s.get('discharge_median_m3s')} | "
            f"P95={s.get('discharge_p95_m3s')} m3/s | método V6 nearest PIN")


def main():
    print("AUDITORIA PULSO HÍDRICO MS — GloFAS V7\n")
    for d in DATES:
        print(d)
        print("  V7:", line(read(NEW / f"{d}.json")))
        old = read(OLD / f"{d}.json")
        if old:
            print("  V6:", line(old))
    print("\nCritério: V7 deve usar network.type=glofas_lisflood_v4 e deixar PIN MS apenas como contexto.")

if __name__ == "__main__":
    main()
