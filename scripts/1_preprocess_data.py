import rasterio
import numpy as np
import os

INPUT = "../data/raw/horizia_stack1.tif"
OUTPUT = "../data/processed/stack_normalized1.tif"
INPUT = "../data/raw/horizia_stack1.tif"
OUTPUT = "../data/processed/stack_normalized1.tif"
os.makedirs("../data/processed", exist_ok=True)

with rasterio.open(INPUT) as src:
    arr = src.read().astype('float32')
    profile = src.profile


# simple normalization per band
arr_norm = np.zeros_like(arr)
for i in range(arr.shape[0]):
    band = arr[i]
    band_min, band_max = np.nanpercentile(band, (1, 99))
    if band_max - band_min < 1e-6:
        arr_norm[i] = np.zeros_like(band)
    else:
        arr_norm[i] = np.clip((band - band_min) / (band_max - band_min), 0, 1)


profile.update(dtype='float32')
with rasterio.open(OUTPUT, 'w', **profile) as dst:
    dst.write(arr_norm)

print("Normalized pixel values stack saved to:", OUTPUT)
