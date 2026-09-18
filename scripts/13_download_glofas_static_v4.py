#!/usr/bin/env python3
"""Baixa os mapas estáticos oficiais do GloFAS v4 usados pela rede LISFLOOD.

Arquivos oficiais CEMS/ECMWF:
- uparea_glofas_v4_0.nc  (área a montante)
- ldd_glofas_v4_0.nc     (Local Drain Direction)

Os arquivos completos são guardados em data/raw/glofas_static/.
Depois são recortados para MS + margem em data/processed/glofas_static/.
"""
from __future__ import annotations

from pathlib import Path
import sys
import requests
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "glofas_static"
PROC = ROOT / "data" / "processed" / "glofas_static"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

FILES = {
    "uparea_glofas_v4_0.nc": [
        "https://confluence.ecmwf.int/download/attachments/242067380/uparea_glofas_v4_0.nc?api=v2&modificationDate=1668604690076&version=2",
        "https://confluence.ecmwf.int/download/attachments/242067380/uparea_glofas_v4_0.nc",
    ],
    "ldd_glofas_v4_0.nc": [
        "https://confluence.ecmwf.int/download/attachments/242067380/ldd_glofas_v4_0.nc?api=v2&modificationDate=1669994937993&version=1",
        "https://confluence.ecmwf.int/download/attachments/242067380/ldd_glofas_v4_0.nc",
    ],
}

# MS + margem suficiente para preservar a conexão das células de fronteira.
NORTH, WEST, SOUTH, EAST = -16.65, -58.60, -24.55, -50.35
UA = "Pulso-Hidrico-MS/0.7 (+pesquisa e docencia)"


def download_one(name: str, urls: list[str]) -> Path:
    target = RAW / name
    if target.exists() and target.stat().st_size > 1_000_000:
        print(f"[já existe] {name} ({target.stat().st_size/1024/1024:.1f} MB)")
        return target
    last = None
    for url in urls:
        try:
            print(f"[baixando] {name}")
            with requests.get(url, stream=True, timeout=120, headers={"User-Agent": UA}) as r:
                r.raise_for_status()
                tmp = target.with_suffix(target.suffix + ".part")
                with tmp.open("wb") as f:
                    total = 0
                    for chunk in r.iter_content(1024 * 1024):
                        if not chunk:
                            continue
                        f.write(chunk)
                        total += len(chunk)
                        if total and total % (10 * 1024 * 1024) < 1024 * 1024:
                            print(f"  {total/1024/1024:.0f} MB")
                tmp.replace(target)
            if target.stat().st_size < 1_000_000:
                raise RuntimeError("arquivo demasiado pequeno; resposta não parece NetCDF")
            print(f"[ok] {name} ({target.stat().st_size/1024/1024:.1f} MB)")
            return target
        except Exception as exc:
            last = exc
            if target.with_suffix(target.suffix + ".part").exists():
                target.with_suffix(target.suffix + ".part").unlink(missing_ok=True)
    raise RuntimeError(f"não foi possível baixar {name}: {last}")


def coord_name(ds, candidates):
    for name in candidates:
        if name in ds.coords or name in ds.dims:
            return name
    raise RuntimeError(f"coordenada não encontrada; disponíveis: {list(ds.coords)}")


def subset_bbox(ds):
    lon = coord_name(ds, ["longitude", "lon", "x"])
    lat = coord_name(ds, ["latitude", "lat", "y"])
    lons = ds[lon].values
    lats = ds[lat].values
    lon_slice = slice(WEST, EAST) if lons[0] < lons[-1] else slice(EAST, WEST)
    lat_slice = slice(SOUTH, NORTH) if lats[0] < lats[-1] else slice(NORTH, SOUTH)
    return ds.sel({lon: lon_slice, lat: lat_slice})


def crop(src: Path, out: Path):
    if out.exists() and out.stat().st_size > 10_000:
        print(f"[já existe] {out.name}")
        return
    print(f"[recortando] {src.name} -> {out.name}")
    with xr.open_dataset(src) as ds:
        sub = subset_bbox(ds).load()
        sub.to_netcdf(out)
    print(f"[ok] {out.name} ({out.stat().st_size/1024/1024:.2f} MB)")


def main() -> int:
    try:
        up = download_one("uparea_glofas_v4_0.nc", FILES["uparea_glofas_v4_0.nc"])
        ldd = download_one("ldd_glofas_v4_0.nc", FILES["ldd_glofas_v4_0.nc"])
        crop(up, PROC / "uparea_ms_v4.nc")
        crop(ldd, PROC / "ldd_ms_v4.nc")
    except Exception as exc:
        print("ERRO:", exc, file=sys.stderr)
        return 2
    print("\nMapas estáticos GloFAS v4 preparados para Mato Grosso do Sul.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
