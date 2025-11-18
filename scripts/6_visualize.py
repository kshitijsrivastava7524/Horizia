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
S2_PATH   = "../data/processed/stack_normalized1.tif"      # Sentinel-2 composite (normalized)
PROB_PATH = "../data/output/predicted_lake_prob1.tif"      # Model probability output
BIN_PATH  = "../data/output/predicted_lake_binary1.tif"    # Binary mask
AOI_NAME  = "Himalayan Glacial Lakes"
STATIC_ONLY = False  # Set to True if you don't want interactive Leafmap view

# --- New settings for saving plots ---
OUTPUT_DIR = "../data/output/images/"
EXPORT_DPI = 300
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

# -----------------------------------------------------------------
# NEW: Save individual plots as separate 300 DPI PNG files
# -----------------------------------------------------------------
print(f"Saving individual plots to {OUTPUT_DIR} at {EXPORT_DPI} DPI...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Plot 1: Sentinel-2 RGB ---
# Create a new figure and axis for this specific plot
fig_rgb, ax_rgb = plt.subplots(figsize=(10, 10))
ax_rgb.set_title("Sentinel-2 RGB")
ax_rgb.imshow(rgb)
ax_rgb.axis('off')

# Define the output path
rgb_path = os.path.join(OUTPUT_DIR, "visualization_rgb.png")
# Save the figure using settings from your example
plt.savefig(rgb_path, dpi=EXPORT_DPI, bbox_inches='tight', pad_inches=0)
plt.close(fig_rgb)  # Close the figure to free memory
print(f"Saved: {rgb_path}")

# --- Plot 2: Predicted Lake Probability ---
fig_prob, ax_prob = plt.subplots(figsize=(10, 10))
ax_prob.set_title("Predicted Lake Probability")
ax_prob.imshow(prob, cmap='Blues', vmin=0, vmax=1)
ax_prob.axis('off')
prob_path = os.path.join(OUTPUT_DIR, "visualization_probability.png")
plt.savefig(prob_path, dpi=EXPORT_DPI, bbox_inches='tight', pad_inches=0)
plt.close(fig_prob)
print(f"Saved: {prob_path}")

# --- Plot 3: Predicted Binary Mask Overlay ---
fig_overlay, ax_overlay = plt.subplots(figsize=(10, 10))
ax_overlay.set_title("Predicted Binary Mask Overlay")
ax_overlay.imshow(rgb)
ax_overlay.imshow(binary, cmap=ListedColormap(['none', 'cyan']), alpha=0.5)
ax_overlay.axis('off')
overlay_path = os.path.join(OUTPUT_DIR, "visualization_overlay.png")
plt.savefig(overlay_path, dpi=EXPORT_DPI, bbox_inches='tight', pad_inches=0)
plt.close(fig_overlay)
print(f"Saved: {overlay_path}")
print("--- Individual plot saving complete ---")


# ORIGINAL: Static visualization (shows the 1x3 combined plot)

# This block is unchanged and will still display the combined plot
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
# This block is unchanged
# ---------- Interactive map ----------
if not STATIC_ONLY:

    m = leafmap.Map(
        center=[(bounds.top + bounds.bottom) / 2, (bounds.left + bounds.right) / 2],
        zoom=10
    )

    m.add_basemap("SATELLITE")
    m.add_raster(S2_PATH, layer_name="Sentinel-2 RGB", bands=[3,2,1], opacity=0.7)
    m.add_raster(PROB_PATH, layer_name="Lake Probability", colormap="gray", opacity=0.5)

    # Use rio-tiler valid colormap
    m.add_raster(BIN_PATH, layer_name="Predicted Lakes", colormap="blues", opacity=0.6)

    m.add_legend(title="Predicted Lakes", labels=["Lake Regions"], colors=["#00FFFF"])
    m.add_title(AOI_NAME)
    m.show()
