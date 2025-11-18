#library importing
import ee

# Deciding the area of interest
# AOI = [87.9, 27.6, 88.6, 28.2]  # decide
GEE_FOLDER = 'GEE_Exports'

#Authenticate and initialise Earth Engine
try:
    ee.Initialize(project='ace-connection-447103-v6')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='ace-connection-447103-v6')

# Define area of interest
aoi = ee.Geometry.Polygon([
    # [[87.9, 27.6], [88.6, 27.6], [88.6, 28.2], [87.9, 28.2], [87.9, 27.6]]
    [[88.03, 27.72],[88.06, 27.72],[88.06, 27.75],[88.03, 27.75],[88.03, 27.72]]1.
]) # go


# Sentinel-2 (optical)
s2 = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate('2024-02-01', '2025-09-30')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .median()
    .select(['B2', 'B3', 'B4', 'B8'])
)

# Sentinel-1 (radar)
s1 = (
    ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(aoi)
    .filterDate('2024-02-01', '2025-09-30')
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

print('Export started — check Google Drive', GEE_FOLDER)
