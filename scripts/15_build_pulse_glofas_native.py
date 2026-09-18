#!/usr/bin/env python3
"""Reconstrói os quatro pulsos de teste usando a rede nativa GloFAS v4.

Não associa mais cada trecho PIN ao pixel mais próximo. Cada segmento dinâmico
corresponde a uma célula da própria rede LISFLOOD com área a montante >=250 km².
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "docs" / "data" / "glofas_network.geojson"
GLOFAS_DIR = ROOT / "data" / "processed" / "glofas"
OUT_DIR = ROOT / "docs" / "data" / "pulse"
BACKUP = ROOT / "data" / "audit" / "pulse_v6_nearest_pin"
DATES = ["2001-02-08", "2010-02-08", "2020-02-08", "2025-02-08"]


def coord_name(ds, candidates, label):
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    raise RuntimeError(f"não foi possível detectar {label}; coords={list(ds.coords)}")


def data_var(ds):
    preferred = ["dis24", "discharge", "river_discharge", "average_river_discharge_in_the_last_24_hours"]
    for name in preferred:
        if name in ds.data_vars:
            return name
    for name in ds.data_vars:
        low = name.lower()
        if "dis" in low or "river" in low:
            return name
    if len(ds.data_vars) == 1:
        return list(ds.data_vars)[0]
    raise RuntimeError(f"descarga não detectada; vars={list(ds.data_vars)}")


def visual_index(q):
    if not np.isfinite(q) or q < 0:
        return None
    return round(float(np.clip(np.log10(q + 1.0) / 5.0 * 100.0, 0, 100)), 2)


def fmt(v):
    return round(float(v), 3)


def backup_old(date_str: str):
    old = OUT_DIR / f"{date_str}.json"
    if not old.exists():
        return
    try:
        data = json.loads(old.read_text(encoding="utf-8"))
        if data.get("network", {}).get("type") == "glofas_lisflood_v4":
            return
    except Exception:
        pass
    BACKUP.mkdir(parents=True, exist_ok=True)
    target = BACKUP / old.name
    if not target.exists():
        shutil.copy2(old, target)


def main() -> int:
    if not NETWORK.exists():
        raise SystemExit("Falta docs/data/glofas_network.geojson. Execute scripts/14_build_glofas_network_v4.py")
    fc = json.loads(NETWORK.read_text(encoding="utf-8"))
    feats = fc.get("features") or []
    if not feats:
        raise SystemExit("Rede GloFAS vazia.")

    ids = [str(f["properties"]["glofas_id"]) for f in feats]
    lons = np.asarray([f["properties"]["glofas_lon"] for f in feats], dtype=float)
    lats = np.asarray([f["properties"]["glofas_lat"] for f in feats], dtype=float)
    upareas = np.asarray([f["properties"]["upstream_area_km2"] for f in feats], dtype=float)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built = []
    print(f"Rede nativa GloFAS: {len(ids):,} células/segmentos")

    for date_str in DATES:
        src = GLOFAS_DIR / f"glofas_ms_{date_str}.nc"
        if not src.exists():
            print(f"[faltando] {src.name}")
            continue
        backup_old(date_str)
        with xr.open_dataset(src) as ds:
            lon_name = coord_name(ds, ["longitude", "lon", "x"], "longitude")
            lat_name = coord_name(ds, ["latitude", "lat", "y"], "latitude")
            var = data_var(ds)
            da = ds[var].squeeze(drop=True)
            for tname in ("valid_time", "time", "date"):
                if tname in da.dims:
                    da = da.isel({tname: 0}).squeeze(drop=True)
            sampled = da.sel({
                lon_name: xr.DataArray(lons, dims="points"),
                lat_name: xr.DataArray(lats, dims="points"),
            }, method="nearest")
            q = np.asarray(sampled.values, dtype=float).reshape(-1)

        segments = {}
        finite = np.isfinite(q) & (q >= 0)
        vals = q[finite]
        for rid, qi, ua, ok in zip(ids, q, upareas, finite):
            if not ok:
                continue
            segments[rid] = {
                "discharge_m3s": fmt(qi),
                "discharge_index": visual_index(qi),
                "upstream_area_km2": round(float(ua), 2),
                "temperature_c": None,
            }

        if vals.size:
            summary = {
                "segments_with_discharge": int(vals.size),
                "segments_positive": int(np.sum(vals > 0)),
                "zero_fraction": round(float(np.mean(vals == 0)), 4),
                "discharge_p50_m3s": fmt(np.percentile(vals, 50)),
                "discharge_p90_m3s": fmt(np.percentile(vals, 90)),
                "discharge_p95_m3s": fmt(np.percentile(vals, 95)),
                "discharge_max_m3s": fmt(np.max(vals)),
            }
        else:
            summary = {"segments_with_discharge": 0, "segments_positive": 0, "zero_fraction": None,
                       "discharge_p50_m3s": None, "discharge_p90_m3s": None,
                       "discharge_p95_m3s": None, "discharge_max_m3s": None}

        payload = {
            "date": date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "network": {
                "type": "glofas_lisflood_v4",
                "threshold_upstream_area_km2": 250,
                "feature_count": len(ids),
            },
            "segments": segments,
            "summary": summary,
            "sources": {
                "context_geometry": "PIN MS / IMASUL — Hidrografia",
                "dynamic_network": "CEMS GloFAS v4 / LISFLOOD — upstream area + LDD",
                "discharge": "GloFAS Historical v4 — average daily river discharge",
                "temperature": None,
            },
            "method": "native GloFAS/LISFLOOD river pixels >=250 km2 drainage area; discharge sampled on the same model grid",
            "note": "Descarga modelada por GloFAS; não é medição in situ. A rede PIN permanece apenas como contexto hidrográfico fino.",
        }
        out = OUT_DIR / f"{date_str}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        built.append(date_str)
        print(f"[ok] {out.name}: P90={summary['discharge_p90_m3s']} m³/s; max={summary['discharge_max_m3s']} m³/s; zeros={summary['zero_fraction']}")

    index = {
        "version": "0.7",
        "network": "glofas_lisflood_v4",
        "dates": built,
        "count": len(built),
    }
    (OUT_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("\nPulso V7 reconstruído. Recarregue a PWA com Ctrl+Shift+R.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
