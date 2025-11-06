import numpy as np
import matplotlib.pyplot as plt
x = np.load("D:/project/Horizia/data/train/images/tile_0001.npy")
y = np.load("D:/project/Horizia/data/train/masks/mask_0001.npy")
plt.subplot(1,2,1); plt.imshow(x[3], cmap='gray'); plt.title("NIR band")
plt.subplot(1,2,2); plt.imshow(y, cmap='Blues'); plt.title("Lake Mask")
plt.show()
