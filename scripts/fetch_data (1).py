import ee
import os
import requests
from datetime import datetime, timedelta

# ---------------- INIT ----------------
def init_gee():
    try:
        ee.Initialize(project='favorable-array-486408-d1')
    except Exception:
        ee.Authenticate()
        ee.Initialize(project='favorable-array-486408-d1')


# ---------------- SITE CONFIG ----------------
SITES_CONFIG = {
    "site1": [[88.03, 27.72],[88.06, 27.72],[88.06, 27.75],[88.03, 27.75],[88.03, 27.72]],
    "site2": [[88.10, 27.70],[88.15, 27.70],[88.15, 27.75],[88.10, 27.75],[88.10, 27.70]],
    "site3": [[88.20, 27.60],[88.25, 27.60],[88.25, 27.65],[88.20, 27.65],[88.20, 27.60]],
    "site4": [[88.30, 27.50],[88.35, 27.50],[88.35, 27.55],[88.30, 27.55],[88.30, 27.50]],
}


def get_aoi(site):
    if site not in SITES_CONFIG:
        raise ValueError(f"Invalid site: {site}")
    return ee.Geometry.Polygon([SITES_CONFIG[site]])


# ---------------- CORE FETCH FUNCTION ----------------
def fetch_data(site, date):
    print(f"\n[FETCH START] {site} | {date}")

    aoi = get_aoi(site)

    # buffer window (important for data availability)
    start = (date - timedelta(days=14)).strftime('%Y-%m-%d')
    end = (date).strftime('%Y-%m-%d')

    # Sentinel-2
    s2_collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    )

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

    s1 = s1_collection.mean().select(['VV', 'VH']).toFloat()

    # DEM
    dem = ee.Image('USGS/SRTMGL1_003').clip(aoi).select('elevation').toFloat()

    # Stack all bands
    stack = s2.addBands(s1).addBands(dem)

    # Generate download URL
    url = stack.getDownloadURL({
        'scale': 10,
        'region': aoi,
        'format': 'GEO_TIFF'
    })

    # Output path (dynamic per site/date)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(
        BASE_DIR,
        f"../data/raw/{site}/{date.strftime('%Y-%m-%d')}.tif"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Download file
    print(f"[DOWNLOAD] {site} {date}")
    response = requests.get(url, stream=True)

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    print(f"[DONE] Saved → {output_path}")

    return output_path


# ---------------- CLI ENTRY (optional testing) ----------------
# if __name__ == "__main__":
#     init_gee()

#     # test run
#     test_site = "site1"
#     test_date = datetime.now()

#     fetch_data(test_site, test_date)