"""
EcoSort-Search — Pont entre le modèle PyTorch Lightning (ResNet18) et le
Backend. Charge le checkpoint entraîné (Model_Dl/models/weights/*.ckpt) et
convertit la prédiction brute (cardboard/glass/.../trash) vers les 5
catégories officielles du projet.

IMPORTANT : ce module ne fait QUE de la prédiction par image (le modèle ne
connaît que des emballages, jamais l'électronique). La détection D3E et la
logique de repli quand le modèle est absent vivent dans Backend/pipeline.py.
"""

from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent
CHECKPOINT_PATH = MODEL_DIR / "models" / "weights" / "model_resnet18_ecosort.ckpt"
IMG_SIZE = 224

CATEGORY_LABELS = {
    "jaune": "🟡 Poubelle JAUNE — Emballages légers (plastique, métal, carton)",
    "vert": "🟢 Poubelle VERTE — Verre",
    "bleu": "🔵 Poubelle BLEUE — Papier",
    "electronique": "🎛️ Bac D3E — Électronique",
    "marron": "⚫ Poubelle MARRON — Déchets résiduels",
}

CATEGORY_COLORS = {
    "jaune": "#F2C94C",
    "vert": "#27AE60",
    "bleu": "#2D9CDB",
    "electronique": "#7D7D7D",
    "marron": "#6D4C41",
}

# Mapping des classes brutes du dataset Kaggle vers les catégories officielles
RAW_CLASS_TO_CATEGORY = {
    "plastic": "jaune",
    "metal": "jaune",
    "cardboard": "jaune",
    "glass": "vert",
    "paper": "bleu",
    "trash": "marron",
}

# Doit correspondre exactement à CLASSES dans Model_Dl/utils/config.py
# (ImageFolder trie les classes par ordre alphabétique)
RAW_CLASSES_ORDER = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

_model = None
_transform = None


def load_model():
    """Charge le checkpoint PyTorch Lightning (mise en cache en mémoire)."""
    global _model, _transform
    if _model is None:
        try:
            import torch
            from torchvision import transforms
            from Model_Dl.utils.custom_classes.GarbageClassifier import GarbageClassifier
            from Model_Dl.utils.custom_classes.GarbageDataModule import IMAGENET_MEAN, IMAGENET_STD

            if not CHECKPOINT_PATH.exists():
                raise FileNotFoundError(f"Checkpoint introuvable : {CHECKPOINT_PATH}")

            _model = GarbageClassifier.load_from_checkpoint(
                str(CHECKPOINT_PATH), num_classes=len(RAW_CLASSES_ORDER), pretrained=False
            )
            _model.eval()
            _transform = transforms.Compose([
                transforms.Resize((IMG_SIZE, IMG_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ])
        except Exception as e:
            print(f"[model_utils] Modèle introuvable ou non chargeable : {e}")
            _model = None
    return _model


def predict_from_image(image):
    """
    Prend une image PIL (ou None) et retourne un tuple (categorie, confiance).

    - Si le modèle n'est pas chargeable ou qu'aucune image n'est fournie,
      retourne (None, None) : c'est au code appelant (Backend/pipeline.py)
      de décider du repli (mots-clés ou mode démo).
    - Sinon, retourne la catégorie officielle ('jaune', 'vert', 'bleu' ou
      'marron' — jamais 'electronique', absente du dataset) et la confiance
      du modèle pour cette classe (entre 0 et 1).
    """
    model = load_model()
    if model is None or image is None:
        return None, None

    import torch

    tensor = _transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        class_index = int(torch.argmax(probs))
        confidence = float(probs[class_index])

    raw_label = RAW_CLASSES_ORDER[class_index]
    category = RAW_CLASS_TO_CATEGORY.get(raw_label, "marron")
    return category, confidence
