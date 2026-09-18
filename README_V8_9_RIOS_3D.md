# Pulso Hídrico MS · V8.9 · Rios volumétricos 3D

Esta versão recupera o componente vertical do pulso fluvial sobre o terreno 3D.

## Codificação científica

- terreno 3D = DEM Mapzen/AWS;
- cor dos rios = climatologia mensal DynQual;
- largura dos rios = descarga GloFAS;
- altura dos rios = descarga GloFAS em transformação logarítmica fixa;
- a altura é **exagero visual** e não representa altitude física nem volume armazenado.

A descarga é uma taxa de fluxo em m³/s. O efeito volumétrico serve para tornar as diferenças
hidrológicas perceptíveis, de maneira análoga a uma superfície 2.5D temática.

## Implementação

Para manter desempenho móvel, os rios são construídos como várias fitas WebGL empilhadas.
A quantidade de camadas é reduzida automaticamente no celular.

O modo 3D usa `TerrainExtension` em modo `offset`, enquanto a pegada dos rios permanece
projetada sobre o terreno.

## Instalação

Substituir apenas:

```text
docs/3d/
```

Não apagar `docs/data/`.

Abrir:

```text
http://localhost:9564/3d/
```

A versão visível deve ser:

```text
V0.8.9 · RIOS VOLUMÉTRICOS 3D
```

## Teste visual

O que deve ser verificado:

1. Mato Grosso do Sul continua reconhecível como território.
2. Rios de maior descarga sobem claramente acima do terreno.
3. Rios de menor descarga permanecem baixos.
4. A escala relativa não muda de mês para mês.
5. Pinch, rotação e inclinação continuam fluidos no celular.
