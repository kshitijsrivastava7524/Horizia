import rasterio, os, numpy as np
from rasterio.windows import Window
from math import ceil

IN_IMG = "D:/project/Horizia/data/processed/stack_normalized.tif"
IN_MASK = "D:/project/Horizia/data/processed/lake_mask.tif"
OUT_IMG_DIR = "D:/project/Horizia/data/train/images"
OUT_MASK_DIR = "D:/project/Horizia/data/train/masks"
PATCH = 256

os.makedirs(OUT_IMG_DIR, exist_ok=True)
os.makedirs(OUT_MASK_DIR, exist_ok=True)

with rasterio.open(IN_IMG) as img_src, rasterio.open(IN_MASK) as mask_src:
    H, W = img_src.height, img_src.width
    nH, nW = ceil(H / PATCH), ceil(W / PATCH)
    idx = 0
    for i in range(nH):
        for j in range(nW):
            win = Window(j*PATCH, i*PATCH, PATCH, PATCH).intersection(Window(0,0,W,H))
            img = img_src.read(window=win)
            mask = mask_src.read(1, window=win)

            np.save(os.path.join(OUT_IMG_DIR, f"tile_{idx:04d}.npy"), img)
            np.save(os.path.join(OUT_MASK_DIR, f"mask_{idx:04d}.npy"), mask)
            idx += 1

print(f"✅ Created {idx} image tiles.")
