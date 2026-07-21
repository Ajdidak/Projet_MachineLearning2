"""
DeepCycle — LightningModule : ResNet18 pré-entraîné (ImageNet),
fine-tuné pour la classification des 6 classes d'emballages.
"""

import torch
import torch.nn as nn
import torchmetrics
import pytorch_lightning as pl
from torchvision import models


class GarbageClassifier(pl.LightningModule):
    def __init__(self, num_classes=6, learning_rate=1e-3, fine_tune=False, pretrained=True):
        super().__init__()
        self.save_hyperparameters()

        # pretrained=False évite de télécharger les poids ImageNet quand on
        # sait qu'on va de toute façon les écraser juste après avec un
        # checkpoint déjà entraîné (voir Model_Dl/model_utils.py) — inutile
        # d'attendre ce téléchargement (~45 Mo) à chaque démarrage de l'app.
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        self.model = models.resnet18(weights=weights)

        # Transfer learning : backbone gelé par défaut, seule la tête
        # (fc) est entraînée. Passer fine_tune=True (phase 2) pour dégeler
        # tout le réseau avec un learning_rate plus faible.
        if not fine_tune:
            for param in self.model.parameters():
                param.requires_grad = False

        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, num_classes)

        self.criterion = nn.CrossEntropyLoss()
        self.train_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)
        self.val_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.train_acc(preds, y)
        self.log("train_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log("train_acc", self.train_acc, prog_bar=True, on_step=False, on_epoch=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.val_acc(preds, y)
        self.log("val_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log("val_acc", self.val_acc, prog_bar=True, on_step=False, on_epoch=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.learning_rate)
