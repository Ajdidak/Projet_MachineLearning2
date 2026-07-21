"""
DeepCycle — Backend.

"""

import random
import re
import time
import requests
from io import BytesIO
from PIL import Image

from scraper.scraper import rechercher_jumia
from model_DL.model_utils import predict_from_image, CATEGORY_LABELS

# --- Détection D3E (électronique) -----------------------------------------

_ELECTRONIC_PATTERNS = [
    # Mots génériques
    r"smartphone", r"i ?phone", r"\bipad\b", r"macbook", r"airpods",
    r"t[ée]l[ée]phone", r"\bportable\b", r"tablette", r"[ée]couteur",
    r"casque(\s+audio)?", r"chargeur", r"c[âa]ble\s*usb", r"batterie",
    r"power\s*bank", r"montre\s*connect[ée]e", r"smartwatch",
    r"ordinateur", r"\blaptop\b", r"pc\s*portable", r"\bsouris\b",
    r"clavier", r"imprimante", r"t[ée]l[ée]vision", r"\btv\b",
    r"enceinte", r"haut[\s-]?parleur", r"cam[ée]ra", r"appareil\s*photo",
    r"console", r"manette", r"playstation", r"\bxbox\b", r"nintendo",
    r"mixeur", r"blender", r"micro-?ondes", r"r[ée]frig[ée]rateur",
    r"cong[ée]lateur", r"climatiseur", r"ventilateur",
    r"machine\s*[àa]\s*laver", r"fer\s*[àa]\s*repasser",
    r"s[èe]che-?cheveux", r"rasoir\s*[ée]lectrique", r"aspirateur",
    r"perceuse", r"routeur", r"modem", r"disque\s*dur", r"cl[ée]\s*usb",
    r"\bdrone\b",
    # Marques très majoritairement électroniques sur Jumia
    r"\bsamsung\b", r"\btecno\b", r"\binfinix\b", r"\bitel\b",
    r"\bxiaomi\b", r"\bredmi\b", r"\boppo\b", r"\bvivo\b", r"\bhonor\b",
    r"\bhuawei\b", r"\bnokia\b", r"\brealme\b", r"\bpoco\b",
    r"\bnasco\b", r"\bhisense\b",
    # Motifs de fiche technique typiques des téléphones/électronique
    r"\d+\s?(go|gb)\s?ram", r"\d+\s?(go|gb)\s?rom", r"\d+\s?mah",
    r"\bandroid\b", r"\b[45]g\b", r"dual\s*sim", r"amoled",
]
_ELECTRONIC_RE = re.compile("|".join(_ELECTRONIC_PATTERNS), re.IGNORECASE)

# Indices secondaires (phrases précises, pour éviter les faux positifs comme
# "papier toilette" -> bleu, qui doit rester marron) utilisés UNIQUEMENT en
# dernier recours, quand aucun modèle n'est chargé.
SECONDARY_KEYWORD_HINTS = {
    "vert": [
        "bouteille en verre", "bouteille de vin", "vin rouge", "vin blanc",
        "bocal", "pot de confiture", "pot en verre", "champagne", "whisky",
    ],
    "bleu": [
        "journal", "magazine", "cahier", "livre", "enveloppe",
        "prospectus", "catalogue", "calendrier", "carnet",
    ],
    "jaune": [
        "bouteille plastique", "bouteille d eau", "bouteille en plastique",
        "canette", "boite de conserve", "boîte de conserve",
        "brique de lait", "shampooing", "gel douche", "flacon",
        "lessive", "detergent", "détergent", "boite de cereales",
        "boîte de céréales", "soda", "boisson gazeuse",
    ],
    "marron": [
        "couche bebe", "couche bébé", "sachet plastique", "film plastique",
        "essuie-tout", "papier toilette", "serviette hygienique",
        "serviette hygiénique", "lingette",
        # Emballages alimentaires / snacks (souvent multicouches -> résiduel)
        "biscuit", "biscuits", "gateau", "gâteau", "cookie", "cookies",
        "chips", "bonbon", "bonbons", "chocolat", "chocolats", "gaufrette",
        "chewing-gum", "nouille", "nouilles", "cube maggi", "cube d assaisonnement",
        "cafe soluble", "café soluble",
    ],
}


def classify_by_keywords(name: str):
    """Retourne une catégorie devinée à partir du nom du produit, ou None."""
    if _ELECTRONIC_RE.search(name):
        return "electronique"

    normalized = name.lower().replace("'", " ").replace("\u2019", " ")
    name_lower = f" {normalized} "
    for category, phrases in SECONDARY_KEYWORD_HINTS.items():
        for phrase in phrases:
            if phrase in name_lower:
                return category

    return None


def search_products(query: str, max_results: int = 5):
    """
    Retourne les produits Jumia les plus pertinents pour `query`.
    rechercher_jumia() trie déjà par score de pertinence et impose entre
    3 et 5 résultats (clamp interne), donc max_results=5 correspond
    exactement à « les 5 produits les plus pertinents ».
    """
    return rechercher_jumia(query, max_results=max_results)


def _download_image(image_url: str, max_retries: int = 3):
    """Télécharge une image depuis une URL et la retourne en objet PIL, ou None si échec.

    Réessaie plusieurs fois avec un délai croissant : le réseau vers les CDN
    d'images Jumia peut être intermittent (observé notamment depuis un
    conteneur Docker), un simple essai unique de 10s est parfois trop strict.
    """
    if not image_url:
        return None

    for tentative in range(1, max_retries + 1):
        try:
            response = requests.get(image_url, timeout=20)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"[pipeline] Tentative {tentative}/{max_retries} échouée pour l'image : {e}")
            if tentative < max_retries:
                time.sleep(1.5 * tentative)

    print(f"[pipeline] Abandon du téléchargement de l'image après {max_retries} tentatives.")
    return None


def classify_product(product: dict) -> dict:
    """
    Classifie un produit et retourne :
        {"category": str, "source": "ia" | "mots-cles" | "demo", "confidence": float | None}

    Ordre de décision :
    1. Mots-clés/marques/motifs électroniques -> D3E directement (le modèle
       ne sait pas prédire cette classe, absente du dataset Kaggle).
    2. Sinon, modèle de deep learning sur l'image téléchargée, si disponible.
    3. Sinon, mots-clés secondaires (verre/papier/jaune/marron).
    4. Sinon, catégorie aléatoire clairement labellisée "mode démo".
    """
    name = product.get("name", "")
    keyword_guess = classify_by_keywords(name)

    if keyword_guess == "electronique":
        return {"category": "electronique", "source": "mots-cles", "confidence": None}

    image = _download_image(product.get("image_url"))
    category, confidence = predict_from_image(image)
    if category is not None:
        return {"category": category, "source": "ia", "confidence": confidence}

    if keyword_guess is not None:
        return {"category": keyword_guess, "source": "mots-cles", "confidence": None}

    return {
        "category": random.choice(list(CATEGORY_LABELS.keys())),
        "source": "demo",
        "confidence": None,
    }
