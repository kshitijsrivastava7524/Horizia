
import ee
import os
import requests

from fetch_data import SITES_CONFIG  # reuse same AOIs


_gee_initialized = False

def init_gee():
    global _gee_initialized
    if _gee_initialized:
        return
    try:
        ee.Initialize(project='favorable-array-486408-d1')
    except Exception:
        ee.Authenticate()
        ee.Initialize(project='favorable-array-486408-d1')
    _gee_initialized = True

def fetch_dem(site):
    init_gee()

    print(f"[DEM FETCH] {site}")

    coords = SITES_CONFIG[site]
    aoi = ee.Geometry.Polygon([coords])

    dem = (
        ee.Image('USGS/SRTMGL1_003')
        .clip(aoi)
        .select('elevation')
        .resample('bilinear')
        .toFloat()
    )

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    out_path = os.path.join(BASE_DIR, f"../data/dem/{site}/dem.tif")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if os.path.exists(out_path):
        print(f"[SKIP] DEM exists: {out_path}")
        return out_path

    url = dem.getDownloadURL({
        'region': aoi.getInfo()['coordinates'],
        'format': 'GeoTIFF'
    })

    response = requests.get(url)

    with open(out_path, 'wb') as f:
        f.write(response.content)

    print(f"[DONE] DEM saved → {out_path}")
    return out_path