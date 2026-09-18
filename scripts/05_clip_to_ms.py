"""
05 - Recorta HydroRIVERS y, cuando estén disponibles, DynQual/GloFAS a MS.

La geometría hidrográfica queda en data/processed/rivers_ms.gpkg.
DynQual se recorta a data/processed/water_temp_ms.nc.
Los GloFAS descargados por 03 ya vienen recortados por bounding box y no necesitan
volver a pasar por este script.
"""

from pathlib import Path
import geopandas as gpd
import xarray as xr

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
BOUNDARY_FILE = RAW / "boundary" / "ms_boundary.geojson"
HYDRORIVERS_SHP = RAW / "hydrorivers" / "shp" / "HydroRIVERS_v10_sa.shp"
DYNQUAL_NC = RAW / "dynqual" / "waterTemperature_monthlyAvg_1980_2019.nc"


def find_coord(ds, names):
    for n in names:
        if n in ds.coords or n in ds.dims:
            return n
    raise ValueError(f"No encontré coordenada entre {names}. Disponibles: {list(ds.coords)}")


def clip_rivers(boundary):
    if not HYDRORIVERS_SHP.exists():
        print(f"Aviso: falta {HYDRORIVERS_SHP}; se omite HydroRIVERS.")
        return
    print("Recortando HydroRIVERS a MS …")
    rivers = gpd.read_file(HYDRORIVERS_SHP, bbox=tuple(boundary.to_crs(4326).total_bounds))
    rivers = rivers.to_crs(boundary.crs)
    clipped = gpd.clip(rivers, boundary)
    out = PROCESSED / "rivers_ms.gpkg"
    clipped.to_file(out, driver="GPKG")
    print(f"Guardado {out} ({len(clipped)} segmentos)")


def clip_dynqual(bounds):
    if not DYNQUAL_NC.exists():
        print("DynQual todavía no descargado; se omite temperatura.")
        return
    print("Recortando DynQual a MS …")
    ds = xr.open_dataset(DYNQUAL_NC)
    lon = find_coord(ds, ["longitude", "lon", "x"])
    lat = find_coord(ds, ["latitude", "lat", "y"])
    minx, miny, maxx, maxy = bounds

    lon_vals = ds[lon].values
    lat_vals = ds[lat].values
    lon_slice = slice(minx, maxx) if lon_vals[0] < lon_vals[-1] else slice(maxx, minx)
    lat_slice = slice(miny, maxy) if lat_vals[0] < lat_vals[-1] else slice(maxy, miny)
    sub = ds.sel({lon: lon_slice, lat: lat_slice})
    out = PROCESSED / "water_temp_ms.nc"
    sub.to_netcdf(out)
    print(f"Guardado {out}")


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    if not BOUNDARY_FILE.exists():
        raise SystemExit("Falta el límite de MS. Ejecuta 01_download_boundary.py o 00_bootstrap_ms_geometry.py")
    boundary = gpd.read_file(BOUNDARY_FILE).to_crs(4326)
    clip_rivers(boundary)
    clip_dynqual(tuple(boundary.total_bounds))


if __name__ == "__main__":
    main()
