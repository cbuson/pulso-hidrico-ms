#!/usr/bin/env python3
"""Gera somente geometria DEMO para testar a interface. Não produz dados científicos."""
from __future__ import annotations
import json, math, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'data'
OUT.mkdir(parents=True,exist_ok=True)

# Contorno estilizado APENAS para modo de teste. Não é limite oficial.
ring=[
 [-57.70,-17.75],[-56.70,-17.45],[-55.45,-17.40],[-54.45,-17.15],[-53.55,-17.45],[-52.70,-18.05],
 [-51.85,-18.70],[-51.35,-19.55],[-51.45,-20.35],[-51.85,-21.05],[-52.45,-21.55],[-52.70,-22.15],
 [-53.25,-22.75],[-53.75,-23.45],[-54.45,-23.95],[-55.15,-23.95],[-55.65,-23.55],[-56.35,-23.55],
 [-56.95,-23.05],[-57.45,-22.35],[-57.65,-21.55],[-57.55,-20.75],[-57.75,-19.85],[-57.55,-18.85],[-57.70,-17.75]
]
boundary={"type":"FeatureCollection","demo":True,"features":[{"type":"Feature","properties":{"name":"Mato Grosso do Sul · contorno DEMO","demo":True,"warning":"Geometria aproximada apenas para teste da interface"},"geometry":{"type":"Polygon","coordinates":[ring]}}]}

# Rede sintética dendrítica. Os eixos são abstratos e não recebem nomes de rios reais.
rnd=random.Random(20250917)
features=[]

def add(coords,order=1,basin='demo'):
    i=len(features)+1
    features.append({"type":"Feature","properties":{"id":f"demo-{i:04d}","demo":True,"order":order,"basin":basin},"geometry":{"type":"LineString","coordinates":coords}})

# Dois coletores principais, um a oeste e outro a leste, para dar leitura de duas grandes vertentes.
west=[[-57.45,-18.0],[-57.50,-18.7],[-57.48,-19.4],[-57.42,-20.1],[-57.45,-20.8],[-57.35,-21.5],[-57.25,-22.2],[-57.15,-22.75]]
east=[[-52.15,-18.8],[-51.85,-19.5],[-51.65,-20.2],[-51.90,-20.9],[-52.20,-21.5],[-52.55,-22.1],[-52.95,-22.75],[-53.45,-23.45]]
add(west,5,'oeste'); add(east,5,'leste')

# Eixos intermediários que convergem aos coletores.
west_axes=[
 ([[-53.5,-18.3],[-54.5,-18.7],[-55.5,-19.0],[-56.4,-19.25],[-57.48,-19.4]],4),
 ([[-53.8,-19.6],[-54.8,-19.8],[-55.7,-20.05],[-56.6,-20.12],[-57.42,-20.1]],4),
 ([[-54.1,-20.7],[-55.0,-20.8],[-55.9,-21.0],[-56.7,-21.25],[-57.35,-21.5]],4),
 ([[-54.7,-22.0],[-55.4,-22.15],[-56.1,-22.35],[-56.7,-22.55],[-57.15,-22.75]],3)
]
east_axes=[
 ([[-54.4,-18.0],[-53.6,-18.3],[-52.8,-18.55],[-52.15,-18.8]],4),
 ([[-54.4,-19.3],[-53.6,-19.5],[-52.8,-19.8],[-51.85,-19.5]],4),
 ([[-54.2,-20.7],[-53.5,-20.8],[-52.8,-20.9],[-51.9,-20.9]],4),
 ([[-54.5,-21.9],[-53.8,-21.8],[-53.0,-21.7],[-52.2,-21.5]],4),
 ([[-55.0,-22.8],[-54.4,-22.7],[-53.7,-22.55],[-52.95,-22.75]],3)
]
for c,o in west_axes:add(c,o,'oeste')
for c,o in east_axes:add(c,o,'leste')

# Tributários curtos convergentes, determinísticos.
axes=[f for f in features if f['properties']['order'] in (3,4)]
for ai,axis in enumerate(axes):
    coords=axis['geometry']['coordinates']
    for j in range(7):
        seg=j%(len(coords)-1)
        a,b=coords[seg],coords[seg+1]
        t=.25+.5*rnd.random()
        join=[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]
        side=-1 if j%2 else 1
        length=.28+.34*rnd.random()
        src=[join[0]+side*length*(.7+rnd.random()*.4), join[1]-(.18+rnd.random()*.55)]
        mid=[(src[0]+join[0])/2+rnd.uniform(-.08,.08),(src[1]+join[1])/2+rnd.uniform(-.05,.05)]
        add([src,mid,join],2,axis['properties']['basin'])
        if j%2==0:
            src2=[src[0]+side*(.18+rnd.random()*.16),src[1]-.12-rnd.random()*.20]
            mid2=[(src2[0]+src[0])/2,(src2[1]+src[1])/2]
            add([src2,mid2,src],1,axis['properties']['basin'])

rivers={"type":"FeatureCollection","demo":True,"features":features,"metadata":{"warning":"Rede sintética para teste de interface. Não representa a hidrografia real de Mato Grosso do Sul.","generated_by":"scripts/09_prepare_test_data.py","seed":20250917}}
(OUT/'boundary-demo.geojson').write_text(json.dumps(boundary,separators=(',',':')),encoding='utf-8')
(OUT/'rivers-demo.geojson').write_text(json.dumps(rivers,separators=(',',':')),encoding='utf-8')
print(f"OK: {len(features)} feições demo em {OUT/'rivers-demo.geojson'}")
