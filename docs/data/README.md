# Datos consumidos por la PWA

La aplicación funciona sin datos reales en **modo demo visual**. En ese modo no se muestra ningún valor hidrológico real.

Para activar **DADOS REAIS**, colocar aquí:

```
docs/data/
├── meta.json
├── boundary.geojson
├── rivers.geojson
└── pulse/
    ├── 2025-02-08.json
    ├── 2025-02-09.json
    └── ...
```

`meta.json` mínimo:

```json
{
  "mode": "real",
  "generated_at": "2026-09-17T00:00:00Z",
  "sources": {
    "boundary": "IBGE",
    "rivers": "HydroRIVERS",
    "discharge": "GloFAS",
    "temperature": "DynQual"
  }
}
```

Cada archivo diario puede usar valores compactos por segmento:

```json
{
  "date": "2025-02-08",
  "summary": {
    "discharge_total_m3s": null,
    "temperature_mean_c": 25.1,
    "discharge_range_m3s": [0, 4200],
    "temperature_range_c": [18, 32]
  },
  "segments": {
    "123456": [210.4, 24.8],
    "123457": [95.2, 25.1]
  },
  "note": "Valores amostrados na grade mais próxima; visualização exploratória."
}
```

El identificador debe coincidir con `HYRIV_ID` de `rivers.geojson`.
