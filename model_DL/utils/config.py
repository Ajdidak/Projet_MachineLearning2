"""
EcoSort-Search — Configuration centrale du modèle de deep learning.
Architecture inspirée du projet de référence garbage_classifier
(ResNet18 + PyTorch Lightning).
"""

# Classes du dataset Kaggle "Garbage Classification" (ordre important : il
# doit correspondre à l'ordre alphabétique détecté par ImageFolder, et à
# RAW_CLASSES_ORDER dans Model_Dl/model_utils.py).
CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Chemin du dataset pour un entraînement local (depuis Model_Dl/).
# Sur Kaggle Notebook, le chemin est détecté automatiquement (voir le
# notebook entrainement_kaggle.ipynb) et cette constante n'est pas utilisée.
DATA_PATH = "dataset"

# Hyperparamètres
IMG_SIZE = 224
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
NUM_EPOCHS = 15
TRAIN_RATIO = 0.8

# Emplacement de sauvegarde du modèle entraîné
CHECKPOINT_DIR = "models/weights"
CHECKPOINT_NAME = "model_resnet18_ecosort"  # .ckpt ajouté automatiquement par Lightning

# Emplacement des courbes de performance
LOSS_CURVES_DIR = "models/performance/loss_curves"
