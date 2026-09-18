"""
07 - Genera docs/data/pulse/YYYY-MM-DD.json para la PWA.

Descarga: GloFAS Historical del día seleccionado.
Temperatura: climatología mensual DynQual 1980-2019. No se presenta como una
observación diaria de 2025/2026.

La unión GloFAS↔HydroRIVERS se hace por muestreo de la celda de grilla más
próxima a un punto representativo del segmento. Es una aproximación cartográfica,
no enrutamiento hidrológico ni validación contra estaciones.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import xarray as xr

BASE = Path(__file__).resolve().parent.parent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--rivers", type=Path, default=BASE / "data" / "processed" / "rivers_ms.gpkg")
    p.add_argument("--glofas", type=Path, default=None, help="NetCDF GloFAS. Por defecto usa data/processed/glofas/glofas_ms_FECHA.nc")
    p.add_argument("--temperature", type=Path, default=BASE / "data" / "processed" / "water_temp_ms.nc")
    p.add_argument("--out", type=Path, default=BASE / "docs" / "data" / "pulse")
    p.add_argument("--discharge-var", default=None)
    p.add_argument("--temperature-var", default=None)
    p.add_argument("--min-order", type=int, default=2)
    return p.parse_args()


def pick_coord(ds, candidates, label):
    for c in candidates:
        if c in ds.coords or c in ds.dims:
            return c
    raise SystemExit(f"No pude detectar {label}. Coordenadas: {list(ds.coords)}")


def pick_var(ds, explicit, hints, label):
    if explicit:
        if explicit not in ds.data_vars:
            raise SystemExit(f"No existe {explicit}. Variables: {list(ds.data_vars)}")
        return explicit
    for v in ds.data_vars:
        low = v.lower()
        if any(h in low for h in hints):
            return v
    if len(ds.data_vars) == 1:
        return list(ds.data_vars)[0]
    raise SystemExit(f"No pude detectar variable de {label}. Variables: {list(ds.data_vars)}")


def sample_2d(da, lon, lat, lons, lats):
    pts = xr.DataArray(np.arange(len(lons)), dims="points")
    out = da.sel({
        lon: xr.DataArray(lons, dims="points", coords={"points": pts}),
        lat: xr.DataArray(lats, dims="points", coords={"points": pts}),
    }, method="nearest")
    return np.asarray(out.values, dtype=float).reshape(-1)


def prepare_discharge(path, date_str, lons, lats, explicit_var=None):
    ds = xr.open_dataset(path)
    lon = pick_coord(ds, ["longitude", "lon", "x"], "longitud GloFAS")
    lat = pick_coord(ds, ["latitude", "lat", "y"], "latitud GloFAS")
    var = pick_var(ds, explicit_var, ["dis", "discharge", "river_discharge"], "descarga")
    da = ds[var]
    time = next((c for c in ["valid_time", "time", "date"] if c in da.coords or c in da.dims), None)
    if time:
        da = da.sel({time: np.datetime64(date_str)}, method="nearest")
    da = da.squeeze(drop=True)
    return sample_2d(da, lon, lat, lons, lats)


def prepare_temp_climatology(path, date_str, lons, lats, explicit_var=None):
    if not path.exists():
        return np.full(len(lons), np.nan), None
    ds = xr.open_dataset(path)
    lon = pick_coord(ds, ["longitude", "lon", "x"], "longitud DynQual")
    lat = pick_coord(ds, ["latitude", "lat", "y"], "latitud DynQual")
    var = pick_var(ds, explicit_var, ["watertemperature", "water_temperature", "watertemp", "temperature", "temp"], "temperatura")
    da = ds[var]
    target_month = int(date_str[5:7])
    time = next((c for c in ["time", "date"] if c in da.coords or c in da.dims), None)
    if time:
        try:
            da = da.where(da[time].dt.month == target_month, drop=True).mean(time, skipna=True)
        except Exception:
            da = da.sel({time: da[time][target_month - 1]}).squeeze(drop=True)
    elif "month" in da.coords or "month" in da.dims:
        month_coord = da["month"]
        vals = np.asarray(month_coord.values)
        # admite 1..12 o 0..11
        key = target_month if target_month in vals else target_month - 1
        da = da.sel(month=key)
    da = da.squeeze(drop=True)
    vals = sample_2d(da, lon, lat, lons, lats)

    units = str(da.attrs.get("units", "")).lower()
    finite = vals[np.isfinite(vals)]
    # DynQual reciente documenta K; versiones antiguas pueden estar en °C.
    if "k" == units.strip() or "kelvin" in units or (finite.size and np.nanmedian(finite) > 100):
        vals = vals - 273.15
    return vals, f"DynQual climatologia mensal 1980-2019, mês {target_month:02d}"


def finite_range(values):
    v = values[np.isfinite(values)]
    if not v.size:
        return None
    return [float(np.nanpercentile(v, 2)), float(np.nanpercentile(v, 98))]


def main():
    args = parse_args()
    glofas = args.glofas or (BASE / "data" / "processed" / "glofas" / f"glofas_ms_{args.date}.nc")
    if not args.rivers.exists():
        raise SystemExit(f"Falta {args.rivers}. Ejecuta 00_bootstrap_ms_geometry.py")
    if not glofas.exists():
        raise SystemExit(f"Falta {glofas}. Ejecuta: python scripts/03_download_glofas.py --date {args.date}")

    rivers = gpd.read_file(args.rivers).to_crs(4326)
    order_col = next((c for c in ["ORD_STRA", "ord_stra"] if c in rivers.columns), None)
    if order_col:
        rivers = rivers[rivers[order_col].fillna(0).astype(float) >= args.min_order].copy()
    id_col = next((c for c in ["HYRIV_ID", "hyriv_id", "id"] if c in rivers.columns), None)
    if not id_col:
        raise SystemExit("HydroRIVERS necesita HYRIV_ID para enlazar con la PWA.")

    pts = rivers.geometry.representative_point()
    lons = pts.x.to_numpy(float)
    lats = pts.y.to_numpy(float)
    q = prepare_discharge(glofas, args.date, lons, lats, args.discharge_var)
    t, temp_source = prepare_temp_climatology(args.temperature, args.date, lons, lats, args.temperature_var)

    segments = {}
    for rid, qv, tv in zip(rivers[id_col].astype(str), q, t):
        q_out = None if not math.isfinite(float(qv)) else round(float(qv), 3)
        t_out = None if not math.isfinite(float(tv)) else round(float(tv), 3)
        if q_out is not None or t_out is not None:
            segments[str(rid)] = [q_out, t_out]

    tf = t[np.isfinite(t)]
    payload = {
        "date": args.date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            # No se suman todos los segmentos: eso contaría varias veces el mismo caudal aguas abajo.
            "discharge_total_m3s": None,
            "temperature_mean_c": round(float(np.mean(tf)), 2) if tf.size else None,
            "discharge_range_m3s": finite_range(q),
            "temperature_range_c": finite_range(t),
            "segments_with_values": len(segments),
        },
        "segments": segments,
        "sources": {
            "discharge": "GloFAS Historical v4",
            "temperature": temp_source,
        },
        "method": "nearest-grid sampling at one representative point per HydroRIVERS segment",
        "note": "Descarga GloFAS por segmento; temperatura = climatologia mensal DynQual 1980-2019. Amostragem de grade para visualização exploratória; não equivale a observação in situ nem a roteamento hidrológico.",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / f"{args.date}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Guardado {out} con {len(segments)} segmentos.")


if __name__ == "__main__":
    main()
