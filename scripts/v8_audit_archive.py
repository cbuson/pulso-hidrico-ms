#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from v8_common import ARCHIVE_DIR, END_YEAR, START_YEAR, load_network, rebuild_index


def main() -> int:
    ids, _, _ = load_network()
    idx = rebuild_index()
    print('PULSO HÍDRICO MS — auditoria V8')
    print(f'Rede: {len(ids):,} segmentos')
    print(f'Datas: {idx["date_count"]:,}')
    print(f'Meses: {idx["month_count"]}')
    print(f'Período: {idx.get("start")} → {idx.get("end")}')
    bad = 0
    total_bytes = 0
    for key, info in sorted(idx['months'].items()):
        meta_path = ARCHIVE_DIR / info['meta']
        bin_path = ARCHIVE_DIR / info['binary']
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        expected = len(meta['dates']) * len(ids) * 4
        actual = bin_path.stat().st_size if bin_path.exists() else -1
        total_bytes += max(0, actual)
        if actual != expected:
            print(f'[ERRO] {key}: binário {actual} B; esperado {expected} B')
            bad += 1
    print(f'Tamanho dos binários: {total_bytes/1024/1024:.1f} MB')
    target_days = sum(366 if y % 400 == 0 or (y % 4 == 0 and y % 100 != 0) else 365 for y in range(START_YEAR, END_YEAR + 1))
    print(f'Cobertura alvo 2001–2025: {idx["date_count"]}/{target_days} dias ({idx["date_count"]/target_days*100:.1f}%)')
    if bad:
        print(f'Falhas: {bad}')
        return 2
    print('Estrutura binária consistente.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
