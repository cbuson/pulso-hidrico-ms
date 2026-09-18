"""
04 - Descarga la serie mensual global de temperatura del agua de DynQual.

Se usa como CLIMATOLOGÍA MENSUAL, no como temperatura observada en 2025/2026.
Dataset oficial 1980-2019, 5 arcmin (~10 km):
https://zenodo.org/records/14673871

El archivo es grande (~2 GB). Solo es necesario descargarlo una vez; el paso 05
lo recorta a Mato Grosso do Sul.
"""

from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "raw" / "dynqual"
RECORD = "14673871"
FILENAME = "waterTemperature_monthlyAvg_1980_2019.nc"
URL = f"https://zenodo.org/api/records/{RECORD}/files/{FILENAME}/content"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / FILENAME
    if out.exists() and out.stat().st_size > 0:
        print(f"Ya existe {out}; se reutiliza.")
        return
    print("Descargando DynQual water temperature 1980-2019. Archivo global grande (~2 GB).")
    with requests.get(URL, stream=True, timeout=(30, 1200)) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with out.open("wb") as f:
            for chunk in r.iter_content(chunk_size=4 * 1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"  {100 * done / total:5.1f}%", end="\r")
    print(f"\nGuardado {out}")


if __name__ == "__main__":
    main()
