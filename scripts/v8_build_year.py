#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import xarray as xr

from v8_common import (
    ARCHIVE_DIR, YEAR_DIR, coord_name, data_var, time_name,
    date_strings, discharge_day_strings, ensure_dirs, expected_dates, gap_paths, load_network, rebuild_index,
    summary_for_row, unavailable_dates, validate_year_bundle, valid_days_in_year,
)


def sample_file(path: Path, ids: list[str], lons: np.ndarray, lats: np.ndarray, year: int) -> tuple[list[str], np.ndarray]:
    with xr.open_dataset(path) as ds:
        lon_name = coord_name(ds, ('longitude', 'lon', 'x'), 'longitude')
        lat_name = coord_name(ds, ('latitude', 'lat', 'y'), 'latitude')
        tname = time_name(ds)
        var = data_var(ds)
        da = ds[var]
        for dim in list(da.dims):
            if dim not in (lon_name, lat_name, tname) and da.sizes.get(dim, 0) == 1:
                da = da.isel({dim: 0}, drop=True)
        sampled = da.sel({
            lon_name: xr.DataArray(lons, dims='points'),
            lat_name: xr.DataArray(lats, dims='points'),
        }, method='nearest')
        if tname not in sampled.dims:
            raise RuntimeError(f'dimensão temporal {tname} desapareceu após amostragem; dims={sampled.dims}')
        sampled = sampled.transpose(tname, 'points')
        dates = discharge_day_strings(sampled[tname].values)
        values = np.asarray(sampled.values, dtype=np.float32)

    mask = np.asarray([d.startswith(f'{year:04d}-') for d in dates], dtype=bool)
    dates = [d for d, keep in zip(dates, mask) if keep]
    values = values[mask]
    if values.shape[1] != len(ids):
        raise RuntimeError(f'número de segmentos incompatível: dados={values.shape[1]} rede={len(ids)}')
    values = np.where(np.isfinite(values) & (values >= 0), values, np.nan).astype('<f4', copy=False)
    return dates, values


def sample_year(path: Path, year: int) -> tuple[list[str], np.ndarray]:
    ids, lons, lats = load_network()
    all_dates: list[str] = []
    all_rows: list[np.ndarray] = []

    for src in [path, *gap_paths(year)]:
        dates, values = sample_file(src, ids, lons, lats, year)
        for d, row in zip(dates, values):
            all_dates.append(d)
            all_rows.append(row)

    # Deduplica por data. Reparos individuais têm prioridade sobre o arquivo anual.
    by_date: dict[str, np.ndarray] = {}
    for d, row in zip(all_dates, all_rows):
        by_date[d] = row
    dates = sorted(by_date)
    values = np.stack([by_date[d] for d in dates], axis=0).astype('<f4', copy=False)

    unavailable = set(unavailable_dates(year))
    expected = [d for d in expected_dates(year) if d not in unavailable]
    missing = sorted(set(expected) - set(dates))
    extra = sorted(set(dates) - set(expected_dates(year)))
    if missing:
        raise RuntimeError(f'ano {year} incompleto depois de combinar arquivo-base e reparos: faltam {", ".join(missing[:5])}')
    if extra:
        keep = [i for i, d in enumerate(dates) if d in set(expected_dates(year))]
        dates = [dates[i] for i in keep]
        values = values[keep]
    return dates, values


def build_year(year: int, force: bool = False) -> None:
    ensure_dirs()
    src = YEAR_DIR / f'glofas_ms_v4_{year}.nc'
    ok, detail = validate_year_bundle(src, year, strict=True)
    if not ok:
        raise FileNotFoundError(f'{src} inválido/ausente: {detail}')
    ids, _, _ = load_network()
    dates, values = sample_year(src, year)
    print(f'[processando] {year}: {len(dates)} dias × {len(ids):,} segmentos')

    out_year = ARCHIVE_DIR / str(year)
    out_year.mkdir(parents=True, exist_ok=True)
    months = sorted(set(d[:7] for d in dates))
    for month in months:
        sel = [i for i, d in enumerate(dates) if d.startswith(month + '-')]
        md = [dates[i] for i in sel]
        arr = values[sel].astype('<f4', copy=False)
        bin_path = out_year / f'{month}.f32'
        meta_path = out_year / f'{month}.json'
        if not force and bin_path.exists() and meta_path.exists():
            try:
                old = json.loads(meta_path.read_text(encoding='utf-8'))
                expected = len(md) * len(ids) * 4
                if old.get('format') == 'pulso-v8-f32' and old.get('dates') == md and bin_path.stat().st_size == expected:
                    print(f'  [já existe] {month}')
                    continue
            except Exception:
                pass

        tmp = bin_path.with_suffix('.tmp')
        arr.tofile(tmp)
        tmp.replace(bin_path)
        summaries = [summary_for_row(row) for row in arr]
        meta = {
            'format': 'pulso-v8-f32',
            'version': '0.8.3',
            'month': month,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'network': 'glofas_lisflood_v4',
            'system_version': 'version_4_0',
            'segment_count': len(ids),
            'day_count': len(md),
            'dates': md,
            'unavailable_dates': [d for d in unavailable_dates(year) if d.startswith(month + '-')],
            'binary_file': bin_path.name,
            'binary_dtype': 'float32-little-endian',
            'binary_shape': [len(md), len(ids)],
            'summaries': summaries,
            'sources': {
                'dynamic_network': 'CEMS GloFAS v4 / LISFLOOD — upstream area + LDD',
                'discharge': 'GloFAS Historical v4 — average daily river discharge',
                'context_geometry': 'PIN MS / IMASUL — Hidrografia',
            },
            'note': 'Descarga modelada, não medida in situ. V8.3 usa o dia hidrológico correto: valid_time do dis24 é o fim da média de 24 h, portanto a data visível é valid_time - 1 dia. Reparos diários ficam reservados para ausências reais.',
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'  [ok] {month}: {len(md)} dias · {bin_path.stat().st_size/1024:.0f} KB')

    idx = rebuild_index()
    print(f'[índice] {idx["date_count"]:,} datas · {idx["month_count"]} meses disponíveis')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    try:
        build_year(args.year, args.force)
        return 0
    except Exception as exc:
        print(f'ERRO ao processar {args.year}: {exc}', file=sys.stderr)
        return 4


if __name__ == '__main__':
    raise SystemExit(main())
