import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os

# --- 1. SET YOUR PARAMETERS HERE ---

# Input files (Update these paths to match your folder structure)
CONTOUR_MAP_FILE = 'generated_maps/submission-dark-mode-30-1.png'
LAKE_OVERLAY_FILE = '../data/output/visualization_lakes_red_transparent.png'

# Output file
OUTPUT_FILE = 'generated_maps/submission_combined_contour_lake_map.png'

# Settings from your other script
BACKGROUND_COLOR = '#000000' # Black background
EXPORT_DPI = 300

# --- 2. THE SCRIPT ---
print("--- Starting Image Overlay ---")

# Create output directory if it doesn't exist
output_dir = os.path.dirname(OUTPUT_FILE)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}")

# --- 3. Read the images ---
print(f"Reading base map: {CONTOUR_MAP_FILE}")
contour_img = mpimg.imread(CONTOUR_MAP_FILE)

print(f"Reading overlay: {LAKE_OVERLAY_FILE}")
lake_img = mpimg.imread(LAKE_OVERLAY_FILE)

# --- 4. Check Image Sizes ---
# This is a crucial check. If the images were created with 'bbox_inches=tight'
# from the same data, they should have identical pixel dimensions.
if contour_img.shape[:2] != lake_img.shape[:2]:
    print("!!! WARNING: Image shapes differ! Alignment may be incorrect. !!!")
    print(f"  Contour map shape: {contour_img.shape}")
    print(f"  Lake mask shape:   {lake_img.shape}")
    print("The script will continue, but you may need to resize one image.")

# --- 5. Plot and Overlay ---
print("Creating plot and overlaying images...")

# Create a plot figure, just like in your contour script
# The figsize is arbitrary since 'bbox_inches=tight' will crop it
fig, ax = plt.subplots(figsize=(10, 10), facecolor=BACKGROUND_COLOR)
ax.set_facecolor(BACKGROUND_COLOR)

# Plot the base contour map (layer 1)
ax.imshow(contour_img)

# Plot the lake overlay on top (layer 2)
# Matplotlib automatically respects the alpha channel (transparency)
ax.imshow(lake_img)

# --- 6. Crop and Export ---
ax.set_axis_off()

print(f"Saving final image to {OUTPUT_FILE} at {EXPORT_DPI} DPI...")
plt.savefig(
    OUTPUT_FILE,
    dpi=EXPORT_DPI,
    facecolor=BACKGROUND_COLOR,
    bbox_inches='tight',
    pad_inches=0
)

plt.close(fig) # Close the figure to free memory
print("\n--- SUCCESS! ---")
print("Done.")