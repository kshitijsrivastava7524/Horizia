# Plot your NDWI mask over your original image
import matplotlib.pyplot as plt
import numpy as np
import rasterio

# Load RGB bands (Sentinel-2 B4, B3, B2)
with rasterio.open("../../data/processed/stack_normalized.tif") as src:
    r = src.read(3)  # B4
    g = src.read(2)  # B3
    b = src.read(1)  # B2
with rasterio.open("../../data/processed/lake_mask.tif") as m:
    mask = m.read(1)

# Make RGB composite
rgb = np.dstack((r, g, b))
rgb = np.clip(rgb / np.percentile(rgb, 99), 0, 1)

plt.figure(figsize=(12,6))
plt.subplot(1,2,1)
plt.imshow(rgb)
plt.title("Sentinel-2 RGB Composite")

plt.subplot(1,2,2)
plt.imshow(rgb)
plt.imshow(mask, cmap='Blues', alpha=0.5)
plt.title("Lake Mask Overlay (blue)")
plt.show()
