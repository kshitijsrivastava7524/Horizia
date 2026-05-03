#library importing
import ee
import os 
import requests
import rasterio
GEE_FOLDER = 'GEE_Exports'

#Authenticate and initialise Earth Engine
try:
    ee.Initialize(project='favorable-array-486408-d1')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='favorable-array-486408-d1')

# Define area of interest
aoi = ee.Geometry.Polygon([
        [78.5, 30.8],
        [79.5, 30.8],
        [79.5, 31.7],
        [78.5, 31.7],
        [78.5, 30.8]
])


# Sentinel-2 (optical)
s2 = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate('2024-02-01', '2026-03-30')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .reduce(ee.Reducer.percentile([25]))
    .select(['B2', 'B3', 'B4', 'B8','B11'])
)

# Sentinel-1 (radar)
s1 = (
    ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(aoi)
    .filterDate('2024-02-01', '2026-03-30')
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .mean()
    .select(['VV', 'VH'])
)

# DEM
dem = ee.Image('USGS/SRTMGL1_003').clip(aoi).select('elevation')

# Harmonize datatypes
s2 = s2.toFloat()
s1 = s1.toFloat()
dem = dem.toFloat()

# Stack bands (all float32)
stack = s2.addBands(s1).addBands(dem)

# # Generate download URL
# url = stack.getDownloadURL({
#     'scale': 10,
#     'region': aoi,
#     'format': 'GEO_TIFF'
# })

# print("Download URL generated")

# # Download locally
# output_path = "../data/raw/horizia_stack.tif"
# os.makedirs(os.path.dirname(output_path), exist_ok=True)

# response = requests.get(url, stream=True)
# response.raise_for_status()   # ← missing in your current code

# with open(output_path, 'wb') as f:
#     for chunk in response.iter_content(chunk_size=1024):
#         if chunk:
#             f.write(chunk)

# # verify immediately after download
# with rasterio.open(output_path) as src:
#     print("CRS:      ", src.crs)
#     print("Transform:", src.transform)
#     print("Bounds:   ", src.bounds)
#     print("Shape:    ", src.height, src.width)
#     print("Bands:    ", src.count)
#     if src.crs is None:
#         raise RuntimeError("Downloaded file has no CRS — GEE export issue")

# print(f"File downloaded locally: {output_path}")
# Export to Google Drive
task = ee.batch.Export.image.toDrive(
    image=stack,
    description='horizia_stack_export',
    folder=GEE_FOLDER,
    fileNamePrefix='horizia_stack',
    scale=10,
    region=aoi.getInfo()['coordinates'],
    maxPixels=1e10
)
task.start()

print('Export started — check Google Drive →', GEE_FOLDER)