import rasterio
import numpy as np

# check the fetched data
src = rasterio.open('../../data/raw/horizia_stack.tif')
print("Loaded", src.count, "bands,", "Resolution:", src.res, "CRS:", src.crs)

# check normalized pixel in stack_normalized.tif
import numpy as np

with rasterio.open("../../data/processed/stack_normalized.tif") as src_new:
    arr = src_new.read()
    g = src_new.read(2)   # B3
    n = src_new.read(4)   # B8
    ndwi = (g - n) / (g + n + 1e-6)
    print("NDWI range:", ndwi.min(), ndwi.max())
print("Min:", np.nanmin(arr), "Max:", np.nanmax(arr))

# check lake_mask
with rasterio.open("../../data/processed/lake_mask.tif") as m:
    print("Mask shape:", (m.count, m.height, m.width))
    print("Data type:", m.dtypes)
    print("Unique values:", np.unique(m.read(1)))
