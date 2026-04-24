import ee
import os
import requests
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
CLOUD_THRESHOLD = 40

# SITES_CONFIG = {
#     "site1": [[88.03, 27.72],[88.06, 27.72],[88.06, 27.75],[88.03, 27.75],[88.03, 27.72]],
#     "site2": [[88.10, 27.70],[88.15, 27.70],[88.15, 27.75],[88.10, 27.75],[88.10, 27.70]],
#     "site3": [[88.20, 27.60],[88.25, 27.60],[88.25, 27.65],[88.20, 27.65],[88.20, 27.60]],
#     "site4": [[88.30, 27.50],[88.35, 27.50],[88.35, 27.55],[88.30, 27.55],[88.30, 27.50]],
# }


SITES_CONFIG = {
    # 1. Lhonak region 
    "site1": [[88.03, 27.72],[88.06, 27.72],[88.06, 27.75],[88.03, 27.75],[88.03, 27.72]],

    # 2. Gurudongmar–Khangchung (Sikkim)
    "site2": [[88.68, 28.03],[88.72, 28.03],[88.72, 28.07],[88.68, 28.07],[88.68, 28.03]],

    # 3. Chorabari Tal (Kedarnath)
    "site3": [[79.05, 30.72],[79.08, 30.72],[79.08, 30.75],[79.05, 30.75],[79.05, 30.72]],

    # 4. Imja Tsho (Nepal)
    "site4": [[86.92, 27.87],[86.96, 27.87],[86.96, 27.91],[86.92, 27.91],[86.92, 27.87]],
}

# ---------------- INIT ----------------
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


# ---------------- HELPERS ----------------

def get_aoi(site):
    if site not in SITES_CONFIG:
        raise ValueError(f"Invalid site: {site}")
    return ee.Geometry.Polygon([SITES_CONFIG[site]])


# ---------------- CORE FETCH FUNCTION ----------------

def fetch_data_fun(site, date):
    init_gee()
    print(f"\n[FETCH START] {site} | {date.date()}")

    aoi = get_aoi(site)

    start = (date - timedelta(days=14)).strftime('%Y-%m-%d')
    end   = (date + timedelta(days=1)).strftime('%Y-%m-%d')

    # Sentinel-2
    s2_collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_THRESHOLD))
    )

    if s2_collection.size().getInfo() == 0:
        print(f"[SKIP] No Sentinel-2 data")
        return None

    s2 = s2_collection.median().select(['B2', 'B3', 'B4', 'B8']).toFloat()

    # Sentinel-1
    s1_collection = (
        ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
    )

    if s1_collection.size().getInfo() == 0:
        print(f"[SKIP] No Sentinel-1 data")
        return None

    s1 = s1_collection.mean().select(['VV', 'VH']).toFloat()

    # DEM
    dem = ee.Image('USGS/SRTMGL1_003').clip(aoi).select('elevation').toFloat()

    # Stack
    stack = s2.addBands(s1).addBands(dem)

    # URL
    url = stack.getDownloadURL({
        'scale': 10,
        'region': aoi,
        'format': 'GEO_TIFF'
    })

    # Output path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(
        BASE_DIR,
        f"../data/raw/{site}/{date.strftime('%Y-%m-%d')}.tif"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Skip if already exists
    if os.path.exists(output_path):
        print(f"[SKIP] Already exists: {output_path}")
        return output_path

    print(f"[DOWNLOAD] {output_path}")

    # Download safely
    tmp_path = output_path + ".tmp"

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        os.replace(tmp_path, output_path)

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return None

    print(f"[DONE] Saved -> {output_path}")
    return output_path