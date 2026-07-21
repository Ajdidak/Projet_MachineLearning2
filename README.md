# ♻️ DEEPCYCLE

Application web qui aide au tri sélectif : l'utilisateur saisit un nom de produit,
l'app le recherche sur Jumia, puis une IA (deep learning) analyse le produit choisi
pour indiquer la bonne poubelle.

## Structure du projet

```
Backend/      # Orchestration : fait le lien entre Scraper et Model_Dl pour le Frontend
Docker/       # docker-compose.yml pour lancer l'app facilement
Frontend/     # Interface Streamlit (app.py)
Model_Dl/     # ResNet18 + PyTorch Lightning : utils/ (config, DataModule, LightningModule,
              # callback), train.py, predict.py, model_utils.py (pont vers le Backend),
              # entrainement_kaggle.ipynb, models/weights/ (checkpoint .ckpt)
Scraper/      # Scraping Jumia (scraper.py, debug_scraper.py)
Dockerfile    # Image Docker principale
Requirements.txt
```

## Lancer en local (sans Docker)

```bash
pip install -r Requirements.txt
streamlit run Frontend/app.py
```

## Lancer avec Docker

Depuis la racine du projet :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Ou avec docker-compose, depuis le dossier `Docker/` :

```bash
cd Docker
docker-compose up -d --build
```

Puis ouvrir [http://localhost:8501](http://localhost:8501).

## Entraîner le modèle (Jalon 1)

1. Télécharger le dataset Kaggle *Garbage Classification* et le décompresser dans
   `Model_DL/dataset/` (ignoré par Git, voir `.gitignore`).
2. Depuis `Model_DL/`, lancer :
   ```bash
   python train.py
   ```
3. Le modèle est sauvegardé dans `Model_DL/model/modele_eco_sort.h5`.
4. Vérifier que `RAW_CLASSES_ORDER` dans `model_utils.py` correspond bien à l'ordre
   des classes affiché par `train.py` (`class_indices`).

## Entraîner le modèle (Jalon 1) — PyTorch Lightning + ResNet18

Architecture inspirée du projet de référence `garbage_classifier` (ResNet18
pré-entraîné, fine-tuné avec PyTorch Lightning).

**Sur Kaggle Notebook (recommandé)** :
1. Ouvrez `Model_DL/entrainement_kaggle.ipynb` sur Kaggle, ajoutez le dataset
   *Garbage Classification* via **+ Add Data**, activez le GPU (Settings →
   Accelerator → GPU T4 x2), puis exécutez les cellules dans l'ordre.
2. Téléchargez le checkpoint final (`model_resnet18_ecosort.ckpt`) depuis
   l'onglet *Output*.

**En local (si vous avez un GPU ou pour un test rapide sur CPU)** :
```bash
cd Model_Dl
python train.py
```
Le dataset doit être dans `Model_Dl/dataset/` (un sous-dossier par classe :
`cardboard/`, `glass/`, `metal/`, `paper/`, `plastic/`, `trash/`).

**Dans tous les cas**, placez le checkpoint obtenu dans :
```
Model_Dl/models/weights/model_resnet18_ecosort.ckpt
```
et vérifiez que l'ordre des classes affiché pendant l'entraînement correspond
bien à `CLASSES` dans `Model_Dl/utils/config.py` et à `RAW_CLASSES_ORDER`
dans `Model_Dl/model_utils.py`.

**Prédiction en ligne de commande** (pour tester le modèle isolément) :
```bash
cd Model_Dl
python predict.py chemin/vers/image.jpg
python predict.py chemin/vers/dossier/
```

## Si le scraper ne renvoie que des résultats de démonstration

Depuis `scraper/`, lancez :
```bash
python debug_scraper.py "smartphone"
```
Ce script affiche le statut HTTP, sauvegarde le HTML brut dans `debug_output.html`
et indique combien de produits ont été détectés — pratique pour vérifier
rapidement si Jumia a changé sa structure ou si l'URL de recherche doit être
ajustée.

## Transparence de la classification

Chaque résultat affiche sa source : `🧠 modèle IA` (image analysée par le CNN),
`🔤 mots-clés` (notamment pour le Bac D3E, absent du dataset Kaggle — voir
`Backend/pipeline.py`), ou `🎲 mode démo` (aucun modèle chargé, catégorie
aléatoire). Une fois `Model_Dl/model/modele_eco_sort.h5` en place, le mode
démo disparaît progressivement au profit du modèle réel.

## Équipe

- Répartition du travail sur 3 branches Git distinctes, PR obligatoire pour merger sur `main`.
