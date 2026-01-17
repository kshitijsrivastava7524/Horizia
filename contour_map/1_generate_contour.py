import os
import matplotlib.pyplot as plt
import geopandas as gpd
from osgeo import gdal, osr, ogr
# from gdal import gdal
# from osgeo import osr

# --- 1. SET YOUR PARAMETERS HERE ---

# Input DEM file you downloaded from Google Earth Engine
# DEM_FILE = 'data/dem_for_qgis.tiff'  #OLD
DEM_FILE = 'data/submission_dem.tiff'

# Where to save the final PNG
# OUTPUT_PNG = 'generated_maps/default-dark-mode-100-1.png' #OLD
OUTPUT_PNG = 'generated_maps/submission-dark-mode-30-1.png'

# Temporary file to store the contours (will be deleted)
TEMP_VECTOR_FILE = '.tmp/temp_contours.gpkg' # GPKG is a modern format

# Your settings
CONTOUR_INTERVAL = 30
LINE_WIDTH = 0.3   # This is in 'points' (matplotlib's unit)
LINE_COLOR = '#ffffff' #'#b2b2b2'
BACKGROUND_COLOR = '#000000'
EXPORT_DPI = 300

# --- 2. THE SCRIPT ---

def generate_contour_map():
    print(f"--- Starting Standalone Contour Generation ---")
    
    # --- 3. Generate Contours (using GDAL) ---
    print(f"Opening DEM: {DEM_FILE}")
    src_ds = gdal.Open(DEM_FILE)
    if src_ds is None:
        print(f"!!! ERROR: Could not open {DEM_FILE}. Make sure it's in the same folder.")
        return

    # Create the output vector file
    srs = osr.SpatialReference()
    srs.ImportFromWkt(src_ds.GetProjection())
    dst_driver = gdal.GetDriverByName('GPKG')
    dst_ds = dst_driver.Create(TEMP_VECTOR_FILE, 0, 0, 0, gdal.GDT_Unknown)
    dst_layer = dst_ds.CreateLayer('contours', srs, ogr.wkbLineString)
    
    # Add the 'ELEV' field
    field_defn = ogr.FieldDefn('ELEV', ogr.OFTReal)
    dst_layer.CreateField(field_defn)

    # Get the raster band
    src_band = src_ds.GetRasterBand(1)

    # --- FIX: Get the NoData value from the DEM ---
    nodata_val = src_band.GetNoDataValue()
    use_nodata_flag = 0  # 0 = False

    if nodata_val is not None:
        print(f"Found NoData value in DEM: {nodata_val}")
        use_nodata_flag = 1  # 1 = True
    else:
        print("Warning: No NoData value found in DEM.")
        nodata_val = 0 # Set a default, though it won't be used

    print(f"Generating contours at {CONTOUR_INTERVAL}m interval...")
    # Run the contour algorithm
    gdal.ContourGenerate(
        src_band,                 # Input band
        CONTOUR_INTERVAL,         # Contour interval
        0,                        # Offset
        [],                       # No fixed levels
        use_nodata_flag,          # <-- FIX: Tells GDAL to use the NoData value
        nodata_val,               # <-- FIX: Passes the actual NoData value
        dst_layer,                # Output layer
        0,                        # Index of elevation field
        0                         # Index of ID field
    )
    # Close files
    src_ds = None
    dst_ds = None
    print(f"Temporary contours saved to {TEMP_VECTOR_FILE}")

    # --- 4. Plot and Style (using GeoPandas & Matplotlib) ---
    print("Styling and plotting the image...")
    
    # Read the vector file we just created
    contours = gpd.read_file(TEMP_VECTOR_FILE)

    # Create a plot figure
    # We set the fig and ax background to black
    fig, ax = plt.subplots(1, 1, figsize=(10, 10), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # Plot the contour lines
    contours.plot(
        ax=ax, 
        color=LINE_COLOR, 
        linewidth=LINE_WIDTH
    )

    # --- 5. Crop and Export (The final image) ---
    
    # Turn off all axes, labels, and borders
    ax.set_axis_off()

    # This is the magic: save with bbox_inches='tight' and pad_inches=0
    # This automatically crops the image to your data, removing all padding.
    print(f"Saving final image to {OUTPUT_PNG} at {EXPORT_DPI} DPI...")
    plt.savefig(
        OUTPUT_PNG,
        dpi=EXPORT_DPI,
        facecolor=BACKGROUND_COLOR,
        bbox_inches='tight',
        pad_inches=0
    )
    
    print("\n--- SUCCESS! ---")

    # # --- 6. Clean Up ---
    # print("Cleaning up temporary files...")
    # # Delete the temporary .gpkg file and its sidecar files
    # if os.path.exists(TEMP_VECTOR_FILE):
    #     os.remove(TEMP_VECTOR_FILE)
    # for ext in ['.gpkg-shm', '.gpkg-wal']:
    #     if os.path.exists(TEMP_VECTOR_FILE + ext):
    #         os.remove(TEMP_VECTOR_FILE + ext)
    print("Done.")

# Run the function
if __name__ == "__main__":
    generate_contour_map()