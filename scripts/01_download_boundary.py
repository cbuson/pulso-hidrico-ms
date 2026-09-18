"""
01 - Descarga el límite administrativo de Mato Grosso do Sul desde el IBGE.

Fuente: IBGE - Malhas Territoriais
https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html

El IBGE publica las mallas por UF en formato shapefile, comprimidas en .zip.
Este script descarga la malha estadual (nivel UF) y la deja en data/raw/boundary/.

Nota: la URL exacta del IBGE cambia de estructura entre años/versiones de malha.
Verificar el enlace vigente en el portal antes de correr, o usar el servicio
de API de malhas: https://servicodados.ibge.gov.br/api/docs/malhas
"""

import zipfile
from pathlib import Path

import requests

# Código IBGE de Mato Grosso do Sul: 50
UF_CODE = "50"

# API de malhas del IBGE (formato GeoJSON directo, más simple que el shapefile zipado)
URL = f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{UF_CODE}?formato=application/vnd.geo+json&qualidade=intermediaria"

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "boundary"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "ms_boundary.geojson"

    print(f"Descargando límite de MS desde {URL} ...")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()

    out_file.write_bytes(resp.content)
    print(f"Guardado en {out_file}")


if __name__ == "__main__":
    main()
