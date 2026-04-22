import rasterio
import numpy as np
import sys

def inspect_tif(path):
    print(f"\n--- Inspecting: {path} ---\n")

    with rasterio.open(path) as src:
        print("📐 Dimensions:")
        print(f"  Width  : {src.width}")
        print(f"  Height : {src.height}")
        print(f"  Bands  : {src.count}")

        print("\n🌍 CRS (Coordinate Reference System):")
        print(f"  {src.crs}")

        print("\n📏 Transform (pixel size & origin):")
        print(src.transform)

        print("\n📊 Per-band statistics:")

        for i in range(1, src.count + 1):
            band = src.read(i)

            print(f"\n  Band {i}:")
            print(f"    Min   : {np.min(band)}")
            print(f"    Max   : {np.max(band)}")
            print(f"    Mean  : {np.mean(band):.4f}")
            print(f"    Std   : {np.std(band):.4f}")

            unique_vals = np.unique(band[:100, :100])  # sample for speed
            print(f"    Sample unique values: {unique_vals[:10]}")

        print("\n🧱 Data type:")
        print(f"  {src.dtypes}")

        print("\n📦 Bounds (geographic extent):")
        print(src.bounds)

        print("\n--- Done ---\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_tif.py <file.tif>")
    else:
        inspect_tif(sys.argv[1])