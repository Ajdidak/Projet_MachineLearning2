# ♻️ DEEPCYCLE

Application web qui aide au tri sélectif : l'utilisateur saisit un nom de produit,
l'app le recherche sur Jumia, puis une IA (deep learning) analyse le produit choisi
pour indiquer la bonne poubelle.

## Structure du projet

```
backend/      # Orchestration : fait le lien entre scraper et model_DL pour le frontend
docker/       # docker-compose.yml pour lancer l'app facilement
frontend/     # Interface Streamlit (app.py)
model_DL/     # ResNet18 + PyTorch Lightning : utils/ (config, DataModule, LightningModule,
              # callback), train.py, predict.py, model_utils.py (pont vers le backend),
              # entrainement_kaggle.ipynb, models/weights/ (checkpoint .ckpt)
scraper/      # Scraping Jumia (scraper.py, debug_scraper.py)
Dockerfile    # Image Docker principale
requirements.txt
```

## Lancer en local (sans Docker)

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

## Lancer avec Docker

Depuis la racine du projet :

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

Ou avec docker-compose, depuis le dossier `docker/` :

```bash
cd docker
docker-compose up -d --build
```

Puis ouvrir [http://localhost:8501](http://localhost:8501).

## Récupérer le modèle pré-entraîné (sans réentraîner)

Le fichier de poids (`.ckpt`) n'est pas versionné sur Git (trop volumineux).
Pour lancer l'application avec le vrai modèle sans avoir à réentraîner :

1. Téléchargez le checkpoint ici :
   👉 [model_resnet18_ecosort.ckpt](https://drive.google.com/file/d/1J8UgX2J7HTj5KjpRg7tkJj6h0zQX2B3o/view?usp=sharing)

2. Placez le fichier téléchargé exactement ici, sans renommer :
   ```
   model_DL/models/weights/model_resnet18_ecosort.ckpt
   ```

3. Lancez l'application normalement (`docker-compose up --build` depuis `docker/`).

⚠️ Sans ce fichier, l'application fonctionne quand même mais bascule en
**mode démo** (catégorie aléatoire, badge 🎲 visible sur les résultats).

## Entraîner le modèle soi-même (PyTorch Lightning + ResNet18)

Architecture inspirée du projet de référence `garbage_classifier` (ResNet18
pré-entraîné, fine-tuné avec PyTorch Lightning).

**Sur Kaggle Notebook (recommandé)** :
1. Ouvrez `model_DL/entrainement_kaggle.ipynb` sur Kaggle, ajoutez le dataset
   *Garbage Classification* via **+ Add Data**, activez le GPU (Settings →
   Accelerator → GPU T4 x2), puis exécutez les cellules dans l'ordre.
2. Téléchargez le checkpoint final (`model_resnet18_ecosort.ckpt`) depuis
   l'onglet *Output*.

**En local (si vous avez un GPU ou pour un test rapide sur CPU)** :
```bash
cd model_DL
python train.py
```
Le dataset doit être dans `model_DL/dataset/` (ignoré par Git, voir `.gitignore`),
avec un sous-dossier par classe :
`cardboard/`, `glass/`, `metal/`, `paper/`, `plastic/`, `trash/`.

**Dans tous les cas**, placez le checkpoint obtenu dans :
```
model_DL/models/weights/model_resnet18_ecosort.ckpt
```
et vérifiez que l'ordre des classes affiché pendant l'entraînement correspond
bien à `CLASSES` dans `model_DL/utils/config.py` et à `RAW_CLASSES_ORDER`
dans `model_DL/model_utils.py`.

**Prédiction en ligne de commande** (pour tester le modèle isolément) :
```bash
cd model_DL
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
`backend/pipeline.py`), ou `🎲 mode démo` (aucun modèle chargé, catégorie
aléatoire). Une fois `model_DL/models/weights/model_resnet18_ecosort.ckpt` en
place, le mode démo disparaît au profit du modèle réel.

