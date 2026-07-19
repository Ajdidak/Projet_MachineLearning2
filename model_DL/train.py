"""
EcoSort-Search — Entraînement du modèle (ResNet18 + PyTorch Lightning).
Architecture inspirée du projet de référence garbage_classifier.

Usage (depuis Model_Dl/, avec le dataset Kaggle décompressé dans dataset/,
un sous-dossier par classe : dataset/cardboard/, dataset/glass/, ...) :

    python train.py
"""

import pytorch_lightning as pl
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint

from utils.config import (
    CLASSES, DATA_PATH, BATCH_SIZE, LEARNING_RATE, NUM_EPOCHS,
    TRAIN_RATIO, IMG_SIZE, CHECKPOINT_DIR, CHECKPOINT_NAME, LOSS_CURVES_DIR,
)
from utils.custom_classes.GarbageDataModule import GarbageDataModule
from utils.custom_classes.GarbageClassifier import GarbageClassifier
from utils.custom_classes.LossCurveCallback import LossCurveCallback


def main():
    dm = GarbageDataModule(
        DATA_PATH, batch_size=BATCH_SIZE, img_size=IMG_SIZE, train_ratio=TRAIN_RATIO
    )
    dm.setup()

    print("Classes détectées (ordre alphabétique via ImageFolder) :", dm.class_names)
    if dm.class_names != CLASSES:
        print(
            f"⚠️  ATTENTION : l'ordre détecté {dm.class_names} ne correspond pas "
            f"à CLASSES dans utils/config.py ({CLASSES}). Mettez à jour "
            f"config.py avec l'ordre ci-dessus avant de continuer, sinon les "
            f"prédictions du Backend seront décalées."
        )

    model = GarbageClassifier(num_classes=len(dm.class_names), learning_rate=LEARNING_RATE)

    checkpoint_cb = ModelCheckpoint(
        dirpath=CHECKPOINT_DIR,
        filename=CHECKPOINT_NAME,
        monitor="val_acc",
        mode="max",
        save_top_k=1,
    )
    early_stop_cb = EarlyStopping(monitor="val_loss", patience=5, mode="min")
    loss_curve_cb = LossCurveCallback(output_dir=LOSS_CURVES_DIR)

    trainer = pl.Trainer(
        max_epochs=NUM_EPOCHS,
        callbacks=[checkpoint_cb, early_stop_cb, loss_curve_cb],
        accelerator="auto",
        log_every_n_steps=10,
    )

    trainer.fit(model, datamodule=dm)

    print(f"\nModèle sauvegardé : {checkpoint_cb.best_model_path}")
    print(f"Courbes de performance : {LOSS_CURVES_DIR}/loss_curves.png")
    print(
        "\n→ Copiez le fichier .ckpt ci-dessus vers "
        "Model_Dl/models/weights/model_resnet18_ecosort.ckpt "
        "(chemin attendu par model_utils.py)."
    )


if __name__ == "__main__":
    main()
