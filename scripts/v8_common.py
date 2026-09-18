from __future__ import annotations

from pathlib import Path
import calendar
from datetime import date, timedelta
import json
import os
from typing import Iterable

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
YEAR_DIR = ROOT / 'data' / 'processed' / 'glofas_v8_yearly'
GAP_DIR = YEAR_DIR / '_gaps'
ARCHIVE_DIR = ROOT / 'docs' / 'data' / 'pulse-v8'
NETWORK = ROOT / 'docs' / 'data' / 'glofas_network.geojson'
PROGRESS = ROOT / 'data' / 'processed' / 'glofas_v8_progress.json'
UNAVAILABLE = ROOT / 'data' / 'processed' / 'glofas_v8_unavailable.json'

DATASET = 'cems-glofas-historical'
AREA_MS = [-16.85, -58.40, -24.35, -50.55]  # N, W, S, E
START_YEAR = 2001
END_YEAR = 2025


def ensure_dirs() -> None:
    YEAR_DIR.mkdir(parents=True, exist_ok=True)
    GAP_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)


def base_request() -> dict:
    return {
        'system_version': ['version_4_0'],
        'product_type': ['consolidated'],
        'hydrological_model': ['lisflood'],
        'variable': ['average_river_discharge_in_the_last_24_hours'],
        'timespan': ['time_mean'],
        'area': AREA_MS,
        'data_format': 'netcdf',
        'download_format': 'unarchived',
    }


def year_request(year: int) -> dict:
    req = base_request()
    req.update({
        'year': [str(year)],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'day': [f'{d:02d}' for d in range(1, 32)],
    })
    return req


def day_request(day_iso: str) -> dict:
    y, m, d = day_iso.split('-')
    req = base_request()
    req.update({'year': [y], 'month': [m], 'day': [d]})
    return req



def load_unavailable() -> dict:
    if UNAVAILABLE.exists():
        try:
            data = json.loads(UNAVAILABLE.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {'dates': {}}


def save_unavailable(data: dict) -> None:
    ensure_dirs()
    tmp = UNAVAILABLE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, UNAVAILABLE)


def mark_unavailable(day_iso: str, reason: str) -> None:
    data = load_unavailable()
    data.setdefault('dates', {})[day_iso] = {
        'reason': str(reason),
        'recorded_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
    }
    save_unavailable(data)


def unavailable_dates(year: int | None = None) -> list[str]:
    dates = sorted((load_unavailable().get('dates') or {}).keys())
    if year is None:
        return dates
    prefix = f'{year:04d}-'
    return [d for d in dates if d.startswith(prefix)]


def coord_name(ds: xr.Dataset, candidates: Iterable[str], label: str) -> str:
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    raise RuntimeError(f'não foi possível detectar {label}; coords={list(ds.coords)} dims={list(ds.dims)}')


def time_name(ds: xr.Dataset) -> str:
    for name in ('valid_time', 'time', 'date'):
        if name in ds.coords or name in ds.dims:
            return name
    for name in ds.coords:
        arr = ds[name]
        if np.issubdtype(arr.dtype, np.datetime64):
            return name
    raise RuntimeError(f'não foi possível detectar tempo; coords={list(ds.coords)}')


def data_var(ds: xr.Dataset) -> str:
    preferred = [
        'dis24', 'discharge', 'river_discharge',
        'average_river_discharge_in_the_last_24_hours',
    ]
    for name in preferred:
        if name in ds.data_vars:
            return name
    for name in ds.data_vars:
        low = name.lower()
        if 'dis' in low or 'river' in low:
            return name
    if len(ds.data_vars) == 1:
        return list(ds.data_vars)[0]
    raise RuntimeError(f'descarga não detectada; vars={list(ds.data_vars)}')


def load_network() -> tuple[list[str], np.ndarray, np.ndarray]:
    if not NETWORK.exists():
        raise FileNotFoundError('Falta docs/data/glofas_network.geojson. Execute PREPARAR_V7_GLOFAS.cmd primeiro.')
    fc = json.loads(NETWORK.read_text(encoding='utf-8'))
    feats = fc.get('features') or []
    if not feats:
        raise RuntimeError('Rede GloFAS vazia.')
    ids = [str(f['properties']['glofas_id']) for f in feats]
    lons = np.asarray([f['properties']['glofas_lon'] for f in feats], dtype=float)
    lats = np.asarray([f['properties']['glofas_lat'] for f in feats], dtype=float)
    return ids, lons, lats


