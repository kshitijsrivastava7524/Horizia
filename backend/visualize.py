import os
import numpy as np
import rasterio
from PIL import Image
import cv2

def generate_images(stack_path, prob_path, binary_path, site, date):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    date_str = date.strftime("%Y-%m-%d")

    out_dir = os.path.join(BASE_DIR, f"../data/output/images/{site}/{date_str}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[VISUALIZE] {site} {date_str}")

    # ---------- Load data ----------
    with rasterio.open(stack_path) as src:
        rgb = np.stack([
            src.read(3),  # B4
            src.read(2),  # B3
            src.read(1)   # B2
        ], axis=-1)

    with rasterio.open(prob_path) as src:
        prob = src.read(1)

    with rasterio.open(binary_path) as src:
        binary = src.read(1)

    # ================================
    # 1. RGB (native resolution)
    # ================================
    rgb_uint8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)

    Image.fromarray(rgb_uint8).save(
        os.path.join(out_dir, "rgb.png")
    )

    # ================================
    # 2. PROBABILITY (white → blue)
    # ================================
    prob_norm = np.clip(prob, 0, 1)

    # Start from white
    prob_img = np.ones((*prob.shape, 3), dtype=np.float32)

    # Reduce red + green → turns white → blue
    prob_img[..., 0] = 1 - prob_norm
    prob_img[..., 1] = 1 - prob_norm

    prob_uint8 = (prob_img * 255).astype(np.uint8)

    Image.fromarray(prob_uint8).save(
        os.path.join(out_dir, "prob.png")
    )

    # ================================
    # 3. RGB + BINARY OVERLAY (cyan)
    # ================================
    overlay = rgb_uint8.copy()

    cyan = np.array([0, 255, 255], dtype=np.uint8)
    mask = binary == 1

    overlay[mask] = (
        0.5 * overlay[mask] + 0.5 * cyan
    ).astype(np.uint8)

    Image.fromarray(overlay).save(
        os.path.join(out_dir, "rgb-mask.png")
    )

    # ================================
    # 4. TRANSPARENT RED MASK (binary)
    # ================================
    rgba = np.zeros((*binary.shape, 4), dtype=np.uint8)

    rgba[..., 0] = 255            # Red
    rgba[..., 3] = binary * 255   # Alpha (0 or 255)

    Image.fromarray(rgba, mode="RGBA").save(
        os.path.join(out_dir, "mask-trans.png")
    )

    print("[DONE] Images generated (native resolution)")

    create_contour_overlay(site, date)


def create_contour_overlay(site, date):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    date_str = date.strftime("%Y-%m-%d")

    contour_path = os.path.join(BASE_DIR, f"../data/dem/{site}/contour.png")
    mask_path = os.path.join(BASE_DIR, f"../data/output/images/{site}/{date_str}/mask-trans.png")

    out_path = os.path.join(BASE_DIR, f"../data/output/images/{site}/{date_str}/contour-overlay.png")

    contour = cv2.imread(contour_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)

    # Resize mask → match contour
    mask = cv2.resize(
        mask,
        (contour.shape[1], contour.shape[0]),
        interpolation=cv2.INTER_NEAREST
    )

    alpha = mask[:, :, 3] / 255.0

    for c in range(3):
        contour[:, :, c] = (
            (1 - alpha) * contour[:, :, c] +
            alpha * mask[:, :, c]
        )

    cv2.imwrite(out_path, contour)

    print(f"[DONE] contour overlay -> {out_path}")