# Pulso Hídrico MS — V0.8

Atualização para série homogênea **GloFAS Historical v4, 2001–2025**, mantendo a rede nativa LISFLOOD validada na V7.

## O que muda

- download reanudável de 2001–2025;
- **uma solicitação EWDS por ano**, em vez de milhares de pedidos diários;
- recorte espacial limitado a Mato Grosso do Sul;
- conversão local de cada ano em 12 blocos mensais;
- arquivo web binário `Float32` com descarga em m³/s, sem perda adicional além da precisão float32 do produto;
- PWA carrega somente o mês consultado;
- linha do tempo real diária quando os blocos V8 existem;
- compatibilidade com os quatro JSON de validação V7;
- correção do aviso falso “Mapa base sem conexão”;
- formatação numérica `pt-BR`.

## Uso

A V7 deve estar funcionando primeiro. Descompacte este ZIP **sobre a pasta atual do projeto** e execute:

```text
BAIXAR_SERIE_2001_2025.cmd
```

O processo pode ser interrompido. Ao executar de novo, arquivos anuais e mensais válidos são ignorados e o trabalho continua do ponto em que parou.

## Estrutura de dados

```text
data/processed/glofas_v8_yearly/
  glofas_ms_v4_2001.nc
  ...
  glofas_ms_v4_2025.nc

docs/data/pulse-v8/
  index.json
  2001/
    2001-01.json
    2001-01.f32
    ...
```

Cada `.f32` é uma matriz `[dia, segmento]` em `float32 little-endian`. A ordem dos segmentos é exatamente a de `docs/data/glofas_network.geojson`.

## Homogeneidade

A V8 mantém **GloFAS v4** em toda a série 2001–2025. Embora GloFAS v5 esteja disponível no EWDS, não se misturam versões dentro da mesma série.
