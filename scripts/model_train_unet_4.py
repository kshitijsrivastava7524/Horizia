# scripts/train_unet.py
import os
import glob
import random
import numpy as np
import torch
import torch.nn as nn
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader

# ---------- Dataset ----------
class LakeTileDataset(Dataset):
    def __init__(self, img_dir, mask_dir, augment=False):
        self.imgs = sorted(glob.glob(os.path.join(img_dir, "*.npy")))
        self.masks = sorted(glob.glob(os.path.join(mask_dir, "*.npy")))
        assert len(self.imgs) == len(self.masks), "Images and masks count mismatch"
        self.augment = augment

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        img = np.load(self.imgs[idx]).astype("float32")  # (C,H,W)
        mask = np.load(self.masks[idx]).astype("float32")  # (H,W)
        img = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)
        # This ensures the mask is strictly binary (0.0 or 1.0)
        # It handles cases where masks are 0/255, 0/2, etc.
        mask = (mask > 0.5).astype("float32")
        
        # Normalize image already in 0-1 range; ensure shape (C,H,W)
        if img.ndim == 2:
            img = img[np.newaxis, ...]
        # augmentation: flips
        if self.augment:
            if random.random() > 0.5:
                img = np.flip(img, axis=2).copy()
                mask = np.flip(mask, axis=1).copy()
            if random.random() > 0.5:
                img = np.flip(img, axis=1).copy()
                mask = np.flip(mask, axis=0).copy()
        # to tensor
        x = torch.from_numpy(img)
        y = torch.from_numpy(mask).unsqueeze(0)
        return x, y

# ---------- UNet model ----------
class DoubleConv(nn.Module):
    def __init__(self, in_c, out_c):
        super().__init__()
        self.seq = nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c), nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, 3, padding=1),
            nn.BatchNorm2d(out_c), nn.ReLU(inplace=True)
        )
    def forward(self, x): return self.seq(x)

class UNet(nn.Module):
    def __init__(self, in_c=7, out_c=1):
        super().__init__()
        self.enc1 = DoubleConv(in_c, 32)
        self.enc2 = DoubleConv(32, 64)
        self.enc3 = DoubleConv(64, 128)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(128, 256)
        self.up3 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.dec3 = DoubleConv(256, 128)
        self.up2 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.dec2 = DoubleConv(128, 64)
        self.up1 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.dec1 = DoubleConv(64, 32)
        self.outc = nn.Conv2d(32, out_c, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        b = self.bottleneck(self.pool(e3))
        d3 = self.up3(b)
        d3 = self.dec3(torch.cat([d3, e3], dim=1))
        d2 = self.up2(d3)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))
        d1 = self.up1(d2)
        d1 = self.dec1(torch.cat([d1, e1], dim=1))
        out = self.outc(d1)   # return raw logits
        return out

# ---------- Metrics and loss ----------
def iou_score(pred_logits, target, thresh=0.5):
    pred_prob = torch.sigmoid(pred_logits)
    pred_bin = (pred_prob > thresh).float()
    inter = (pred_bin * target).sum(dim=(1,2,3))
    union = (pred_bin + target - pred_bin * target).sum(dim=(1,2,3))
    iou = (inter + 1e-6) / (union + 1e-6)
    return iou.mean().item()


def dice_loss(pred_logits, target, smooth=1.0):
    pred_prob = torch.sigmoid(pred_logits)
    pred_flat = pred_prob.view(pred_prob.size(0), -1)
    target_flat = target.view(target.size(0), -1)
    inter = (pred_flat * target_flat).sum(1)
    denom = pred_flat.sum(1) + target_flat.sum(1)
    dice = (2. * inter + smooth) / (denom + smooth)
    return 1.0 - dice.mean()


# ---------- Training ----------
def train_loop(args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    print("Using device:", device)

    train_ds = LakeTileDataset(os.path.join(args.tiles, "train", "images"),os.path.join(args.tiles, "train", "masks"),augment=True)
    val_ds = LakeTileDataset(os.path.join(args.tiles, "val", "images"),os.path.join(args.tiles, "val", "masks"),augment=False)

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=2, pin_memory=True)

    # determine input channels from one sample
    sample_img = np.load(sorted(glob.glob(os.path.join(args.tiles, "train", "images", "*.npy")))[0])
    in_c = sample_img.shape[0]

    model = UNet(in_c=in_c, out_c=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()


    best_iou = 0.0
    os.makedirs(args.out, exist_ok=True)

    for epoch in range(1, args.epochs+1):
        model.train()
        running_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs} [train]")
        for X, Y in pbar:
            X = X.to(device); Y = Y.to(device)
            pred = model(X)
            loss = 0.5 * bce(pred, Y) + 0.5 * dice_loss(pred, Y)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            running_loss = loss.item()
            pbar.set_postfix(loss=running_loss)

        # validation
        model.eval()
        val_losses = []
        ious = []
        with torch.no_grad():
            for Xv, Yv in tqdm(val_loader, desc=f"Epoch {epoch}/{args.epochs} [val]"):
                Xv = Xv.to(device); Yv = Yv.to(device)
                pv = model(Xv)
                lval = 0.5 * bce(pv, Yv) + 0.5 * dice_loss(pv, Yv)
                val_losses.append(lval.item())
                ious.append(iou_score(pv, Yv, thresh=args.thresh))
        mean_val_loss = sum(val_losses)/len(val_losses)
        mean_iou = sum(ious)/len(ious)

        print(f"Epoch {epoch} => Train Loss:{running_loss:.4f} | Val Loss:{mean_val_loss:.4f} | Val IoU:{mean_iou:.4f}")

        # checkpoint best model
        if mean_iou > best_iou:
            best_iou = mean_iou
            ckpt_path = os.path.join(args.out, "horizia_unet_best.pth")
            torch.save({"epoch": epoch, "model_state": model.state_dict(), "iou": best_iou}, ckpt_path)
            print("Saved best model ->", ckpt_path)

    # final save
    torch.save(model.state_dict(), os.path.join(args.out, "horizia_unet_final.pth"))
    print("Training complete. Best IoU:", best_iou)

args = {
    "tiles": "../data/tiles",
    "out": "../models",
    "epochs": 30,
    "batch": 4,
    "lr": 1e-4,
    "thresh": 0.5,
    "no_cuda": False
}
from types import SimpleNamespace
args = SimpleNamespace(**args)
if __name__ == '__main__':
    train_loop(args)