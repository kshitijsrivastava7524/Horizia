import rasterio, numpy as np, os
from skimage.morphology import remove_small_objects, remove_small_holes

IN = "../data/processed/stack_normalized1.tif"
OUT = "../data/processed/lake_mask.tif"
os.makedirs("../data/processed", exist_ok=True)

with rasterio.open(IN) as src:
    green = src.read(2)   # B3
    nir   = src.read(4)   # B8
    vv    = src.read(5)   # Sentinel-1 VV
    vh    = src.read(6)   # Sentinel-1 VH
    dem   = src.read(7)   # elevation
    profile = src.profile

ndwi = (green - nir) / (green + nir + 1e-6)
mask = ndwi > 0.3   # threshold (tunable)
radar_water = np.logical_or(vv < 0.35, vh < 0.25)
mask = np.logical_or(mask, radar_water)

mask = remove_small_objects(mask.astype(bool), min_size=100)
mask = remove_small_holes(mask, area_threshold=100)
mask = mask.astype('uint8')
with rasterio.open("../data/processed/stack_normalized1.tif") as src:
    dem = src.read(7)
mask = np.logical_and(mask, dem < 5500)


profile.update(count=1, dtype='uint8')
with rasterio.open(OUT, 'w', **profile) as dst:
    dst.write(mask, 1)

print("Lake mask generated:", OUT)



# import rasterio
# import numpy as np
# import os
# from skimage.morphology import remove_small_objects, remove_small_holes

# IN  = "../data/processed/stack_normalized1.tif"
# OUT = "../data/processed/lake_mask.tif"
# os.makedirs("../data/processed", exist_ok=True)

# with rasterio.open(IN) as src:
#     green = src.read(2)   # B3
#     nir   = src.read(4)   # B8
#     vv    = src.read(5)   # Sentinel-1 VV
#     vh    = src.read(6)   # Sentinel-1 VH
#     dem   = src.read(7)   # elevation
#     profile = src.profile

# # ---------- NDWI (optical) ----------
# ndwi = (green - nir) / (green + nir + 1e-6)
# optical_water = ndwi > 0.2

# # ---------- Radar water index ----------
# # water has very low backscatter in both VV and VH
# # your stack is normalized 0-1 so we convert back
# # to approximate dB range for thresholding
# # normalized 0-1 → original was roughly -30 to 0 dB
# # so threshold 0.5 in normalized ≈ -15 dB in real

# radar_water = np.logical_and(vv < 0.35, vh < 0.25)
# # vv < 0.35 → low VV backscatter → likely water
# # vh < 0.25 → low VH backscatter → confirms water

# # ---------- Combine optical + radar ----------
# # UNION: pixel is water if EITHER detects it
# # catches lakes missed by clouds (radar saves them)
# # combined = np.logical_or(optical_water, radar_water)

# # INTERSECTION: pixel must be confirmed by BOTH
# # stricter, fewer false positives
# combined = np.logical_and(optical_water, radar_water)

# # ---------- Elevation filter ----------
# elev_filter = dem < 5500
# mask = np.logical_and(combined, elev_filter)

# # ---------- Clean up ----------
# mask = remove_small_objects(mask.astype(bool), min_size=100)
# mask = remove_small_holes(mask, area_threshold=100)
# mask = mask.astype('uint8')

# # ---------- Save ----------
# profile.update(count=1, dtype='uint8')
# with rasterio.open(OUT, 'w', **profile) as dst:
#     dst.write(mask, 1)

# print("Lake mask generated:", OUT)

# # ---------- Stats ----------
# total = mask.size
# lake  = np.sum(mask)
# print(f"Lake pixels:     {lake:,}")
# print(f"Lake coverage:   {(lake/total)*100:.2f}%")