def date_strings(values: np.ndarray) -> list[str]:
    """Return raw NetCDF valid-time dates (end of model averaging period)."""
    out: list[str] = []
    for v in np.asarray(values).reshape(-1):
        try:
            out.append(np.datetime_as_string(np.datetime64(v), unit='D'))
        except Exception:
            out.append(str(v)[:10])
    return out


def discharge_day_strings(values: np.ndarray) -> list[str]:
    """Map GloFAS dis24 valid_time to the calendar day represented.

    GloFAS average_river_discharge_in_the_last_24_hours is a 24-hour mean and
    its timestamp is the END of the averaging period. Consequently a request
    for calendar day 2001-01-01 is commonly returned with valid_time
    2001-01-02 00:00. For Pulso Hídrico the visible date is the day covered by
    the mean, so we subtract one day from valid_time.
    """
    out: list[str] = []
    for v in np.asarray(values).reshape(-1):
        try:
            dt = np.datetime64(v, 'D') - np.timedelta64(1, 'D')
            out.append(np.datetime_as_string(dt, unit='D'))
        except Exception:
            raw = str(v)[:10]
            try:
                y, m, d = map(int, raw.split('-'))
                out.append((date(y, m, d) - timedelta(days=1)).isoformat())
            except Exception:
                out.append(raw)
    return out


def valid_days_in_year(year: int) -> int:
    return 366 if calendar.isleap(year) else 365


def expected_dates(year: int) -> list[str]:
    cur = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    out: list[str] = []
    while cur < end:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out


def dates_in_file(path: Path, year: int) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with xr.open_dataset(path) as ds:
        tname = time_name(ds)
        return sorted(set(d for d in discharge_day_strings(ds[tname].values) if d.startswith(f'{year:04d}-')))




def validate_gap_file(path: Path, day_iso: str) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size == 0:
        return False, 'arquivo ausente ou vazio'
    try:
        year = int(day_iso[:4])
        with xr.open_dataset(path) as ds:
            tname = time_name(ds)
            raw_dates = date_strings(ds[tname].values)
            dates = discharge_day_strings(ds[tname].values)
            if day_iso not in dates:
                return False, f'dia hidrológico {day_iso} não encontrado; valid_time={raw_dates[:5]} -> dias={dates[:5]}'
            data_var(ds)
            coord_name(ds, ('longitude', 'lon', 'x'), 'longitude')
            coord_name(ds, ('latitude', 'lat', 'y'), 'latitude')
        return True, day_iso
    except Exception as exc:
        return False, str(exc)

def gap_paths(year: int) -> list[Path]:
    folder = GAP_DIR / str(year)
    if not folder.exists():
        return []
    return sorted(folder.glob('*.nc'))


def bundle_dates(path: Path, year: int) -> list[str]:
    found = set(dates_in_file(path, year))
    for p in gap_paths(year):
        try:
            found.update(dates_in_file(p, year))
        except Exception:
            pass
    return sorted(found)


def missing_dates(path: Path, year: int, include_unavailable: bool = False) -> list[str]:
    miss = set(expected_dates(year)) - set(bundle_dates(path, year))
    if not include_unavailable:
        miss -= set(unavailable_dates(year))
    return sorted(miss)


def validate_year_file(path: Path, year: int, strict: bool = False) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size < 1024:
        return False, 'arquivo ausente ou muito pequeno'
    try:
        with xr.open_dataset(path) as ds:
            tname = time_name(ds)
            raw_dates = date_strings(ds[tname].values)
            dates = discharge_day_strings(ds[tname].values)
            in_year = sorted(set(d for d in dates if d.startswith(f'{year:04d}-')))
            minimum = valid_days_in_year(year) if strict else 300
            if len(in_year) < minimum:
                return False, f'apenas {len(in_year)} datas do ano {year}'
            data_var(ds)
            coord_name(ds, ('longitude', 'lon', 'x'), 'longitude')
            coord_name(ds, ('latitude', 'lat', 'y'), 'latitude')
        return True, f'{len(in_year)} dias'
    except Exception as exc:
        return False, str(exc)


