#!/usr/bin/env python3
"""Cruza a hidrografia PIN MS/IMASUL com GloFAS e cria arquivos diários da PWA.

Método de teste:
- cada trecho da rede PIN MS recebe um ponto representativo no meio da geometria;
- a descarga é amostrada na célula GloFAS mais próxima;
- o índice 0–100 usado apenas para espessura cartográfica deriva de uma escala
  logarítmica fixa de 0 a 100.000 m³/s, portanto é comparável entre datas;
- o valor físico em m³/s é preservado no JSON.

Isto é uma associação cartográfica preliminar, não uma validação hidrológica nem
uma observação de estação fluviométrica.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RIVERS = ROOT / "docs" / "data" / "rivers.geojson"
GLOFAS_DIR = ROOT / "data" / "processed" / "glofas"
OUT_DIR = ROOT / "docs" / "data" / "pulse"
DATES = ["2001-02-08", "2010-02-08", "2020-02-08", "2025-02-08"]


def line_length(coords):
    total = 0.0
    for a, b in zip(coords, coords[1:]):
        total += math.hypot(b[0]-a[0], b[1]-a[1])
    return total


def midpoint_line(coords):
    if not coords:
        return None
    if len(coords) == 1:
        return float(coords[0][0]), float(coords[0][1])
    total = line_length(coords)
    if total <= 0:
        c = coords[len(coords)//2]
        return float(c[0]), float(c[1])
    target = total / 2.0
    acc = 0.0
    for a, b in zip(coords, coords[1:]):
        seg = math.hypot(b[0]-a[0], b[1]-a[1])
        if acc + seg >= target and seg > 0:
            f = (target - acc) / seg
            return float(a[0] + (b[0]-a[0])*f), float(a[1] + (b[1]-a[1])*f)
        acc += seg
    c = coords[-1]
    return float(c[0]), float(c[1])


def representative_point(geom):
    if not geom:
        return None
    typ = geom.get("type")
    coords = geom.get("coordinates") or []
    if typ == "LineString":
        return midpoint_line(coords)
    if typ == "MultiLineString":
        lines = [ln for ln in coords if ln]
        if not lines:
            return None
        return midpoint_line(max(lines, key=line_length))
    return None


def feature_id(feature, idx):
    p = feature.get("properties") or {}
    for key in ("OBJECTID_1", "OBJECTID", "COTRECHO", "id"):
        v = p.get(key)
        if v is not None:
            return str(v)
    return str(idx)


def coord_name(ds, candidates, label):
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    raise RuntimeError(f"Não foi possível detectar {label}. Coordenadas: {list(ds.coords)}")


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
    raise RuntimeError(f"Não foi possível detectar a descarga. Variáveis: {list(ds.data_vars)}")


def open_discharge(path):
    ds = xr.open_dataset(path)
    lon = coord_name(ds, ["longitude", "lon", "x"], "longitude")
    lat = coord_name(ds, ["latitude", "lat", "y"], "latitude")
    var = data_var(ds)
    da = ds[var].squeeze(drop=True)
    # Se houver dimensão temporal residual com tamanho >1, fica apenas a primeira.
    for tname in ("valid_time", "time", "date"):
        if tname in da.dims:
            da = da.isel({tname: 0}).squeeze(drop=True)
    return ds, da, lon, lat, var


def visual_index(q):
    if not np.isfinite(q) or q < 0:
        return None
    # Escala fixa: 0 m3/s -> 0; 100.000 m3/s -> 100.
    return round(float(np.clip(np.log10(q + 1.0) / 5.0 * 100.0, 0, 100)), 2)


def main():
    if not RIVERS.exists():
        raise SystemExit("Falta docs/data/rivers.geojson. Execute primeiro BAIXAR_DADOS_REAIS.cmd")
    fc = json.loads(RIVERS.read_text(encoding="utf-8"))
    features = fc.get("features") or []
    ids, lons, lats = [], [], []
    for i, f in enumerate(features):
        pt = representative_point(f.get("geometry"))
        if pt is None:
            continue
        ids.append(feature_id(f, i))
        lons.append(pt[0]); lats.append(pt[1])
    if not ids:
        raise SystemExit("A rede PIN MS não contém geometrias lineares utilizáveis.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rede PIN MS: {len(ids):,} trechos com ponto representativo")

    for date_str in DATES:
        src = GLOFAS_DIR / f"glofas_ms_{date_str}.nc"
        if not src.exists():
            print(f"[faltando] {src.name}")
            continue
        ds, da, lon_name, lat_name, var_name = open_discharge(src)
        try:
            points = xr.DataArray(np.arange(len(ids)), dims="points")
            sampled = da.sel({
                lon_name: xr.DataArray(np.asarray(lons), dims="points", coords={"points": points}),
                lat_name: xr.DataArray(np.asarray(lats), dims="points", coords={"points": points}),
            }, method="nearest")
            values = np.asarray(sampled.values, dtype=float).reshape(-1)
        finally:
            ds.close()

        segments = {}
        physical = []
        for rid, q in zip(ids, values):
            if not np.isfinite(q) or q < 0:
                continue
            qf = float(q)
            physical.append(qf)
            segments[rid] = {
                "discharge_m3s": round(qf, 3),
                "discharge_index": visual_index(qf),
                "temperature_c": None,
            }
        arr = np.asarray(physical, dtype=float)
        summary = {
            "segments_with_discharge": int(arr.size),
            "discharge_median_m3s": round(float(np.median(arr)), 3) if arr.size else None,
            "discharge_p05_m3s": round(float(np.percentile(arr, 5)), 3) if arr.size else None,
            "discharge_p95_m3s": round(float(np.percentile(arr, 95)), 3) if arr.size else None,
        }
        payload = {
            "date": date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "segments": segments,
            "summary": summary,
            "sources": {
                "geometry": "PIN MS / IMASUL — Hidrografia",
                "discharge": "GloFAS Historical v4 / LISFLOOD — average daily discharge",
                "temperature": None,
            },
            "method": "nearest GloFAS grid cell sampled at a representative point of each PIN MS river segment",
            "note": "Associação cartográfica preliminar. Descarga GloFAS é modelada, não medição in situ. O índice 0–100 serve apenas para espessura visual e usa escala logarítmica fixa.",
        }
        out = OUT_DIR / f"{date_str}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"[ok] {out.name}: {len(segments):,} trechos; variável NetCDF={var_name}")

    print("\nArquivos temporais de teste concluídos. Na PWA selecione uma das quatro datas e clique em REAL.")


if __name__ == "__main__":
    main()
