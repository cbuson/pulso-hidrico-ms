#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from v8_common import END_YEAR, PROGRESS, ROOT, START_YEAR, YEAR_DIR, load_progress, rebuild_index, save_progress


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(ROOT / 'scripts' / script), *args]
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    if rc != 0:
        raise RuntimeError(f'comando falhou ({rc}): {" ".join(cmd)}')


def main() -> int:
    ap = argparse.ArgumentParser(description='Baixa e processa a série GloFAS v4 2001–2025 de forma reanudável.')
    ap.add_argument('--start-year', type=int, default=START_YEAR)
    ap.add_argument('--end-year', type=int, default=END_YEAR)
    ap.add_argument('--download-only', action='store_true')
    ap.add_argument('--process-only', action='store_true')
    args = ap.parse_args()
    if args.download_only and args.process_only:
        raise SystemExit('Escolha apenas --download-only ou --process-only.')
    if args.start_year > args.end_year:
        raise SystemExit('start-year > end-year')

    progress = load_progress()
    progress['series'] = {
        'start_year': args.start_year,
        'end_year': args.end_year,
        'system_version': 'version_4_0',
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }
    save_progress(progress)

    print('=' * 68)
    print('PULSO HÍDRICO MS — V8.3 · SÉRIE GLOFAS 2001–2025')
    print('V4 homogênea · reanudável · falhas EWDS explícitas nunca são interpoladas')
    print('=' * 68)
    print('Pode fechar e executar novamente depois: anos/meses válidos são pulados.')
    print()

    failures: list[tuple[int, str]] = []
    for year in range(args.start_year, args.end_year + 1):
        print('\n' + '-' * 68)
        print(f'ANO {year}')
        print('-' * 68)
        try:
            if not args.process_only:
                run('v8_download_year.py', '--year', str(year))
            if not args.download_only:
                run('v8_build_year.py', '--year', str(year))
            progress = load_progress()
            progress.setdefault('years', {}).setdefault(str(year), {})['v8_complete'] = not args.download_only
            progress['years'][str(year)]['updated_at'] = datetime.now(timezone.utc).isoformat()
            save_progress(progress)
        except Exception as exc:
            failures.append((year, str(exc)))
            print(f'[FALHOU] {year}: {exc}', file=sys.stderr)
            print('A série é reanudável. Corrija o problema e execute novamente; o que já está pronto será preservado.')
            break

    idx = rebuild_index()
    print('\n' + '=' * 68)
    print(f'V8 disponível: {idx["date_count"]:,} dias em {idx["month_count"]} meses.')
    if idx.get('start'):
        print(f'Período local atual: {idx["start"]} → {idx["end"]}')
    if failures:
        print(f'Interrompido em {failures[0][0]}. Execute novamente depois de corrigir o erro.')
        return 5
    print('Série solicitada concluída.')
    print('Recarregue a PWA com Ctrl+Shift+R.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
