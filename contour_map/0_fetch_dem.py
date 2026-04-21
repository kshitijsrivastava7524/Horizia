import ee
import requests

# Authenticate and initialise Earth Engine
# This will ask YOU to log in with your own Google account
try:
    ee.Initialize(project='horizia-dem-project-478309') #ace-connection-447103-v6')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='horizia-dem-project-478309') #ace-connection-447103-v6')

# Define area of interest (Same as your team's) (OLD)
# aoi = ee.Geometry.Polygon([
#     [[87.9, 27.6], [88.6, 27.6], [88.6, 28.2], [87.9, 28.2], [87.9, 27.6]]
# ])

aoi = ee.Geometry.Polygon([[88.03, 27.72],
 [88.06, 27.72],
 [88.06, 27.75],
 [88.03, 27.75],
 [88.03, 27.72]])

# 1. Get the DEM
dem_native = ee.Image('USGS/SRTMGL1_003').clip(aoi).select('elevation')

# Force "smooth" resampling BEFORE the export.
dem = dem_native.resample('bilinear')

# 2. Harmonize datatype (good practice)
dem = dem.toFloat()

# --- MODIFIED PART: Get a direct download URL ---

print("Preparing your DEM for direct download...")
print("This may take a minute. The script will 'hang' while it works...")

try:
    # Define the download parameters
    download_params = {
        'scale': 10,  # 10m is the native scale for SRTM
        'region': aoi.getInfo()['coordinates'],
        'format': 'GeoTIFF', # We want a GeoTIFF file
        'fileName': 'dem_aligned_10m'
    }

    # This is a SYNCHRONOUS request. The script will wait for GEE
    # to process the file and generate a link.
    url = dem.getDownloadURL(download_params)
    response = requests.get(url)

    with open('data/submission_dem.tiff', 'wb') as f:
        f.write(response.content)
    
    # print("\n--- DOWNLOAD READY ---")
    # print("COPY and PASTE this URL into your browser to download the file:")
    # print(f"\n{url}\n")
    # print("(This link will expire in about 3 days)")

except ee.ee_exception.EEException as e:
    print("\nAn error occurred. The region might be too large for a direct download.")
    print(f"Error: {e}")
    print("\nIf this fails, the 'toDrive' method is more reliable for large areas.")