"""
EcoSort-Search — Callback PyTorch Lightning : enregistre et trace les
courbes de loss/accuracy (train + validation) à chaque epoch.
"""

import os
import matplotlib
matplotlib.use("Agg")  # pas d'affichage interactif nécessaire (Kaggle/serveur)
import matplotlib.pyplot as plt
import pytorch_lightning as pl


class LossCurveCallback(pl.Callback):
    def __init__(self, output_dir="models/performance/loss_curves"):
        super().__init__()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.train_losses, self.val_losses = [], []
        self.train_accs, self.val_accs = [], []

    def on_train_epoch_end(self, trainer, pl_module):
        metrics = trainer.callback_metrics
        if "train_loss" in metrics:
            self.train_losses.append(float(metrics["train_loss"]))
        if "train_acc" in metrics:
            self.train_accs.append(float(metrics["train_acc"]))

    def on_validation_epoch_end(self, trainer, pl_module):
        metrics = trainer.callback_metrics
        if "val_loss" in metrics:
            self.val_losses.append(float(metrics["val_loss"]))
        if "val_acc" in metrics:
            self.val_accs.append(float(metrics["val_acc"]))
        self._plot()

    def _plot(self):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        axes[0].plot(self.train_losses, label="train")
        axes[0].plot(self.val_losses, label="val")
        axes[0].set_title("Loss")
        axes[0].set_xlabel("Epoch")
        axes[0].legend()

        axes[1].plot(self.train_accs, label="train")
        axes[1].plot(self.val_accs, label="val")
        axes[1].set_title("Accuracy")
        axes[1].set_xlabel("Epoch")
        axes[1].legend()

        fig.tight_layout()
        fig.savefig(os.path.join(self.output_dir, "loss_curves.png"))
        plt.close(fig)
