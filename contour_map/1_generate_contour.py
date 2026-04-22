import os
import numpy as np
import cv2
from osgeo import gdal, ogr, osr
from scipy.interpolate import splprep, splev

# ---------------- PARAMETERS ---------------- #

DEM_FILE = "data/submission_dem.tiff"
OUTPUT_PNG = "generated_maps/contour_final.png"

TEMP_RESAMPLED = ".tmp/dem_resampled.tif"
TEMP_VECTOR = ".tmp/contours.gpkg"

CONTOUR_INTERVAL = 30

FINAL_SIZE = 2310
UPSCALE = 1  # internal render resolution multiplier

LINE_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0)
LINE_THICKNESS = 1

# B-spline (light smoothing only)
SMOOTHING = 0.5
POINT_DENSITY = 3

# DEM resampling factor (CRITICAL)
RESAMPLE_FACTOR = 3  # try 2–4

# -------------------------------------------- #

os.makedirs("generated_maps", exist_ok=True)
os.makedirs(".tmp", exist_ok=True)


# -------- B-SPLINE FUNCTION -------- #

def bspline_smooth(points, smoothing=0.0, num_points=3):
    if len(points) < 4:
        return points

    pts = np.array(points, dtype=np.float32)

    try:
        tck, u = splprep([pts[:, 0], pts[:, 1]], s=smoothing, k=3)
        u_new = np.linspace(0, 1, len(points) * num_points)
        x_new, y_new = splev(u_new, tck)
        return list(zip(x_new, y_new))
    except:
        return points


# -------- STEP 1: RESAMPLE DEM (KEY STEP) -------- #

print("Resampling DEM (cubic interpolation)...")

src_ds = gdal.Open(DEM_FILE)
gt = src_ds.GetGeoTransform()

x_res = gt[1] / RESAMPLE_FACTOR
y_res = abs(gt[5]) / RESAMPLE_FACTOR

gdal.Warp(
    TEMP_RESAMPLED,
    DEM_FILE,
    xRes=x_res,
    yRes=y_res,
    resampleAlg="cubic"
)

dem_ds = gdal.Open(TEMP_RESAMPLED)
band = dem_ds.GetRasterBand(1)

width = dem_ds.RasterXSize
height = dem_ds.RasterYSize
gt = dem_ds.GetGeoTransform()

# -------- STEP 2: GDAL CONTOURS -------- #

print("Generating contours...")

srs = osr.SpatialReference()
srs.ImportFromWkt(dem_ds.GetProjection())

driver = gdal.GetDriverByName("GPKG")
if os.path.exists(TEMP_VECTOR):
    driver.Delete(TEMP_VECTOR)

contour_ds = driver.Create(TEMP_VECTOR, 0, 0, 0, gdal.GDT_Unknown)
layer = contour_ds.CreateLayer("contours", srs, ogr.wkbLineString)

field = ogr.FieldDefn("ELEV", ogr.OFTReal)
layer.CreateField(field)

gdal.ContourGenerate(
    band,
    CONTOUR_INTERVAL,
    0,
    [],
    0,
    0,
    layer,
    0,
    0
)

contour_ds = None
dem_ds = None


# -------- STEP 3: RENDER -------- #

print("Rendering contours...")

TARGET_SIZE = FINAL_SIZE * UPSCALE

img = np.zeros((TARGET_SIZE, TARGET_SIZE, 3), dtype=np.uint8)
img[:] = BACKGROUND_COLOR

scale_x = TARGET_SIZE / width
scale_y = TARGET_SIZE / height

vector_ds = ogr.Open(TEMP_VECTOR)
layer = vector_ds.GetLayer()

for feature in layer:
    geom = feature.GetGeometryRef()
    if geom is None:
        continue

    if geom.GetGeometryType() == ogr.wkbLineString:
        geometries = [geom]
    elif geom.GetGeometryType() == ogr.wkbMultiLineString:
        geometries = [geom.GetGeometryRef(i) for i in range(geom.GetGeometryCount())]
    else:
        continue

    for g in geometries:
        points = g.GetPoints()

        # --- GEO SPACE ---
        geo_points = [(pt[0], pt[1]) for pt in points]

        # --- LIGHT B-SPLINE ---
        if len(geo_points) > 4:
            smooth_geo = bspline_smooth(
                geo_points,
                smoothing=SMOOTHING,
                num_points=POINT_DENSITY
            )
        else:
            smooth_geo = geo_points

        # --- PIXEL SPACE ---
        pixel_points = []
        for x, y in smooth_geo:
            px = (x - gt[0]) / gt[1]
            py = (y - gt[3]) / gt[5]

            px = int(px * scale_x)
            py = int(py * scale_y)

            pixel_points.append((px, py))

        # --- DRAW ---
        if len(pixel_points) > 1:
            cv2.polylines(
                img,
                [np.array(pixel_points, dtype=np.int32)],
                isClosed=False,
                color=LINE_COLOR,
                thickness=LINE_THICKNESS,
                lineType=cv2.LINE_AA
            )

# -------- STEP 4: DOWNSCALE -------- #

print("Downscaling...")

final_img = cv2.resize(
    img,
    (FINAL_SIZE, FINAL_SIZE),
    interpolation=cv2.INTER_AREA
)

cv2.imwrite(OUTPUT_PNG, final_img)

print(f"\n✅ Done! Saved: {OUTPUT_PNG}")
print(f"Final size: {FINAL_SIZE} x {FINAL_SIZE}")