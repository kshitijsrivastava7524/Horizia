import rasterio
import numpy as np
import os

INPUT = "D:/project/Horizia/data/raw/horizia_stack.tif"
OUTPUT = "D:/project/Horizia/data/processed/stack_normalized.tif"
os.makedirs("D:/project/Horizia/data/processed", exist_ok=True)

with rasterio.open(INPUT) as src:
    arr = src.read().astype('float32')
    profile = src.profile


# simple normalization per band
arr_norm = np.zeros_like(arr)
for i in range(arr.shape[0]):
    band = arr[i]
    band_min, band_max = np.nanpercentile(band, (1, 99))
    arr_norm[i] = np.clip((band - band_min) / (band_max - band_min), 0, 1)

profile.update(dtype='float32')
with rasterio.open(OUTPUT, 'w', **profile) as dst:
    dst.write(arr_norm)

print("✅ Normalized stack saved to:", OUTPUT)
