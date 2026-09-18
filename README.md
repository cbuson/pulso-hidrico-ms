# Pulso Hídrico MS — v0.6.2

Correção da configuração da API para o **CEMS Early Warning Data Store (EWDS)**.

GloFAS não é servido pelo endpoint do Climate Data Store (CDS). O endpoint correto é:

`https://ewds.climate.copernicus.eu/api`

## Teste GloFAS

1. Execute `1_CONFIGURAR_EWDS.cmd`.
2. Copie o token da sua conta EWDS e aceite a licença do GloFAS Historical.
3. Execute `2_BAIXAR_GLOFAS_TESTE.cmd`.
4. O teste baixa somente 08/02 de 2001, 2010, 2020 e 2025.
5. Recarregue a PWA e use o modo **Real**.

A geometria PIN MS/IMASUL permanece separada dos valores temporais GloFAS.
