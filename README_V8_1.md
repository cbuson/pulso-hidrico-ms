# Pulso Hídrico MS — V8.1

Correção para respostas anuais do EWDS que chegam com 364/365 ou 365/366 dias.

## O que mudou

A V8 rejeitava o ano inteiro se faltasse um único dia. A V8.1 não reduz o rigor: detecta a data ausente, preserva o NetCDF anual, baixa apenas o dia faltante pela API EWDS e combina o reparo durante o processamento.

## Como aplicar

1. Extraia este ZIP sobre a pasta atual do projeto V8, substituindo os arquivos quando o Windows perguntar.
2. Não apague `data/processed/glofas_v8_yearly/glofas_ms_v4_2001.nc`.
3. Execute novamente `BAIXAR_SERIE_2001_2025.cmd`.

Para 2001, o programa deverá informar qual data está faltando, baixar somente essa data e então continuar com o processamento de 2001 e os anos seguintes.
