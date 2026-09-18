#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / 'data' / 'raw' / 'dynqual'
RAW_FILE = RAW_DIR / 'waterTemperature_monthly_1980_2019_30min.nc'
RIVERS_FILE = ROOT / 'docs' / 'data' / 'rivers.geojson'
OUT_FILE = ROOT / 'docs' / 'data' / 'temperature-climatology.json'
URL = 'https://zenodo.org/records/10155484/files/waterTemperature_monthly_1980_2019_30min.nc?download=1'


def fail(msg: str, code: int = 1):
    print(f'\nERRO: {msg}')
    raise SystemExit(code)


def download(url: str, target: Path):
    import requests
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 50_000_000:
        print(f'[já existe] {target} ({target.stat().st_size/1024/1024:.1f} MB)')
        return
    tmp = target.with_suffix(target.suffix + '.part')
    print('[baixando] DynQual · temperatura mensal 1980–2019 · 0,5°')
    print(f'URL: {url}')
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length') or 0)
        done = 0
        with tmp.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f'  {done/1024/1024:6.1f} / {total/1024/1024:6.1f} MB', end='\r', flush=True)
    tmp.replace(target)
    print(f'\n[ok] {target} ({target.stat().st_size/1024/1024:.1f} MB)')


def flatten_coords(geom):
    if not geom:
        return []
    t = geom.get('type')
    c = geom.get('coordinates')
    if t == 'LineString':
        return c or []
    if t == 'MultiLineString':
        return [pt for line in (c or []) for pt in line]
    if t == 'Polygon':
        return [pt for ring in (c or []) for pt in ring]
    if t == 'MultiPolygon':
        return [pt for poly in (c or []) for ring in poly for pt in ring]
    return []


def anchor(feature):
    pts = [p for p in flatten_coords(feature.get('geometry')) if isinstance(p, list) and len(p) >= 2]
    if not pts:
        return None
    xs = [float(p[0]) for p in pts if math.isfinite(float(p[0])) and math.isfinite(float(p[1]))]
    ys = [float(p[1]) for p in pts if math.isfinite(float(p[0])) and math.isfinite(float(p[1]))]
    if not xs:
        return None
    return sum(xs)/len(xs), sum(ys)/len(ys)


def pick_coord_var(ds, names):
    lowered = {k.lower(): k for k in ds.variables}
    for n in names:
        if n.lower() in lowered:
            return ds.variables[lowered[n.lower()]]
    for k, v in ds.variables.items():
        text = f'{k} {getattr(v, "standard_name", "")} {getattr(v, "long_name", "")}'.lower()
        if any(n.lower() in text for n in names):
            return v
    return None


def pick_temp_var(ds, time_dim, lat_dim, lon_dim):
    best = []
    for k, v in ds.variables.items():
        dims = set(v.dimensions)
        if not {time_dim, lat_dim, lon_dim}.issubset(dims):
            continue
        text = f'{k} {getattr(v, "standard_name", "")} {getattr(v, "long_name", "")} {getattr(v, "units", "")}'.lower()
        score = (5 if 'temperature' in text else 0) + (3 if 'water' in text else 0) + (1 if 'k' in text or 'kelvin' in text else 0)
        best.append((score, k, v))
    if not best:
        return None
    best.sort(key=lambda x: x[0], reverse=True)
    return best[0][2]


def nearest_index(values, target):
    import numpy as np
    arr = np.asarray(values, dtype=float)
    return int(np.nanargmin(np.abs(arr - target)))


def to_float_list(arr):
    import numpy as np
    a = np.ma.asarray(arr)
    if np.ma.isMaskedArray(a):
        a = a.filled(np.nan)
    return np.asarray(a, dtype=float)


def percentile(vals, q):
    import numpy as np
    a = np.asarray([v for v in vals if v is not None and math.isfinite(v)], dtype=float)
    if a.size == 0:
        return None
    return float(np.nanpercentile(a, q))


