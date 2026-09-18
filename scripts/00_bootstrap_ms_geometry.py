"""
00 - Arranque rápido de la PWA con geometría REAL de Mato Grosso do Sul.

Descarga automáticamente:
  * límite estadual de MS desde la API de malhas del IBGE;
  * HydroRIVERS v1.0 para South America desde HydroSHEDS.

Después recorta la red a MS y escribe directamente los archivos que consume la PWA:
  docs/data/boundary.geojson
  docs/data/rivers.geojson
  docs/data/meta.json

No descarga todavía caudal diario ni temperatura. Al terminar, la interfaz deja
DEMO VISUAL y pasa a DADOS REAIS para la geometría hidrográfica.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import requests

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
DOCS_DATA = BASE / "docs" / "data"

IBGE_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/50"
    "?formato=application/vnd.geo+json&qualidade=intermediaria"
)
HYDRORIVERS_URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_sa_shp.zip"


def download(url: str, path: Path, chunk_size: int = 1024 * 1024):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        print(f"Ya existe {path.name}; se reutiliza.")
        return
    print(f"Descargando {url}")
    with requests.get(url, stream=True, timeout=(30, 600)) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"  {100 * done / total:5.1f}%", end="\r")
    print(f"\nGuardado {path}")


def write_geojson(gdf: gpd.GeoDataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gdf.to_json(drop_id=True), encoding="utf-8")


def main():
    boundary_path = RAW / "boundary" / "ms_boundary.geojson"
    rivers_zip = RAW / "hydrorivers" / "HydroRIVERS_v10_sa_shp.zip"
    shp_dir = RAW / "hydrorivers" / "shp"

    download(IBGE_URL, boundary_path)
    download(HYDRORIVERS_URL, rivers_zip)

    shp_dir.mkdir(parents=True, exist_ok=True)
    shp = shp_dir / "HydroRIVERS_v10_sa.shp"
    if not shp.exists():
        print("Descomprimiendo HydroRIVERS …")
        with zipfile.ZipFile(rivers_zip) as zf:
            zf.extractall(shp_dir)
    if not shp.exists():
        candidates = list(shp_dir.rglob("*.shp"))
        if len(candidates) == 1:
            shp = candidates[0]
        else:
            raise SystemExit(f"No pude localizar HydroRIVERS_v10_sa.shp en {shp_dir}")

    print("Leyendo y recortando HydroRIVERS a Mato Grosso do Sul …")
    boundary = gpd.read_file(boundary_path).to_crs(4326)
    rivers = gpd.read_file(shp, bbox=tuple(boundary.total_bounds)).to_crs(4326)
    rivers = gpd.clip(rivers, boundary)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    gpkg = PROCESSED / "rivers_ms.gpkg"
    rivers.to_file(gpkg, driver="GPKG")

    # Para móvil: orden >= 2, simplificación suave. Conserva IDs para unir series diarias.
    order_col = next((c for c in ["ORD_STRA", "ord_stra"] if c in rivers.columns), None)
    pwa = rivers.copy()
    min_order = 2
    if order_col:
        pwa = pwa[pwa[order_col].fillna(0).astype(float) >= min_order].copy()
    id_col = next((c for c in ["HYRIV_ID", "hyriv_id", "id"] if c in pwa.columns), None)
    keep = [c for c in [id_col, order_col, "DIS_AV_CMS", "UPLAND_SKM", "MAIN_RIV"] if c and c in pwa.columns]
    pwa = pwa[keep + [pwa.geometry.name]].copy()
    pwa.geometry = pwa.geometry.simplify(0.0008, preserve_topology=False)
    boundary_pwa = boundary.copy()
    boundary_pwa.geometry = boundary_pwa.geometry.simplify(0.0004, preserve_topology=True)

    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    write_geojson(boundary_pwa, DOCS_DATA / "boundary.geojson")
    write_geojson(pwa, DOCS_DATA / "rivers.geojson")
    meta = {
        "mode": "real",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "river_segments": int(len(pwa)),
        "min_strahler_order": min_order if order_col else None,
        "temperature_mode": "DynQual monthly climatology 1980-2019 when configured",
        "sources": {
            "boundary": "IBGE — API de malhas, UF 50",
            "rivers": "HydroRIVERS v1.0 — HydroSHEDS, South America",
            "discharge": "GloFAS Historical v4 — optional daily pulse files",
            "temperature": "DynQual — optional monthly climatology 1980-2019"
        }
    }
    (DOCS_DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nLISTO: {len(pwa)} segmentos reales preparados para la PWA.")
    print("Recarga http://localhost:9564/ y debe aparecer DADOS REAIS.")
    print("La descarga/temperatura se añaden después con 03/04/07.")


if __name__ == "__main__":
    main()