def validate_year_bundle(path: Path, year: int, strict: bool = True) -> tuple[bool, str]:
    # Valida o arquivo-base estruturalmente sem exigir 365/366 dias nele sozinho.
    ok, detail = validate_year_file(path, year, strict=False)
    if not ok:
        return False, detail
    dates = bundle_dates(path, year)
    unavailable = set(unavailable_dates(year))
    expected = set(expected_dates(year)) - unavailable
    missing = sorted(expected - set(dates))
    extra = sorted(set(dates) - set(expected_dates(year)))
    if strict and missing:
        preview = ', '.join(missing[:5])
        suffix = '' if len(missing) <= 5 else f' (+{len(missing)-5})'
        return False, f'{len(dates)}/{len(expected_dates(year))} dias; faltam {preview}{suffix}'
    msg = f'{len(dates)} dias'
    if unavailable:
        msg += f' + {len(unavailable)} indisponível(is) documentado(s)'
    if extra:
        msg += f' · {len(extra)} extra ignorado(s)'
    return True, msg


def summary_for_row(row: np.ndarray) -> dict:
    vals = np.asarray(row, dtype=float)
    ok = np.isfinite(vals) & (vals >= 0)
    vals = vals[ok]
    if vals.size == 0:
        return {
            'segments_with_discharge': 0,
            'segments_positive': 0,
            'zero_fraction': None,
            'discharge_p50_m3s': None,
            'discharge_p90_m3s': None,
            'discharge_p95_m3s': None,
            'discharge_max_m3s': None,
        }
    return {
        'segments_with_discharge': int(vals.size),
        'segments_positive': int(np.sum(vals > 0)),
        'zero_fraction': round(float(np.mean(vals == 0)), 5),
        'discharge_p50_m3s': round(float(np.percentile(vals, 50)), 3),
        'discharge_p90_m3s': round(float(np.percentile(vals, 90)), 3),
        'discharge_p95_m3s': round(float(np.percentile(vals, 95)), 3),
        'discharge_max_m3s': round(float(np.max(vals)), 3),
    }


def rebuild_index() -> dict:
    ensure_dirs()
    months: dict[str, dict] = {}
    all_dates: list[str] = []
    for meta_path in sorted(ARCHIVE_DIR.glob('*/*.json')):
        try:
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if meta.get('format') != 'pulso-v8-f32' or not isinstance(meta.get('dates'), list):
            continue
        key = meta.get('month') or meta_path.stem
        dates = [str(d) for d in meta['dates']]
        months[key] = {
            'dates': dates,
            'count': len(dates),
            'segment_count': meta.get('segment_count'),
            'binary': f"{meta_path.parent.name}/{meta.get('binary_file', key + '.f32')}",
            'meta': f"{meta_path.parent.name}/{meta_path.name}",
        }
        all_dates.extend(dates)
    all_dates = sorted(set(all_dates))
    index = {
        'version': '0.8.3',
        'format': 'pulso-v8-f32',
        'network': 'glofas_lisflood_v4',
        'system_version': 'version_4_0',
        'period_target': [f'{START_YEAR}-01-01', f'{END_YEAR}-12-31'],
        'start': all_dates[0] if all_dates else None,
        'end': all_dates[-1] if all_dates else None,
        'date_count': len(all_dates),
        'month_count': len(months),
        'dates': all_dates,
        'unavailable_dates': unavailable_dates(),
        'target_date_count': sum(valid_days_in_year(y) for y in range(START_YEAR, END_YEAR + 1)),
        'months': months,
        'note': 'Float32 little-endian; matriz [dia, segmento] na mesma ordem de glofas_network.geojson. V8.3 interpreta valid_time de dis24 como fim da média de 24 h e o converte ao dia hidrológico (valid_time - 1 dia); mantém reparo automático para ausências reais.',
    }
    (ARCHIVE_DIR / 'index.json').write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return index


def load_progress() -> dict:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'years': {}}


def save_progress(data: dict) -> None:
    ensure_dirs()
    tmp = PROGRESS.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, PROGRESS)
