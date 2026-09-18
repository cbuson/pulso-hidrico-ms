"""
02 - Descarga y descomprime HydroRIVERS v1.0 para South America.

Fuente oficial HydroSHEDS:
https://www.hydrosheds.org/products/hydrorivers
Archivo oficial:
https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_sa_shp.zip
"""

import zipfile
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / "data" / "raw" / "hydrorivers"
ZIP_NAME = "HydroRIVERS_v10_sa_shp.zip"
URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_sa_shp.zip"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / ZIP_NAME
    if not zip_path.exists():
        print("Descargando HydroRIVERS South America (~95 MB) …")
        with requests.get(URL, stream=True, timeout=(30, 600)) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with zip_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            print(f"  {100 * done / total:5.1f}%", end="\r")
        print(f"\nGuardado {zip_path}")
    else:
        print(f"Reutilizando {zip_path}")

    extract_dir = RAW_DIR / "shp"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    print(f"HydroRIVERS listo en {extract_dir}")


if __name__ == "__main__":
    main()
