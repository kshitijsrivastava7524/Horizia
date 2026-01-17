import rasterio, numpy as np, os
from skimage.morphology import remove_small_objects, remove_small_holes

IN = "../data/processed/stack_normalized.tif"
OUT = "../data/processed/lake_mask.tif"
os.makedirs("../data/processed", exist_ok=True)

with rasterio.open(IN) as src:
    green = src.read(2)  # B3
    nir = src.read(4)    # B8
    profile = src.profile

ndwi = (green - nir) / (green + nir + 1e-6)
mask = ndwi > 0.3   # threshold (tunable)
mask = remove_small_objects(mask.astype(bool), min_size=100)
mask = remove_small_holes(mask, area_threshold=100)
mask = mask.astype('uint8')
with rasterio.open("../data/processed/stack_normalized.tif") as src:
    dem = src.read(7)
mask = np.logical_and(mask, dem < 5500)


profile.update(count=1, dtype='uint8')
with rasterio.open(OUT, 'w', **profile) as dst:
    dst.write(mask, 1)

print("Lake mask generated:", OUT)
