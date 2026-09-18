#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import cdsapi

from v8_common import (
    DATASET, GAP_DIR, YEAR_DIR, day_request, ensure_dirs, load_progress,
    mark_unavailable, missing_dates, save_progress, unavailable_dates, validate_gap_file,
    validate_year_bundle, validate_year_file, year_request,
)


def _is_end_of_year_invalid_request(day_iso: str, exc: Exception) -> bool:
    # EWDS pode recusar a combinação 31/12 para dis24/time_mean em alguns anos.
    # Só toleramos esse caso estreito: 31 de dezembro + resposta explícita 400/invalid request.
    text = str(exc).lower()
    return day_iso.endswith('-12-31') and ('400 client error' in text or 'bad request' in text) and 'invalid request' in text



def download_missing_days(client: cdsapi.Client, target: Path, year: int) -> None:
    gaps = missing_dates(target, year)
    if not gaps:
        return
    folder = GAP_DIR / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    print(f'[reparo] resposta anual incompleta: faltam {len(gaps)} dia(s): {", ".join(gaps)}')
    for day_iso in gaps:
        out = folder / f'{day_iso}.nc'
        # Se já existe e é legível, não baixa outra vez.
        ok, _ = validate_gap_file(out, day_iso)
        if ok:
            print(f'  [já existe] {day_iso}')
            continue
        out.unlink(missing_ok=True)
        print(f'  [baixando dia ausente] {day_iso}')
        try:
            client.retrieve(DATASET, day_request(day_iso), str(out))
        except Exception as exc:
            out.unlink(missing_ok=True)
            if _is_end_of_year_invalid_request(day_iso, exc):
                reason = f'EWDS recusou a combinação para {day_iso}: {exc}'
                mark_unavailable(day_iso, reason)
                print(f'  [indisponível no EWDS] {day_iso} · não será interpolado nem inventado')
                continue
            raise
        ok, detail = validate_gap_file(out, day_iso)
        if not ok:
            raise RuntimeError(f'reparo {day_iso} inválido: {detail}')
        print(f'  [ok] {day_iso}')


def download_year(year: int, retries: int = 3) -> Path:
    ensure_dirs()
    target = YEAR_DIR / f'glofas_ms_v4_{year}.nc'
    ok, detail = validate_year_bundle(target, year, strict=True)
    if ok:
        print(f'[já existe] {target.name} · {detail} · {target.stat().st_size/1024/1024:.1f} MB')
        return target

    progress = load_progress()
    progress.setdefault('years', {}).setdefault(str(year), {})
    client = cdsapi.Client()

    # Caso típico observado no EWDS: arquivo anual com uma ou poucas datas ausentes.
    # Preserva o arquivo recebido e solicita apenas as datas ausentes.
    base_ok, base_detail = validate_year_file(target, year, strict=False)
    if base_ok:
        print(f'[aviso] {target.name} está utilizável, mas incompleto: {base_detail}')
        try:
            download_missing_days(client, target, year)
            ok, detail = validate_year_bundle(target, year, strict=True)
            if ok:
                progress['years'][str(year)].update({
                    'downloaded': True,
                    'repaired': True,
                    'downloaded_at': datetime.now(timezone.utc).isoformat(),
                    'size_bytes': target.stat().st_size,
                    'validation': detail,
                })
                save_progress(progress)
                print(f'[ok reparado] {year} · {detail}')
                return target
        except Exception as exc:
            print(f'[aviso] reparo do arquivo existente falhou: {exc}', file=sys.stderr)
            # Não apaga o arquivo-base; tenta nova resposta anual abaixo.

    request = year_request(year)
    for attempt in range(1, retries + 1):
        print(f'[baixando] GloFAS v4 {year} · tentativa {attempt}/{retries}')
        print('           1 variável · MS · ano completo · NetCDF')
        try:
            # Não destruímos uma resposta anual anterior útil. Nova tentativa vai para .new.
            dl_target = target if not target.exists() else target.with_suffix('.new.nc')
            dl_target.unlink(missing_ok=True)
            client.retrieve(DATASET, request, str(dl_target))
            if dl_target != target:
                # Só substitui se o novo arquivo for pelo menos estruturalmente válido.
                new_ok, new_detail = validate_year_file(dl_target, year, strict=False)
                if not new_ok:
                    raise RuntimeError(f'novo arquivo anual inválido: {new_detail}')
                dl_target.replace(target)

            base_ok, base_detail = validate_year_file(target, year, strict=False)
            if not base_ok:
                raise RuntimeError(f'arquivo anual recebido inválido: {base_detail}')

            download_missing_days(client, target, year)
            ok, detail = validate_year_bundle(target, year, strict=True)
            if not ok:
                raise RuntimeError(f'ano ainda incompleto após reparo: {detail}')

            progress['years'][str(year)].update({
                'downloaded': True,
                'repaired': bool(missing_dates(target, year) == []),
                'downloaded_at': datetime.now(timezone.utc).isoformat(),
                'size_bytes': target.stat().st_size,
                'validation': detail,
            })
            save_progress(progress)
            print(f'[ok] {target.name} · {detail} · {target.stat().st_size/1024/1024:.1f} MB')
            return target
        except Exception as exc:
            print(f'[erro] {year}: {exc}', file=sys.stderr)
            if attempt >= retries:
                progress['years'][str(year)].update({
                    'downloaded': False,
                    'last_error': str(exc),
                    'failed_at': datetime.now(timezone.utc).isoformat(),
                })
                save_progress(progress)
                raise
            wait = [15, 60, 180][min(attempt - 1, 2)]
            print(f'       nova tentativa em {wait}s...')
            time.sleep(wait)
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--retries', type=int, default=3)
    args = ap.parse_args()
    try:
        download_year(args.year, args.retries)
        return 0
    except Exception as exc:
        print(f'ERRO FINAL {args.year}: {exc}', file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
