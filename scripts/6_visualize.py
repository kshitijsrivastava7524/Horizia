import rasterio
import numpy as np
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
from rasterio.plot import reshape_as_image
from matplotlib.colors import ListedColormap
import os

# ------------------------------
# CONFIG
# ------------------------------
S2_PATH   = "../data/processed/stack_normalized.tif"      # Sentinel-2 composite (normalized)
PROB_PATH = "../data/output/predicted_lake_prob.tif"      # Model probability output
BIN_PATH  = "../data/output/predicted_lake_binary.tif"    # Binary mask
AOI_NAME  = "Himalayan Glacial Lakes"
STATIC_ONLY = False  # Set to True if you don't want interactive Leafmap view
# ------------------------------

# ---------- Verify existence ----------
for path in [S2_PATH, PROB_PATH, BIN_PATH]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

# ---------- Read Sentinel-2 composite ----------
with rasterio.open(S2_PATH) as src:
    # use RGB bands (3,2,1)
    rgb = np.stack([src.read(3), src.read(2), src.read(1)], axis=-1)
    rgb = np.clip(rgb, 0, 1)
    transform = src.transform
    crs = src.crs
    bounds = src.bounds

# ---------- Read model predictions ----------
with rasterio.open(PROB_PATH) as src:
    prob = src.read(1)
with rasterio.open(BIN_PATH) as src:
    binary = src.read(1)

lake_pixels = np.sum(binary)
print(f"Loaded Sentinel RGB: {rgb.shape}, Prob range: {prob.min():.3f}-{prob.max():.3f}, Lake pixels: {lake_pixels:,}")

# ---------- Static visualization ----------
plt.figure(figsize=(10, 10))
plt.subplot(1, 3, 1)
plt.title("Sentinel-2 RGB")
plt.imshow(rgb)
plt.axis('off')

plt.subplot(1, 3, 2)
plt.title("Predicted Lake Probability")
plt.imshow(prob, cmap='Blues', vmin=0, vmax=1)
plt.axis('off')

plt.subplot(1, 3, 3)
plt.title("Predicted Binary Mask Overlay")
plt.imshow(rgb)
plt.imshow(binary, cmap=ListedColormap(['none', 'cyan']), alpha=0.5)
plt.axis('off')

plt.tight_layout()
plt.show()

# ---------- Interactive map ----------
if not STATIC_ONLY:
    print("Launching interactive Leafmap window...")
    m = leafmap.Map(
        center=[(bounds.top + bounds.bottom) / 2, (bounds.left + bounds.right) / 2],
        zoom=10
    )
    m.add_basemap("SATELLITE")
    m.add_raster(S2_PATH, layer_name="Sentinel-2 RGB", bands=[3, 2, 1], opacity=0.7)
    m.add_raster(PROB_PATH, layer_name="Lake Probability", colormap="Blues", opacity=0.5)
    m.add_raster(BIN_PATH, layer_name="Predicted Lakes", colormap="cyan", opacity=0.6)
    m.add_legend(title="Predicted Lakes", labels=["Lake Regions"], colors=["#00FFFF"])
    m.add_title(AOI_NAME)
    m.show()
