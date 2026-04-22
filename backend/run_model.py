import os
import torch
import rasterio
import numpy as np
from rasterio.windows import Window
from tqdm import tqdm
from model_train_unet_4 import UNet


def main(stack_path=None):
    # ---------- CONFIG ----------
    # STACK_PATH = "../data/processed/stack_normalized1.tif"
    STACK_PATH = stack_path or "../data/processed/stack_normalized1.tif"
    MODEL_PATH = "../../models/horizia_unet_best.pth"
    OUT_PATH   = "../data/output/predicted_lake_prob1.tif"
    PATCH      = 256
    THRESH     = 0.5
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    # -----------------------------

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    # ---------- Load model ----------
    with rasterio.open(STACK_PATH) as src:
        bands = src.count
    model = UNet(in_c=bands, out_c=1).to(device)
    ckpt = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(ckpt["model_state"] if "model_state" in ckpt else ckpt)
    model.eval()
    print("Model loaded successfully from:", MODEL_PATH)

    # ---------- Inference ----------
    with rasterio.open(STACK_PATH) as src:
        profile = src.profile
        H, W = src.height, src.width
        pred_mask = np.zeros((H, W), dtype="float32")

        for y in tqdm(range(0, H, PATCH), desc="Predicting rows"):
            for x in range(0, W, PATCH):
                window = Window(x, y, PATCH, PATCH).intersection(Window(0,0,W,H))
                img = src.read(window=window).astype("float32")
                img = np.nan_to_num(img)

                h, w = img.shape[1], img.shape[2]
                pad_h = (8 - h % 8) if h % 8 else 0
                pad_w = (8 - w % 8) if w % 8 else 0
                if pad_h or pad_w:
                    img = np.pad(img, ((0,0),(0,pad_h),(0,pad_w)), mode="reflect")

                img_tensor = torch.from_numpy(img).unsqueeze(0).to(device)
                with torch.no_grad():
                    pred = torch.sigmoid(model(img_tensor)).cpu().numpy()[0,0]

                pred = pred[:h, :w]
                pred_mask[y:y+pred.shape[0], x:x+pred.shape[1]] = pred

    # ---------- Save probability map ----------
    profile.update(count=1, dtype="float32", compress="lzw")
    with rasterio.open(OUT_PATH, "w", **profile) as dst:
        dst.write(pred_mask, 1)
    print("Saved predicted probability map:", OUT_PATH)

    # ---------- Binary mask ----------
    BIN_PATH = OUT_PATH.replace("_prob1.tif", "_binary1.tif")
    binary_mask = (pred_mask > THRESH).astype("uint8")

    profile.update(dtype="uint8", nodata=0)

    with rasterio.open(BIN_PATH, "w", **profile) as dst:
        dst.write(binary_mask, 1)
    print("Saved binary lake mask:", BIN_PATH)

    # ---------- Accurate area computation ----------
    def pixel_area_m2(profile):
        transform = profile["transform"]
        crs = profile["crs"]
        if "EPSG:4326" in str(crs):
            lat_center = profile["transform"][5] + transform[4] * profile["height"] / 2
            m_per_deg_lat = 111320.0
            m_per_deg_lon = 40075000.0 * np.cos(np.deg2rad(lat_center)) / 360.0
            pixel_area = abs(transform[0] * transform[4]) * m_per_deg_lat * m_per_deg_lon
        else:
            pixel_area = abs(transform[0] * transform[4])
        return pixel_area

    pa = pixel_area_m2(profile)
    lake_pixels = np.sum(binary_mask)
    lake_area_km2 = lake_pixels * pa / 1e6

    # ---------- Summary ----------
    print("\n--- Lake Statistics ---")
    print(f"Pixels > 0.5: {lake_pixels:,}")
    print(f"Pixel area: {pa:.3f} m²")
    print(f"Estimated total lake area: {lake_area_km2:.3f} km²")
    lake_coverage = (lake_pixels / (pred_mask.size)) * 100
    print(f"Lake coverage: {lake_coverage:.2f}%")
    print("-----------------------")

    return {
    "lake_pixels": int(lake_pixels),
    "pixel_area_m2": float(pa),
    "lake_area_km2": float(lake_area_km2),
    "lake_coverage_percent": float(lake_coverage),
    "total_pixels": int(pred_mask.size)
}


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    main()