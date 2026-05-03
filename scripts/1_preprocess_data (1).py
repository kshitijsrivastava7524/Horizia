import rasterio
import numpy as np
import os

INPUT = "../data/raw/horizia_stack.tif"
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


# import rasterio
# import numpy as np
# import os
# import logging
# from pathlib import Path

# # ---------- LOGGING ----------
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(message)s'
# )
# log = logging.getLogger(__name__)

# # ---------- CONFIG ----------
# INPUT       = "../data/raw/horizia_stack.tif"
# OUTPUT      = "../data/processed/stack_normalized1.tif"
# LOW_PERC    = 2      # lower percentile for stretch
# HIGH_PERC   = 98     # upper percentile for stretch
# MIN_VALID   = 0.01   # minimum fraction of valid pixels required per band
# NODATA_FILL = 0.0    # value to fill nodata/nan/inf pixels

# os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# # ---------- VALIDATE INPUT ----------
# if not os.path.exists(INPUT):
#     raise FileNotFoundError(f"Input file not found: {INPUT}")

# if os.path.getsize(INPUT) == 0:
#     raise ValueError(f"Input file is empty: {INPUT}")

# log.info(f"Reading: {INPUT}")

# # ---------- READ ----------
# with rasterio.open(INPUT) as src:
#     arr     = src.read().astype('float32')   # (bands, H, W)
#     profile = src.profile.copy()
#     nodata  = src.nodata
#     crs     = src.crs
#     transform = src.transform

#     log.info(f"Shape: {arr.shape} | CRS: {crs} | NoData: {nodata}")
#     log.info(f"Transform: {transform}")

# # ---------- SANITY CHECKS ----------
# if arr.ndim != 3:
#     raise ValueError(f"Expected 3D array (bands,H,W), got shape: {arr.shape}")

# if arr.shape[0] == 0:
#     raise ValueError("No bands found in input file")

# if arr.shape[1] < 2 or arr.shape[2] < 2:
#     raise ValueError(f"Image too small to process: {arr.shape}")

# # ---------- HANDLE NODATA ----------
# # replace nodata value with nan so it is excluded from percentile calc
# if nodata is not None:
#     arr[arr == nodata] = np.nan

# # replace any inf values
# arr[np.isinf(arr)] = np.nan

# log.info(f"NaN pixels before norm: {np.isnan(arr).sum():,}")

# # ---------- NORMALIZE PER BAND ----------
# arr_norm = np.full_like(arr, NODATA_FILL)   # start with fill value

# band_stats = []

# for i in range(arr.shape[0]):
#     band = arr[i]                            # (H, W)

#     # count valid pixels
#     valid_mask  = ~np.isnan(band)
#     valid_count = valid_mask.sum()
#     total_count = band.size
#     valid_frac  = valid_count / total_count

#     log.info(f"Band {i+1}: valid pixels = {valid_count:,} / {total_count:,} ({valid_frac*100:.1f}%)")

#     # skip band if too few valid pixels
#     if valid_frac < MIN_VALID:
#         log.warning(f"Band {i+1}: too few valid pixels ({valid_frac*100:.1f}%) → filled with {NODATA_FILL}")
#         band_stats.append({
#             "band": i+1,
#             "status": "skipped",
#             "min": None,
#             "max": None
#         })
#         continue

#     # percentile stretch on valid pixels only
#     valid_vals          = band[valid_mask]
#     band_min, band_max  = np.nanpercentile(valid_vals, (LOW_PERC, HIGH_PERC))

#     log.info(f"Band {i+1}: percentile range [{band_min:.4f}, {band_max:.4f}]")

#     # flat band check
#     if (band_max - band_min) < 1e-6:
#         log.warning(f"Band {i+1}: flat band (max-min < 1e-6) → filled with {NODATA_FILL}")
#         band_stats.append({
#             "band": i+1,
#             "status": "flat",
#             "min": band_min,
#             "max": band_max
#         })
#         continue

#     # normalize valid pixels
#     normalized = np.full_like(band, NODATA_FILL)
#     normalized[valid_mask] = np.clip(
#         (band[valid_mask] - band_min) / (band_max - band_min),
#         0.0, 1.0
#     )

#     arr_norm[i] = normalized

#     band_stats.append({
#         "band":   i+1,
#         "status": "ok",
#         "min":    band_min,
#         "max":    band_max,
#         "mean":   float(np.nanmean(normalized[valid_mask])),
#         "std":    float(np.nanstd(normalized[valid_mask]))
#     })

# # ---------- FINAL NaN FILL ----------
# # replace any remaining nans with fill value
# nan_remaining = np.isnan(arr_norm).sum()
# if nan_remaining > 0:
#     log.warning(f"Filling {nan_remaining:,} remaining NaN pixels with {NODATA_FILL}")
#     arr_norm = np.nan_to_num(arr_norm, nan=NODATA_FILL)

# # ---------- OUTPUT VALIDATION ----------
# if np.isnan(arr_norm).any():
#     raise RuntimeError("NaN values still present after normalization — check input data")

# if arr_norm.min() < 0.0 or arr_norm.max() > 1.0:
#     raise RuntimeError(f"Values out of [0,1] range: min={arr_norm.min()}, max={arr_norm.max()}")

# # ---------- SAVE ----------
# profile.update(
#     dtype   = 'float32',
#     nodata  = None,       # nodata handled — output is clean 0-1
#     compress= 'lzw',      # lossless compression — reduces file size
#     tiled   = True,       # tiled layout for faster spatial reads
#     blockxsize = 256,     # tile size matches your patch size
#     blockysize = 256
# )

# # safe write — write to tmp first
# tmp_output = OUTPUT + ".tmp"
# try:
#     with rasterio.open(tmp_output, 'w', **profile) as dst:
#         dst.write(arr_norm)
#     os.replace(tmp_output, OUTPUT)
#     log.info(f"Saved: {OUTPUT}")
# except Exception as e:
#     if os.path.exists(tmp_output):
#         os.remove(tmp_output)
#     raise RuntimeError(f"Failed to save output: {e}")

# # ---------- SUMMARY ----------
# log.info("\n--- Band Statistics ---")
# for s in band_stats:
#     if s["status"] == "ok":
#         log.info(
#             f"Band {s['band']}: "
#             f"range=[{s['min']:.4f}, {s['max']:.4f}] "
#             f"mean={s['mean']:.4f} std={s['std']:.4f}"
#         )
#     else:
#         log.warning(f"Band {s['band']}: status={s['status']}")

# log.info(f"Output shape:  {arr_norm.shape}")
# log.info(f"Output range:  [{arr_norm.min():.4f}, {arr_norm.max():.4f}]")
# log.info(f"Output dtype:  {arr_norm.dtype}")
# file_size_mb = os.path.getsize(OUTPUT) / 1e6
# log.info(f"File size:     {file_size_mb:.1f} MB")
# log.info("Normalization complete.")