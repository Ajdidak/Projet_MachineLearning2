"""
EcoSort-Search — DataModule PyTorch Lightning pour le dataset Garbage
Classification (glass, paper, cardboard, plastic, metal, trash).
"""

import numpy as np
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
import pytorch_lightning as pl

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class GarbageDataModule(pl.LightningDataModule):
    """
    Charge le dataset depuis un dossier contenant un sous-dossier par classe
    (format torchvision.datasets.ImageFolder), avec augmentation de données
    côté entraînement uniquement.

    NOTE IMPORTANTE : on crée deux instances distinctes d'ImageFolder (une
    par transform) plutôt qu'un seul dataset partagé entre les deux splits.
    C'est volontaire : avec un seul ImageFolder partagé, changer son
    `.transform` après un random_split() modifierait aussi bien le split
    d'entraînement que de validation (les deux Subset pointent vers le même
    objet dataset sous-jacent). Utiliser deux instances + les mêmes indices
    évite ce piège classique.
    """

    def __init__(self, data_dir, batch_size=32, img_size=224, train_ratio=0.8, seed=42):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.img_size = img_size
        self.train_ratio = train_ratio
        self.seed = seed
        self.class_names = None
        self.train_dataset = None
        self.val_dataset = None

        self.train_transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
        self.val_transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])

    def setup(self, stage=None):
        full_train = datasets.ImageFolder(self.data_dir, transform=self.train_transform)
        full_val = datasets.ImageFolder(self.data_dir, transform=self.val_transform)
        self.class_names = full_train.classes

        n_total = len(full_train)
        indices = list(range(n_total))
        rng = np.random.default_rng(self.seed)
        rng.shuffle(indices)
        n_train = int(self.train_ratio * n_total)

        self.train_dataset = Subset(full_train, indices[:n_train])
        self.val_dataset = Subset(full_val, indices[n_train:])

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=2)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=2)