def process(nc_path: Path, rivers_path: Path, out_path: Path):
    import numpy as np
    from netCDF4 import Dataset, num2date

    if not rivers_path.exists():
        fail(f'arquivo não encontrado: {rivers_path}\nBaixe primeiro a hidrografia real PIN MS / IMASUL.')
    rivers = json.loads(rivers_path.read_text(encoding='utf-8'))
    feats = rivers.get('features') or []
    if not feats:
        fail('rivers.geojson não contém feições.')

    print(f'[rios] {len(feats):,} segmentos PIN MS / IMASUL')
    with Dataset(nc_path, 'r') as ds:
        latv = pick_coord_var(ds, ['lat', 'latitude'])
        lonv = pick_coord_var(ds, ['lon', 'longitude'])
        timev = pick_coord_var(ds, ['time'])
        if latv is None or lonv is None or timev is None:
            fail('não foi possível identificar latitude, longitude e tempo no NetCDF.')
        if len(latv.dimensions) != 1 or len(lonv.dimensions) != 1:
            fail('esta versão espera coordenadas latitude/longitude unidimensionais.')
        lat_dim, lon_dim, time_dim = latv.dimensions[0], lonv.dimensions[0], timev.dimensions[0]
        tempv = pick_temp_var(ds, time_dim, lat_dim, lon_dim)
        if tempv is None:
            fail('não foi possível identificar a variável de temperatura da água.')
        print(f'[netcdf] variável: {tempv.name} · unidades: {getattr(tempv, "units", "?")} · dimensões: {tempv.dimensions}')

        lats = to_float_list(latv[:]); lons = to_float_list(lonv[:])
        lon360 = np.nanmax(lons) > 180
        units = getattr(timev, 'units', None); cal = getattr(timev, 'calendar', 'standard')
        if units:
            dates = list(num2date(timev[:], units=units, calendar=cal, only_use_cftime_datetimes=False, only_use_python_datetimes=False))
            month_of_time = [int(d.month) for d in dates]
        else:
            ntime = len(timev[:])
            month_of_time = [(i % 12) + 1 for i in range(ntime)]
            print('[aviso] tempo sem unidades CF; assumindo sequência mensal iniciada em janeiro.')

        dim_pos = {d: i for i, d in enumerate(tempv.dimensions)}
        tpos, ypos, xpos = dim_pos[time_dim], dim_pos[lat_dim], dim_pos[lon_dim]
        anchors = [anchor(f) for f in feats]
        cell_for_feature = []
        for a in anchors:
            if a is None:
                cell_for_feature.append(None); continue
            lon, lat = a
            qlon = lon + 360 if lon360 and lon < 0 else lon
            yi = nearest_index(lats, lat); xi = nearest_index(lons, qlon)
            cell_for_feature.append((yi, xi))
        unique_cells = sorted({c for c in cell_for_feature if c is not None})
        print(f'[grade] {len(unique_cells):,} células DynQual únicas usadas para MS')

        clim = {}
        raw_units = str(getattr(tempv, 'units', '')).lower()
        for ci, (yi, xi) in enumerate(unique_cells, 1):
            key = [0] * tempv.ndim
            key[tpos] = slice(None); key[ypos] = yi; key[xpos] = xi
            series = to_float_list(tempv[tuple(key)]).reshape(-1)
            good = series[np.isfinite(series)]
            convert_k = ('kelvin' in raw_units) or raw_units.strip() in {'k', 'degk'} or (good.size and float(np.nanmedian(good)) > 100)
            if convert_k:
                series = series - 273.15
            vals = []
            for m in range(1, 13):
                idx = np.asarray([i for i, mm in enumerate(month_of_time) if mm == m], dtype=int)
                x = series[idx] if idx.size else np.asarray([], dtype=float)
                x = x[np.isfinite(x)]
                vals.append(float(np.nanmean(x)) if x.size else None)
            clim[(yi, xi)] = vals
            if ci % 25 == 0 or ci == len(unique_cells):
                print(f'  células processadas: {ci}/{len(unique_cells)}', end='\r', flush=True)
        print()

    months = {f'{m:02d}': [] for m in range(1,13)}
    for c in cell_for_feature:
        vals = clim.get(c) if c is not None else None
        for m in range(1,13):
            v = vals[m-1] if vals else None
            months[f'{m:02d}'].append(None if v is None or not math.isfinite(v) else round(float(v), 2))

    summary = {}
    for m in range(1,13):
        vals = months[f'{m:02d}']
        finite = [v for v in vals if v is not None and math.isfinite(v)]
        summary[f'{m:02d}'] = {
            'mean_c': round(sum(finite)/len(finite), 2) if finite else None,
            'median_c': round(percentile(finite, 50), 2) if finite else None,
            'p10_c': round(percentile(finite, 10), 2) if finite else None,
            'p90_c': round(percentile(finite, 90), 2) if finite else None,
            'segments': len(finite),
        }

    payload = {
        'format': 'dynqual-climatology-ms-v1',
        'variable': 'surface water temperature',
        'units': 'degC',
        'temporal_character': 'monthly climatology',
        'source_period': '1980-2019',
        'source_resolution': '0.5 degree (~50 km)',
        'source_dataset': 'DynQual v1.0 aggregated to 0.5 degree',
        'source_doi': '10.5281/zenodo.10155484',
        'source_file': 'waterTemperature_monthly_1980_2019_30min.nc',
        'river_geometry': 'PIN MS / IMASUL',
        'mapping': 'nearest DynQual grid cell to river-segment coordinate centroid; cartographic visualization only',
        'feature_count': len(feats),
        'months': months,
        'summary': summary,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'[ok] {out_path} ({out_path.stat().st_size/1024/1024:.2f} MB)')
    print('\nTemperatura pronta. Recarregue a PWA com Ctrl + Shift + R.')


def main():
    ap = argparse.ArgumentParser(description='Baixa e prepara a climatologia mensal DynQual para Pulso Hídrico MS.')
    ap.add_argument('--file', type=Path, default=RAW_FILE, help='NetCDF local alternativo')
    ap.add_argument('--no-download', action='store_true')
    args = ap.parse_args()
    if not args.file.exists():
        if args.no_download:
            fail(f'arquivo não encontrado: {args.file}')
        download(URL, args.file)
    process(args.file, RIVERS_FILE, OUT_FILE)


if __name__ == '__main__':
    main()
