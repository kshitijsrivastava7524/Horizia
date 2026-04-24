import os
import numpy as np
import cv2
from osgeo import gdal, ogr, osr
from scipy.interpolate import splprep, splev


FINAL_SIZE = 2048
RESAMPLE_FACTOR = 3
CONTOUR_INTERVAL = 30


def bspline_smooth(points, smoothing=0.5, num_points=3):
    if len(points) < 4:
        return points

    pts = np.array(points, dtype=np.float32)

    try:
        tck, _ = splprep([pts[:, 0], pts[:, 1]], s=smoothing, k=3)
        u_new = np.linspace(0, 1, len(points) * num_points)
        x_new, y_new = splev(u_new, tck)
        return list(zip(x_new, y_new))
    except:
        return points


def generate_contour(site):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    dem_path = os.path.join(BASE_DIR, f"../data/dem/{site}/dem.tif")
    out_path = os.path.join(BASE_DIR, f"../data/dem/{site}/contour.png")

    tmp_dem = os.path.join(BASE_DIR, ".tmp/dem_resampled.tif")
    tmp_vec = os.path.join(BASE_DIR, ".tmp/contours.gpkg")

    os.makedirs(os.path.dirname(tmp_dem), exist_ok=True)

    print(f"[CONTOUR] {site}")

    # ---------- Resample DEM ----------
    src_ds = gdal.Open(dem_path)
    gt = src_ds.GetGeoTransform()

    gdal.Warp(
        tmp_dem,
        dem_path,
        xRes=gt[1] / RESAMPLE_FACTOR,
        yRes=abs(gt[5]) / RESAMPLE_FACTOR,
        resampleAlg="cubic"
    )

    dem_ds = gdal.Open(tmp_dem)
    band = dem_ds.GetRasterBand(1)

    width = dem_ds.RasterXSize
    height = dem_ds.RasterYSize
    gt = dem_ds.GetGeoTransform()

    # ---------- Contours ----------
    driver = gdal.GetDriverByName("GPKG")
    if os.path.exists(tmp_vec):
        driver.Delete(tmp_vec)

    contour_ds = driver.Create(tmp_vec, 0, 0, 0, gdal.GDT_Unknown)

    srs = osr.SpatialReference()
    srs.ImportFromWkt(dem_ds.GetProjection())

    layer = contour_ds.CreateLayer("contours", srs, ogr.wkbLineString)
    layer.CreateField(ogr.FieldDefn("ELEV", ogr.OFTReal))

    gdal.ContourGenerate(band, CONTOUR_INTERVAL, 0, [], 0, 0, layer, 0, 0)

    contour_ds = None
    dem_ds = None

    # ---------- Render ----------
    img = np.zeros((FINAL_SIZE, FINAL_SIZE, 3), dtype=np.uint8)

    scale_x = FINAL_SIZE / width
    scale_y = FINAL_SIZE / height

    vector_ds = ogr.Open(tmp_vec)
    layer = vector_ds.GetLayer()

    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom is None:
            continue

        geoms = [geom] if geom.GetGeometryType() == ogr.wkbLineString else [
            geom.GetGeometryRef(i) for i in range(geom.GetGeometryCount())
        ]

        for g in geoms:
            pts = g.GetPoints()
            pts = bspline_smooth(pts)

            pixel_pts = []
            for x, y in pts:
                px = int(((x - gt[0]) / gt[1]) * scale_x)
                py = int(((y - gt[3]) / gt[5]) * scale_y)
                pixel_pts.append((px, py))

            if len(pixel_pts) > 1:
                cv2.polylines(
                    img,
                    [np.array(pixel_pts, dtype=np.int32)],
                    False,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

    cv2.imwrite(out_path, img)

    print(f"[DONE] contour → {out_path}")
    return out_path