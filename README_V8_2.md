# Pulso Hídrico MS — V8.2

Correção temporal para GloFAS Historical `average_river_discharge_in_the_last_24_hours`.

O campo NetCDF `valid_time` representa o **fim** do período médio de 24 horas. Assim, uma solicitação do dia `2001-01-01` pode chegar com `valid_time = 2001-01-02 00:00`. Para a interface do Pulso Hídrico, o valor pertence ao dia coberto pela média, portanto:

`dia_hidrologico = valid_time - 1 dia`

A V8.1 interpretava `valid_time` como se fosse a data civil do valor, por isso enxergava 364 dias em 2001 e tentava reparar 01/01. A V8.2 corrige essa semântica e mantém o reparo automático somente para ausências realmente presentes depois da normalização temporal.

## Uso

1. Descompactar este patch sobre a pasta atual `pulso-hidrico-ms` e substituir os arquivos existentes.
2. **Não apagar** `data/processed/glofas_v8_yearly/glofas_ms_v4_2001.nc`.
3. Executar novamente `BAIXAR_SERIE_2001_2025.cmd`.

O arquivo anual já baixado deve ser reaproveitado. Se ele contiver o ciclo completo Jan-2001 solicitado, a validação deverá passar como 365/365 após a conversão temporal, sem novo download anual.

Se existir `data/processed/glofas_v8_yearly/_gaps/2001/2001-01-01.nc` criado pela V8.1, pode ficar no lugar: a V8.2 o deduplica pelo dia hidrológico. Não é necessário apagar.
