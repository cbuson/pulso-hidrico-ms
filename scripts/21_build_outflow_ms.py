#!/usr/bin/env python3
"""Calcula a série diária de descarga modelada que cruza o limite de MS para fora.

Definição operacional
---------------------
Um "segmento de saída" é uma ligação da rede nativa GloFAS/LISFLOOD cuja
célula de origem está dentro (ou sobre) o limite de Mato Grosso do Sul e cujo
ponto a jusante está fora do limite. A série soma a descarga GloFAS desses
cruzamentos para cada dia disponível no arquivo V8.

Isto NÃO é um balanço hídrico líquido do estado: rios podem entrar e sair mais
de uma vez ao longo da fronteira e todos os cruzamentos de saída válidos são
somados. O objetivo é fornecer um indicador espacialmente rastreável de fluxo
modelado para fora de MS, compatível com a própria rede LISFLOOD usada no mapa.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone

import numpy as np
from shapely.geometry import Point, LineString, shape, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "data"
NETWORK = DATA / "glofas_network.geojson"
BOUNDARY = DATA / "boundary.geojson"
ARCHIVE = DATA / "pulse-v8"
OUT_JSON = DATA / "outflow-ms.json"
OUT_CSV = DATA / "outflow-ms.csv"
OUT_OUTLETS = DATA / "outflow-ms-outlets.geojson"


def load_fc(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def boundary_geometry() -> object:
    fc = load_fc(BOUNDARY)
    geoms = [shape(f["geometry"]) for f in fc.get("features", []) if f.get("geometry")]
    if not geoms:
        raise RuntimeError("boundary.geojson sem geometrias")
    geom = unary_union(geoms)
    if geom.is_empty:
        raise RuntimeError("limite de MS vazio")
    return geom


def outlet_segments() -> tuple[list[int], list[dict]]:
    boundary = boundary_geometry()
    fc = load_fc(NETWORK)
    feats = fc.get("features") or []
    if not feats:
        raise RuntimeError("glofas_network.geojson vazio")

    idx: list[int] = []
    audit: list[dict] = []
    for i, feat in enumerate(feats):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "LineString":
            continue
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        a = coords[0]
        b = coords[-1]
        p0 = Point(float(a[0]), float(a[1]))
        p1 = Point(float(b[0]), float(b[1]))
        # A direção é definida pelo LDD: primeiro ponto -> ponto a jusante.
        if boundary.covers(p0) and not boundary.covers(p1):
            idx.append(i)
            props = dict(feat.get("properties") or {})
            props.update({"archive_index": i, "crossing": "outbound_ms"})
            audit.append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "LineString", "coordinates": [a, b]},
            })

    if not idx:
        raise RuntimeError(
            "nenhum cruzamento de saída foi encontrado. Verifique se boundary.geojson "
            "e glofas_network.geojson usam WGS84 e a mesma versão da rede."
        )

    OUT_OUTLETS.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": audit,
                "metadata": {
                    "method": "GloFAS/LISFLOOD directed links with origin inside MS and downstream endpoint outside MS",
                    "count": len(idx),
                },
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return idx, feats


def month_files() -> list[Path]:
    files = sorted(ARCHIVE.glob("*/*.json"))
    return [p for p in files if p.name != "index.json"]


def process() -> dict:
    outlet_idx, network_feats = outlet_segments()
    rows: list[tuple[str, float | None, int]] = []
    month_count = 0

    for meta_path in month_files():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("format") != "pulso-v8-f32":
            continue
        dates = [str(x) for x in meta.get("dates", [])]
        nseg = int(meta.get("segment_count") or 0)
        nday = int(meta.get("day_count") or len(dates))
        if nseg != len(network_feats):
            raise RuntimeError(
                f"{meta_path}: segment_count={nseg}, mas a rede atual tem {len(network_feats)} segmentos"
            )
        bin_name = meta.get("binary_file") or (meta_path.stem + ".f32")
        bin_path = meta_path.parent / bin_name
        if not bin_path.exists():
            raise FileNotFoundError(bin_path)
        raw = np.fromfile(bin_path, dtype="<f4")
        expected = nday * nseg
        if raw.size != expected:
            raise RuntimeError(f"{bin_path}: {raw.size} valores; esperado {expected}")
        arr = raw.reshape(nday, nseg)
        month_count += 1
        for di, date in enumerate(dates):
            v = np.asarray(arr[di, outlet_idx], dtype=float)
            valid = np.isfinite(v) & (v >= 0)
            q = float(np.sum(v[valid])) if np.any(valid) else None
            rows.append((date, q, int(np.sum(valid))))

    if not rows:
        raise RuntimeError("nenhum bloco V8 foi encontrado em docs/data/pulse-v8")

    # Em caso de repetição por reparos, a última leitura válida vence.
    by_date: dict[str, tuple[float | None, int]] = {}
    for date, q, n in rows:
        by_date[date] = (q, n)
    dates = sorted(by_date)
    values = [by_date[d][0] for d in dates]
    counts = [by_date[d][1] for d in dates]

    annual: dict[str, dict] = {}
    for year in sorted({d[:4] for d in dates}):
        items = [(d, by_date[d][0]) for d in dates if d.startswith(year + "-") and by_date[d][0] is not None]
        if not items:
            continue
        peak_date, peak = max(items, key=lambda x: x[1])
        annual[year] = {
            "peak_date": peak_date,
            "peak_m3s": round(float(peak), 3),
            "day_count": len(items),
        }

    payload = {
        "version": "0.8.6.5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metric": "sum_outbound_glofas_discharge",
        "unit": "m3/s",
        "network": "GloFAS v4 / LISFLOOD",
        "outlet_segment_count": len(outlet_idx),
        "date_count": len(dates),
        "month_count": month_count,
        "start": dates[0],
        "end": dates[-1],
        "dates": dates,
        "values_m3s": [None if v is None else round(float(v), 3) for v in values],
        "valid_outlet_segments": counts,
        "annual": annual,
        "definition_pt": "Soma da descarga GloFAS nos segmentos dirigidos da rede LISFLOOD que cruzam o limite de Mato Grosso do Sul no sentido de saída.",
        "definition_es": "Suma del caudal GloFAS en los segmentos dirigidos de la red LISFLOOD que cruzan el límite de Mato Grosso do Sul en sentido de salida.",
        "caveat_pt": "Indicador de fluxo para fora do estado; não representa balanço hídrico líquido. Rios que entram novamente em MS podem gerar mais de um cruzamento.",
        "caveat_es": "Indicador del flujo que sale del estado; no representa un balance hídrico neto. Los ríos que vuelven a entrar en MS pueden generar más de un cruce.",
        "sources": {
            "discharge": "CEMS GloFAS Historical v4",
            "routing": "GloFAS/LISFLOOD LDD",
            "boundary": "boundary.geojson local de Mato Grosso do Sul",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "outbound_discharge_m3s", "valid_outlet_segments"])
        for d, v, n in zip(dates, values, counts):
            w.writerow([d, "" if v is None else f"{v:.3f}", n])

    return payload


def main() -> int:
    try:
        p = process()
    except Exception as exc:
        print("ERRO:", exc)
        return 2
    print("=" * 68)
    print("PULSO HÍDRICO MS · SAÍDA HÍDRICA")
    print("=" * 68)
    print(f"Cruzamentos de saída: {p['outlet_segment_count']}")
    print(f"Série: {p['date_count']:,} dias · {p['start']} -> {p['end']}")
    print(f"Arquivo: {OUT_JSON.relative_to(ROOT)}")
    print(f"Auditoria: {OUT_OUTLETS.relative_to(ROOT)}")
    print("Não é balanço hídrico líquido; é soma dos cruzamentos dirigidos para fora de MS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
