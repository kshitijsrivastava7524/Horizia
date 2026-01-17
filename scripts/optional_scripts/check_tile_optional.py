import numpy as np
import matplotlib.pyplot as plt

img = np.load("../../data/tiles/train/images/tile_000001.npy")
mask = np.load("../../data/tiles/train/masks/mask_000001.npy")

plt.subplot(1,2,1)
plt.imshow(img[3], cmap='gray')  # NIR band (index 3)
plt.title("Tile NIR band")

plt.subplot(1,2,2)
plt.imshow(mask, cmap='Blues')
plt.title("Tile Mask")
plt.show()
