#!/usr/bin/env python3
from pathlib import Path
import sys

cfg = Path.home() / '.cdsapirc'
print('Arquivo esperado:', cfg)
if not cfg.exists():
    print('ERRO: .cdsapirc nao existe.')
    raise SystemExit(2)
text = cfg.read_text(encoding='utf-8', errors='replace')
url_line = next((ln for ln in text.splitlines() if ln.strip().lower().startswith('url:')), '')
key_line = next((ln for ln in text.splitlines() if ln.strip().lower().startswith('key:')), '')
url = url_line.split(':',1)[1].strip() if ':' in url_line else ''
key = key_line.split(':',1)[1].strip() if ':' in key_line else ''

if 'cds.climate.copernicus.eu/api' in url and 'ewds.' not in url:
    print('ERRO: o endpoint esta apontando para CDS.')
    print('GloFAS pertence ao EWDS. Use: https://ewds.climate.copernicus.eu/api')
    raise SystemExit(5)
if url.rstrip('/') != 'https://ewds.climate.copernicus.eu/api':
    print('ERRO: URL EWDS incorreta:', url or '(vazia)')
    print('Esperado: https://ewds.climate.copernicus.eu/api')
    raise SystemExit(3)
if not key:
    print('ERRO: token ausente no .cdsapirc.')
    raise SystemExit(3)

print('OK: .cdsapirc encontrado.')
print('OK: endpoint EWDS configurado.')
print('OK: token presente (nao sera exibido).')
try:
    import cdsapi
    cdsapi.Client()
except Exception as exc:
    print('ERRO ao iniciar cdsapi:', exc)
    raise SystemExit(4)
print('OK: cdsapi instalado e configuracao lida pelo Python.')
print('Lembrete: aceite a licenca do GloFAS Historical no portal EWDS.')
