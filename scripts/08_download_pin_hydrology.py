#!/usr/bin/env python3
"""Baixa snapshots locais para a PWA. Requer internet no computador do usuário."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'data'; OUT.mkdir(parents=True,exist_ok=True)
PIN='https://www.pinms.ms.gov.br/arcgis/rest/services/IMASUL/Camadas_SISLA_GRH/MapServer/0/query'
BOUNDARY='https://raw.githubusercontent.com/cbuson/atlas-geocientifico-ms/main/docs/camadas/arquivos/limite_ms_ibge_2025.geojson'
UA='Pulso-Hidrico-MS/0.5 (+pesquisa e docencia)'

def get_json(url,timeout=90):
    req=Request(url,headers={'User-Agent':UA,'Accept':'application/json,application/geo+json'})
    with urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8'))

def download_boundary():
    print('Baixando limite de MS usado no ITA ARANDU MS...')
    data=get_json(BOUNDARY)
    (OUT/'boundary.geojson').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    print('  OK boundary.geojson')

def download_rivers():
    print('Baixando hidrografia oficial PIN MS / IMASUL...')
    feats=[]; offset=0; page=1000
    while True:
        q={
          'where':'1=1','outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson',
          'resultOffset':str(offset),'resultRecordCount':str(page),'orderByFields':'OBJECTID_1'
        }
        url=PIN+'?'+urlencode(q)
        data=get_json(url)
        batch=data.get('features') or []
        feats.extend(batch)
        print(f'  {len(feats):,} feições')
        if len(batch)<page:break
        offset+=page
        if offset>100000:raise RuntimeError('Paginação excedeu o limite de segurança.')
        time.sleep(.08)
    if not feats:raise RuntimeError('O serviço respondeu sem feições.')
    fc={'type':'FeatureCollection','features':feats,'metadata':{
      'source':'PIN MS / IMASUL · Camadas SISLA GRH · Hidrografia','service':PIN,
      'downloaded_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'mode':'snapshot_local'
    }}
    (OUT/'rivers.geojson').write_text(json.dumps(fc,separators=(',',':')),encoding='utf-8')
    print('  OK rivers.geojson')

def main():
    errors=[]
    for fn in (download_boundary,download_rivers):
        try:fn()
        except Exception as e:
            errors.append(f'{fn.__name__}: {e}')
            print('ERRO:',e,file=sys.stderr)
    if errors:
        print('\nA PWA continua funcionando em MODO TESTE. Falhas:',file=sys.stderr)
        for e in errors:print(' -',e,file=sys.stderr)
        return 1
    print('\nDados geométricos reais gravados em docs/data/. Recarregue a PWA com Ctrl+Shift+R.')
    print('Observação: isso NÃO cria descarga GloFAS nem temperatura real; o pulso permanece em modo teste até o pipeline temporal ser executado.')
    return 0
if __name__=='__main__':raise SystemExit(main())
