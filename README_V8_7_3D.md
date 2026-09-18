# Pulso Hídrico MS · V8.7 · Pulso 3D experimental

Este pacote adiciona uma visualização 3D experimental **sem substituir a interface 2D estável**.

## Instalação

Copie a pasta `docs/3d` para a raiz `docs` do projeto atual.

Não substitua `docs/data`. O protótipo reutiliza diretamente os dados já publicados:

- `docs/data/rivers.geojson`
- `docs/data/glofas_network.geojson`
- `docs/data/boundary.geojson`
- `docs/data/temperature-climatology.json`
- `docs/data/pulse-v8/`
- `docs/data/outflow-ms.json` quando disponível

## Abrir localmente

Com o servidor atual do projeto:

```text
SERVIDOR_9564.cmd
```

abra:

```text
http://localhost:9564/3d/
```

## GitHub Pages

Depois de copiar `docs/3d`, fazer commit e push:

```text
https://cbuson.github.io/pulso-hidrico-ms/3d/
```

## Escopo V8.7

- ano piloto: **2025**
- 12 estados mensais
- data representativa: dia disponível mais próximo do dia 15
- geometria visível: PIN MS / IMASUL
- descarga: GloFAS v4
- cor: climatologia mensal DynQual 1980–2019
- altura e largura: transformação logarítmica fixa da descarga
- mapa WebGL com deck.gl
- zoom por pinça, pan, rotação/inclinação quando suportados
- gráfico da saída hídrica de MS se `outflow-ms.json` estiver publicado
- interface PT/ES

## Importante

A altura 3D é **exagero visual**, não altitude física do rio. A constante de referência é mantida fixa entre os 12 meses para que a comparação temporal seja válida.

Este modo é experimental. A V8.6.x 2D continua sendo a visualização de consulta científica principal até validação de desempenho, legibilidade e coerência espacial no celular.
