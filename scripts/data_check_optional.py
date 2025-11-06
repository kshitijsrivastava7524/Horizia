import rasterio
src = rasterio.open('data/raw/horizia_stack.tif')
print("✅ Loaded", src.count, "bands,", "Resolution:", src.res, "CRS:", src.crs)
