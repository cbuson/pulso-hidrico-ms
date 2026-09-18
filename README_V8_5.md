# Pulso Hídrico MS · V0.8.5

Atualização de interface e representação cartográfica sobre a V8 existente.

## Mudanças

- remove completamente o modo **Teste**; a interface trabalha apenas com dados reais processados;
- mantém a geometria original dos rios **PIN MS / IMASUL** como representação visível principal;
- a rede nativa GloFAS/LISFLOOD continua sendo usada internamente para a descarga, mas deixa de aparecer como linhas escalonadas no mapa;
- transfere cartograficamente a descarga da célula fluvial GloFAS mais próxima para os segmentos PIN MS;
- reforça a escala de espessura com transformação logarítmica para que as mudanças sejam visíveis;
- integra **temperatura da água como climatologia mensal DynQual 1980–2019**;
- `Reproduzir` continua avançando mês a mês; consulta manual por setas, calendário e linha do tempo continua diária;
- atualiza `?` e `i`, mantendo autoria de **Carlos Busón Buesa** e **Sandra Gabas**.

## Instalação

Descompacte esta atualização por cima da pasta atual `pulso-hidrico-ms` e aceite substituir os arquivos de `docs`.

Ela não apaga `docs/data/pulse-v8`, os NetCDF GloFAS, `rivers.geojson`, `boundary.geojson` nem `glofas_network.geojson`.

## Temperatura

Execute uma única vez:

`PREPARAR_TEMPERATURA_DYNQUAL.cmd`

O script baixa o arquivo oficial `waterTemperature_monthly_1980_2019_30min.nc` (~88,6 MB) do conjunto DynQual no Zenodo, calcula a climatologia mensal para a geometria dos rios de MS e gera:

`docs/data/temperature-climatology.json`

Fonte: Jones et al., DynQual v1.0, Zenodo DOI `10.5281/zenodo.10155484`.

A temperatura exibida é **climatologia mensal**, não observação diária. Para 2020–2025 ela continua sendo a referência climatológica 1980–2019 do mês correspondente.

## Leitura do mapa

- geometria: PIN MS / IMASUL;
- espessura: descarga modelada GloFAS v4;
- cor: climatologia mensal da temperatura da água DynQual;
- limite: IBGE / arquivo local do projeto.

A transferência de descarga para a geometria PIN MS é uma operação cartográfica para facilitar a leitura. Não converte cada segmento visível em uma estação de medição.
