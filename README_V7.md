# Pulso Hídrico MS — V0.7

Atualização metodológica da V0.6.

## Mudança principal

A V0.6 associava cada trecho PIN MS / IMASUL à célula GloFAS mais próxima. A V0.7 separa as funções das duas redes:

- **PIN MS / IMASUL** — contexto hidrográfico fino.
- **GloFAS v4 / LISFLOOD** — rede dinâmica da descarga.

A rede dinâmica é construída diretamente a partir dos mapas auxiliares oficiais **Upstream Area** e **Local Drain Direction (LDD)** do GloFAS v4. São usados pixels com área drenada >= 250 km². A descarga diária é então amostrada na própria célula do modelo, evitando o pareamento provisório PIN→GloFAS por vizinho mais próximo.

## Aplicação sobre a pasta atual

Extraia o ZIP por cima da pasta atual `pulso-hidrico-ms`. O pacote não contém seus `rivers.geojson`, `boundary.geojson` nem os NetCDF diários já baixados.

Depois execute:

```text
PREPARAR_V7_GLOFAS.cmd
```

O processo:

1. baixa uma única vez `uparea_glofas_v4_0.nc` (~87 MB) e `ldd_glofas_v4_0.nc` (~21 MB);
2. recorta os mapas para MS;
3. cria `docs/data/glofas_network.geojson`;
4. faz backup dos JSON V6;
5. reutiliza os quatro NetCDF de 2001, 2010, 2020 e 2025;
6. recria os quatro JSON na rede nativa GloFAS;
7. executa uma auditoria automática.

## Fontes metodológicas

- CEMS / ECMWF — GloFAS Auxiliary Data, Upstream Area e LDD v4.
- GloFAS v4 — resolução 0,05° e rede LISFLOOD.
- PIN MS / IMASUL — hidrografia de contexto.

A descarga GloFAS é **modelada**, não uma medição fluviométrica in situ.
