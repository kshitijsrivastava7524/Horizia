# create tiles to train model
import os
import numpy as np
import rasterio
from rasterio.windows import Window
from math import ceil
from sklearn.model_selection import train_test_split

def tile_and_save(img_path, mask_path, out_dir, patch=256, val_split=0.2, random_seed=42):
    os.makedirs(out_dir, exist_ok=True)
    img_out_train = os.path.join(out_dir, "train", "images")
    mask_out_train = os.path.join(out_dir, "train", "masks")
    img_out_val = os.path.join(out_dir, "val", "images")
    mask_out_val = os.path.join(out_dir, "val", "masks")

    for p in [img_out_train, mask_out_train, img_out_val, mask_out_val]:
        os.makedirs(p, exist_ok=True)

    with rasterio.open(img_path) as src_img, rasterio.open(mask_path) as src_mask:
        H, W = src_img.height, src_img.width
        bands = src_img.count
        nH, nW = ceil(H / patch), ceil(W / patch)

        tile_paths = []
        idx = 0
        for i in range(nH):
            for j in range(nW):
                window = Window(j*patch, i*patch, patch, patch).intersection(Window(0,0,W,H))
                img = src_img.read(window=window).astype('float32')
                mask = src_mask.read(1, window=window).astype('uint8')

                # pad if at edge
                ph = patch - img.shape[1]
                pw = patch - img.shape[2]
                if ph>0 or pw>0:
                    img = np.pad(img, ((0,0),(0,ph),(0,pw)), mode='constant', constant_values=0)
                    mask = np.pad(mask, ((0,ph),(0,pw)), mode='constant', constant_values=0)

                # skip tiles with no data (optional)
                if img.sum() == 0:
                    idx += 1
                    continue

                img_file = f"tile_{idx:06d}.npy"
                mask_file = f"mask_{idx:06d}.npy"
                tmp_img_path = os.path.join(out_dir, "all_tiles_images", img_file)
                tmp_mask_path = os.path.join(out_dir, "all_tiles_masks", mask_file)
                os.makedirs(os.path.dirname(tmp_img_path), exist_ok=True)
                os.makedirs(os.path.dirname(tmp_mask_path), exist_ok=True)
                np.save(tmp_img_path, img)
                np.save(tmp_mask_path, mask)
                tile_paths.append((tmp_img_path, tmp_mask_path))
                idx += 1

    if len(tile_paths) == 0:
        raise SystemExit("No tiles created. Check input paths and AOI.")

    # train/val split
    img_paths = [p[0] for p in tile_paths]
    mask_paths = [p[1] for p in tile_paths]
    train_imgs, val_imgs, train_masks, val_masks = train_test_split(
        img_paths, mask_paths, test_size=val_split, random_state=random_seed
    )

    # move files
    def move_files(src_list, dst_img_dir, dst_mask_dir):
        for s_img in src_list:
            base = os.path.basename(s_img)
            i_mask = s_img.replace("all_tiles_images", "all_tiles_masks").replace("tile_", "mask_")
            dst_img_path = os.path.join(dst_img_dir, base)
            dst_mask_path = os.path.join(dst_mask_dir, os.path.basename(i_mask))
            os.replace(s_img, dst_img_path)
            os.replace(i_mask, dst_mask_path)

    move_files(train_imgs, img_out_train, mask_out_train)
    move_files(val_imgs, img_out_val, mask_out_val)

    print(f"Created {len(train_imgs)} train tiles and {len(val_imgs)} val tiles.")
    print("Train images ->", img_out_train)
    print("Val images ->", img_out_val)


STACK = "../data/processed/stack_normalized.tif"
MASK = "../data/processed/lake_mask.tif"
OUT = "../data/tiles"
PATCH = 256
VAL_SPLIT = 0.2

tile_and_save(STACK, MASK, OUT, patch=PATCH, val_split=VAL_SPLIT)
