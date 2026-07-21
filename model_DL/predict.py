"""
DeepCycle — Prédiction (image unique ou dossier complet).
Architecture inspirée du projet de référence garbage_classifier.

Usage (depuis Model_Dl/) :
    python predict.py chemin/vers/image.jpg
    python predict.py chemin/vers/dossier/
"""

import sys
import os
import glob
import torch
from PIL import Image
from torchvision import transforms

from utils.config import CLASSES, IMG_SIZE, CHECKPOINT_DIR, CHECKPOINT_NAME
from utils.custom_classes.GarbageClassifier import GarbageClassifier
from utils.custom_classes.GarbageDataModule import IMAGENET_MEAN, IMAGENET_STD

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif")

_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


def load_model(checkpoint_path=None):
    checkpoint_path = checkpoint_path or os.path.join(CHECKPOINT_DIR, f"{CHECKPOINT_NAME}.ckpt")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"Checkpoint introuvable : {checkpoint_path}\n"
            "Avez-vous lancé train.py (ou téléchargé le .ckpt du notebook Kaggle) "
            "et placé le fichier au bon endroit ?"
        )
    model = GarbageClassifier.load_from_checkpoint(checkpoint_path, num_classes=len(CLASSES))
    model.eval()
    return model


def predict_image(model, image_path):
    image = Image.open(image_path).convert("RGB")
    tensor = _transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        class_index = int(torch.argmax(probs))
        confidence = float(probs[class_index])
    return CLASSES[class_index], confidence


def main():
    if len(sys.argv) < 2:
        print("Usage : python predict.py <image.jpg | dossier/>")
        return

    target = sys.argv[1]
    model = load_model()

    if os.path.isdir(target):
        image_paths = sorted(
            p for p in glob.glob(os.path.join(target, "*"))
            if p.lower().endswith(VALID_EXTENSIONS)
        )
        print(f"{len(image_paths)} image(s) trouvée(s) dans {target}\n")
        print(f"{'Fichier':40s} {'Classe':12s} {'Confiance':10s}")
        for path in image_paths:
            label, confidence = predict_image(model, path)
            print(f"{os.path.basename(path):40s} {label:12s} {confidence * 100:.1f}%")
    else:
        label, confidence = predict_image(model, target)
        print(f"Prédiction : {target}")
        print(f"Classe : {label} | Confiance : {confidence * 100:.1f}%")


if __name__ == "__main__":
    main()
