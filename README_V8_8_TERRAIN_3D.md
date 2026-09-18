# Pulso Hídrico MS · V8.8.1 · Cena 3D territorial

Correção visual da V8.8 após teste em navegador.

## O que foi corrigido

- textura de hillshade aplicada diretamente ao terreno 3D;
- máscara azul-cinza fora de Mato Grosso do Sul para recuperar a silhueta territorial;
- câmera inicial mais aberta e menos inclinada;
- enquadramento do estado inteiro com maior margem;
- relevo vertical reduzido de 2,15× para 1,65×;
- rios mais finos e aderidos ao relevo;
- navegação com `TerrainController` quando disponível;
- zoom por pinça, rotação e inclinação preservados;
- dados GloFAS, DynQual e série de saída não são alterados.

## Instalação

Copiar/substituir somente:

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
V0.8.8.1 · CENA 3D TERRITORIAL
```
