# ♻️ DEEPCYCLE

**DEEPCYCLE** est une application web intelligente d'aide au **tri sélectif**.

L'utilisateur recherche un produit sur **Jumia CI**, sélectionne un produit, puis une IA basée sur **ResNet18** analyse son image afin de déterminer la catégorie de déchet et la poubelle adaptée.

##  Fonctionnement

```text
Recherche produit
       ↓
Scraping Jumia CI
       ↓
Sélection du produit
       ↓
Analyse de l'image
       ↓
Modèle IA / Mots-clés
       ↓
Catégorie de déchet
       ↓
Poubelle recommandée ♻️
```

## 📁 Structure du projet

```text
DEEPCYCLE/
├── backend/          # Orchestration de l'application
├── docker/           # Docker Compose
├── frontend/         # Interface Streamlit
├── model_DL/         # Modèle ResNet18 + entraînement
├── scraper/          # Scraping Jumia CI
├── Dockerfile
├── requirements.txt
└── README.md
```

## Installation locale

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

L'application est accessible sur :

```text
http://localhost:8501
```

## 🐳 Avec Docker

```bash
docker build -t deepcycle .
docker run -p 8501:8501 deepcycle
```

Ou avec Docker Compose :

```bash
cd docker
docker-compose up -d --build
```

## Modèle Deep Learning

Le projet utilise **ResNet18** avec **PyTorch Lightning** pour classifier les déchets en 6 catégories :

```text
cardboard
glass
metal
paper
plastic
trash
```

Le modèle entraîné doit être placé ici :

```text
model_DL/models/weights/model_resnet18_ecosort.ckpt
```

📥 **Checkpoint pré-entraîné :** [Télécharger le modèle](https://drive.google.com/file/d/1J8UgX2J7HTj5KjpRg7tkJj6h0zQX2B3o/view?usp=sharing)

> ⚠️ Si le checkpoint est absent, l'application fonctionne en **mode démo** avec une catégorie aléatoire.

## 🏋️ Entraîner le modèle

### Kaggle

Ouvrir :

```text
model_DL/entrainement_kaggle.ipynb
```

Ajouter le dataset **Garbage Classification**, activer le GPU, puis lancer l'entraînement.

### Local

```bash
cd model_DL
python train.py
```

Le dataset doit être organisé ainsi :

```text
dataset/
├── cardboard/
├── glass/
├── metal/
├── paper/
├── plastic/
└── trash/
```

## 🔍 Tester le modèle

Sur une image :

```bash
cd model_DL
python predict.py chemin/vers/image.jpg
```

Sur un dossier :

```bash
python predict.py chemin/vers/dossier/
```

## 🕷️ Diagnostic du scraper

Si le scraper ne fonctionne plus :

```bash
cd scraper
python debug_scraper.py "smartphone"
```

Le script permet de vérifier la réponse de Jumia et la détection des produits.

## 🔎 Transparence de la classification

Chaque résultat indique sa source :

* 🧠 **Modèle IA** : classification par ResNet18.
* 🔤 **Mots-clés** : utilisé notamment pour certains produits électroniques (Bac D3E).
* 🎲 **Mode démo** : utilisé lorsque le modèle `.ckpt` est absent.

## 🛠️ Technologies

* **Python**
* **Streamlit**
* **PyTorch**
* **PyTorch Lightning**
* **ResNet18**
* **BeautifulSoup / Requests**
* **Docker**
* **Kaggle**
