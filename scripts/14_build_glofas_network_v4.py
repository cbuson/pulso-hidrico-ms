#!/usr/bin/env python3
"""Constrói a rede cartográfica nativa GloFAS/LISFLOOD v4 em MS.

A rede é derivada diretamente dos pixels do modelo, não de uma associação por
vizinho mais próximo com a rede PIN. São mantidas células com área a montante
>= 250 km², em linha com o limiar cartográfico usado pelo GloFAS para produtos
em 0,05°.
"""
from __future__ import annotations

from pathlib import Path
import json
import math
import numpy as np
import xarray as xr
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "data" / "processed" / "glofas_static"
UP = STATIC / "uparea_ms_v4.nc"
LDD = STATIC / "ldd_ms_v4.nc"
BOUNDARY = ROOT / "docs" / "data" / "boundary.geojson"
OUT = ROOT / "docs" / "data" / "glofas_network.geojson"

THRESHOLD_KM2 = 250.0
THRESHOLD_M2 = THRESHOLD_KM2 * 1_000_000.0

# PCRaster LDD: códigos como teclado numérico; 5 = pit.
DIR = {
    1: (-1, -1), 2: (0, -1), 3: (1, -1),
    4: (-1,  0),                 6: (1,  0),
    7: (-1,  1), 8: (0,  1), 9: (1,  1),
}


def coord_name(ds, candidates):
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    raise RuntimeError(f"coordenada não encontrada; disponíveis: {list(ds.coords)}")


def data_var(ds, preferred):
    for name in preferred:
        if name in ds.data_vars:
            return name
    if len(ds.data_vars) == 1:
        return list(ds.data_vars)[0]
    raise RuntimeError(f"variável não encontrada; disponíveis: {list(ds.data_vars)}")


def load_boundary():
    if not BOUNDARY.exists():
        return None
    fc = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    geoms = [shape(f["geometry"]) for f in fc.get("features", []) if f.get("geometry")]
    if not geoms:
        return None
    # Pequena margem para não cortar rios que coincidem com fronteiras estaduais.
    return unary_union(geoms).buffer(0.06)


def gid(lon: float, lat: float) -> str:
    return f"g4_{lat:+08.3f}_{lon:+09.3f}"


def main() -> int:
    if not UP.exists() or not LDD.exists():
        raise SystemExit("Faltam mapas estáticos. Execute scripts/13_download_glofas_static_v4.py")

    with xr.open_dataset(UP) as du, xr.open_dataset(LDD) as dl:
        ulon = coord_name(du, ["longitude", "lon"])
        ulat = coord_name(du, ["latitude", "lat"])
        llon = coord_name(dl, ["longitude", "lon"])
        llat = coord_name(dl, ["latitude", "lat"])
        uvar = data_var(du, ["uparea"])
        lvar = data_var(dl, ["ldd"])

        up = du[uvar].values
        ldd = dl[lvar].values
        lons = np.asarray(du[ulon].values, dtype=float)
        lats = np.asarray(du[ulat].values, dtype=float)
        lons2 = np.asarray(dl[llon].values, dtype=float)
        lats2 = np.asarray(dl[llat].values, dtype=float)

    # Os recortes devem usar a mesma grade 0,05°. Reamostra LDD por índice se
    # houver apenas diferença de nome; aborta se a grade não for compatível.
    if up.shape != ldd.shape or len(lons) != len(lons2) or len(lats) != len(lats2):
        raise SystemExit(f"Grades incompatíveis: uparea={up.shape}, ldd={ldd.shape}")
    if not (np.allclose(lons, lons2, atol=1e-7) and np.allclose(lats, lats2, atol=1e-7)):
        raise SystemExit("Coordenadas uparea/LDD não coincidem após o recorte.")

    dlon = float(np.median(np.diff(lons)))
    dlat = float(np.median(np.diff(lats)))
    step_lon = abs(dlon)
    step_lat = abs(dlat)
    boundary = load_boundary()

    feats = []
    valid = np.isfinite(up) & (up >= THRESHOLD_M2)
    rows, cols = np.where(valid)
    for r, c in zip(rows.tolist(), cols.tolist()):
        lon = float(lons[c]); lat = float(lats[r])
        if boundary is not None and not boundary.covers(Point(lon, lat)):
            continue
        code = int(ldd[r, c])
        if code not in DIR:
            continue
        dx, dy = DIR[code]
        lon2 = lon + dx * step_lon
        lat2 = lat + dy * step_lat
        area_km2 = float(up[r, c]) / 1_000_000.0
        feats.append({
            "type": "Feature",
            "properties": {
                "glofas_id": gid(lon, lat),
                "glofas_lon": round(lon, 5),
                "glofas_lat": round(lat, 5),
                "upstream_area_km2": round(area_km2, 2),
                "ldd": code,
                "model": "GloFAS v4 / LISFLOOD",
            },
            "geometry": {"type": "LineString", "coordinates": [[lon, lat], [lon2, lat2]]},
        })

    fc = {
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {
            "source": "CEMS GloFAS v4 auxiliary data: upstream area + LDD",
            "threshold_upstream_area_km2": THRESHOLD_KM2,
            "method": "native LISFLOOD grid connections; no nearest-neighbour matching to PIN MS",
            "feature_count": len(feats),
        },
    }
    OUT.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"[ok] {OUT}: {len(feats):,} segmentos GloFAS nativos (>= {THRESHOLD_KM2:.0f} km²)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
