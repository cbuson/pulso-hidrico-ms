# Pulso Hídrico MS · V0.8.6.5

Atualização de experiência móvel científica.

## O que muda

- **Pinch-to-zoom real** com dois dedos no mapa, pan com um dedo e duplo toque para aproximar.
- **Bottom sheets móveis**: Camadas, Dados e Ajuda abrem sobre o mapa; Pulso fecha o painel e volta à visualização principal.
- O painel pode ser fechado pelo **X**, tocando fora dele ou arrastando o cabeçalho para baixo.
- **Saída hídrica de MS** substitui a linha temporal simples na tela principal móvel por uma curva diária do ano selecionado.
- A curva é interativa: tocar ou arrastar sobre ela escolhe um dia e sincroniza mapa, data e indicadores.
- **Máximo e ativos** são recalculados no navegador quando metadados antigos do V8 não trazem esses campos.
- Interface PT/ES preservada.

## Preparar a curva de saída hídrica

Depois de sobrepor esta atualização à pasta atual do projeto, execute uma única vez:

`PREPARAR_SAIDA_HIDRICA_MS.cmd`

O script não baixa novamente o GloFAS. Ele usa os blocos já presentes em `docs/data/pulse-v8` e cria:

- `docs/data/outflow-ms.json` — série web compacta
- `docs/data/outflow-ms.csv` — série auditável
- `docs/data/outflow-ms-outlets.geojson` — cruzamentos de saída usados no cálculo

### Definição

Um cruzamento de saída é uma ligação dirigida da rede GloFAS/LISFLOOD cuja origem está dentro do limite de MS e cujo ponto a jusante está fora. A curva soma a descarga modelada desses cruzamentos para cada dia.

**Importante:** é um indicador agregado de fluxo **para fora** do estado, não um balanço hídrico líquido. Um rio que saia e volte a entrar em MS pode produzir mais de um cruzamento ao longo do limite.

## Instalação

Sobreponha os arquivos à versão atual. Não apague `docs/data`, `data/processed` nem os blocos V8.

Depois gere a série de saída, faça commit/push e force a atualização da PWA no celular.
