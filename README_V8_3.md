# Pulso Hídrico MS — V8.3

Correção de robustez para a série GloFAS v4 2001–2025.

## O que aconteceu em 2024

O arquivo anual de 2024 chegou utilizável, mas a validação detectou a ausência do dia hidrológico 2024-12-31. A tentativa de reparo diário foi recusada pelo EWDS com `400 Bad Request / invalid request` para essa combinação.

A V8.3 **não interpola, não inventa e não copia** o valor. Quando o EWDS recusa explicitamente um reparo de 31/12 com `400 invalid request`, a data é registrada como indisponível em:

`data/processed/glofas_v8_unavailable.json`

A série continua com todos os dias realmente disponíveis. A PWA não inclui a data ausente no índice temporal.

## Segurança metodológica

A tolerância é deliberadamente estreita. Só é aceita automaticamente quando:

1. a ausência é exatamente `31/12`;
2. o arquivo anual é estruturalmente válido;
3. o reparo individual foi tentado;
4. o EWDS respondeu explicitamente `400 Bad Request` / `invalid request`.

Qualquer outro dia ausente continua interrompendo o processo para revisão.

## Como continuar

1. Descompacte este ZIP sobre a pasta atual `pulso-hidrico-ms`.
2. Aceite substituir os scripts existentes.
3. **Não apague** os NetCDF, meses processados nem o progresso.
4. Execute novamente `BAIXAR_SERIE_2001_2025.cmd`.

A V8.3 reutiliza 2001–2023, registra a indisponibilidade detectada em 2024, processa 2024 com as datas disponíveis e continua para 2025.

## Auditoria

O `index.json` passa a incluir:

- `unavailable_dates`
- `target_date_count`

Assim, uma lacuna de fonte fica explícita e auditável em vez de ser mascarada.
