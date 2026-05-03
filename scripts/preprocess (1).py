import rasterio
import numpy as np
import os


def normalize_stack(input_path, site, date):
    print(f"[NORMALIZE] {site} {date}")

    # dynamic output path (no overwrite issue)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(
        BASE_DIR,
        f"../data/processed/{site}/{date.strftime('%Y-%m-%d')}.tif"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with rasterio.open(input_path) as src:
        arr = src.read().astype('float32')
        profile = src.profile

    # ---------------- SAME LOGIC (UNCHANGED) ----------------
    arr_norm = np.zeros_like(arr)
    for i in range(arr.shape[0]):
        band = arr[i]
        band_min, band_max = np.nanpercentile(band, (1, 99))
        if band_max - band_min < 1e-6:
            arr_norm[i] = np.zeros_like(band)
        else:
            arr_norm[i] = np.clip((band - band_min) / (band_max - band_min), 0, 1)
    # --------------------------------------------------------

    profile.update(dtype='float32')

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(arr_norm)

    print("Normalized pixel values stack saved to:", output_path)

    return output_path