"""
06 - Exporta límite y HydroRIVERS a formatos ligeros consumidos por la PWA.

No inventa datos diarios. Solo prepara geometría estática:
  docs/data/boundary.geojson
  docs/data/rivers.geojson
  docs/data/meta.json

Por defecto conserva ríos de orden Strahler >= 2 para que el GeoJSON sea
manejable en teléfonos. Cambiar --min-order si se necesita más detalle.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

BASE = Path(__file__).resolve().parent.parent
DEFAULT_BOUNDARY = BASE / "data" / "raw" / "boundary" / "ms_boundary.geojson"
DEFAULT_RIVERS = BASE / "data" / "processed" / "rivers_ms.gpkg"
DEFAULT_OUT = BASE / "docs" / "data"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    p.add_argument("--rivers", type=Path, default=DEFAULT_RIVERS)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--min-order", type=int, default=2)
    p.add_argument("--simplify", type=float, default=0.0008,
                   help="Tolerancia en grados WGS84. 0 desactiva simplificación.")
    return p.parse_args()


def write_geojson(gdf: gpd.GeoDataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gdf.to_json(drop_id=True), encoding="utf-8")


def main():
    args = parse_args()
    if not args.boundary.exists():
        raise SystemExit(f"No existe el límite: {args.boundary}")
    if not args.rivers.exists():
        raise SystemExit(f"No existe la red de ríos: {args.rivers}")

    boundary = gpd.read_file(args.boundary).to_crs(4326)
    rivers = gpd.read_file(args.rivers).to_crs(4326)

    order_col = next((c for c in ["ORD_STRA", "ord_stra"] if c in rivers.columns), None)
    if order_col:
        rivers = rivers[rivers[order_col].fillna(0).astype(float) >= args.min_order].copy()

    id_col = next((c for c in ["HYRIV_ID", "hyriv_id", "id"] if c in rivers.columns), None)
    keep = [c for c in [id_col, order_col, "DIS_AV_CMS", "UPLAND_SKM", "MAIN_RIV"] if c and c in rivers.columns]
    rivers = rivers[keep + [rivers.geometry.name]].copy()

    if args.simplify > 0:
        rivers.geometry = rivers.geometry.simplify(args.simplify, preserve_topology=False)
        boundary.geometry = boundary.geometry.simplify(args.simplify / 2, preserve_topology=True)

    args.out.mkdir(parents=True, exist_ok=True)
    write_geojson(boundary, args.out / "boundary.geojson")
    write_geojson(rivers, args.out / "rivers.geojson")

    meta = {
        "mode": "real",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "river_segments": int(len(rivers)),
        "min_strahler_order": args.min_order if order_col else None,
        "sources": {
            "boundary": "IBGE — malha estadual processada localmente",
            "rivers": "HydroRIVERS — HydroSHEDS processado localmente",
            "discharge": "GloFAS — arquivos diários opcionais em data/pulse/",
            "temperature": "DynQual ou fonte configurada — arquivos diários opcionais em data/pulse/"
        }
    }
    (args.out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"PWA preparada: {len(rivers)} segmentos em {args.out / 'rivers.geojson'}")
    print("A interface agora mostrará a rede real. Para valores diários, gerar data/pulse/YYYY-MM-DD.json.")


if __name__ == "__main__":
    main()
