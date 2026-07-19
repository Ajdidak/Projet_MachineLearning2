"""
Ce code est la version finale du scraper Jumia, intégrant plusieurs améliorations par rapport aux versions produites par chaque membre de l'équipe :

- l'extraction par regex sur le lien produit (plus robuste aux changements
  de classes CSS que des sélecteurs figés) + un repli sur des sélecteurs
  CSS classiques si la regex ne trouve rien,
- l'arrêt anticipé de la pagination dès que `max_results` est atteint
- le scoring de pertinence par mots-clés pour trier les résultats déjà
  récupérés (sans coût réseau supplémentaire),
- le retry + backoff exponentiel sur les requêtes réseau,
- le téléchargement d'image en local, nécessaire pour passer l'image au
  modèle de classification,
- des résultats de secours si Jumia est injoignable ou bloque le scraping,
  pour ne jamais planter la démo.
"""

import os
import re
import time
import random
import logging
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.jumia.ci"
SEARCH_URL = BASE_URL + "/catalog/?q={query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

PRODUCT_LINK_RE = re.compile(r"-[a-z0-9]{6,}\.html$", re.IGNORECASE)
PRICE_RE = re.compile(r"[\d][\d\s,.]*\s?FCFA", re.IGNORECASE)

MAX_PAGES_SAFETY = 15
MAX_RESULTS_SAFETY = 300
REQUEST_DELAY_MIN = 0.8
REQUEST_DELAY_MAX = 1.8



# RÉCUPÉRATION D'UNE PAGE (avec retry + backoff)


def _fetch_page(url, session, max_retries=3, backoff=2):
    for tentative in range(1, max_retries + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Tentative {tentative}/{max_retries} échouée pour {url} : {e}")
            if tentative < max_retries:
                time.sleep(backoff * tentative)
    logger.error(f"Abandon après {max_retries} tentatives : {url}")
    return None


# EXTRACTION DES PRODUITS


def _parse_products_by_link(html, base_url=BASE_URL):
    """Stratégie principale : repère les fiches produit via le motif de leur URL.
    Avantage : robuste aux changements de classes CSS, qui sont fréquents sur Jumia."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if not PRODUCT_LINK_RE.search(href):
            continue

        link = urljoin(base_url, href)
        if link in seen_links:
            continue

        img_tag = a_tag.find("img")
        if img_tag is None:
            continue

        name = (img_tag.get("alt") or "").strip()
        if not name:
            continue

        raw_src = img_tag.get("data-src") or img_tag.get("src")
        image_url = None if (raw_src and raw_src.startswith("data:")) else raw_src
        if image_url and image_url.startswith("//"):
            image_url = "https:" + image_url

        price_match = PRICE_RE.search(a_tag.get_text(" ", strip=True))
        price = price_match.group(0) if price_match else ""

        results.append({"name": name, "price": price, "image_url": image_url, "link": link})
        seen_links.add(link)

    return results


def _parse_products_by_css(html, base_url=BASE_URL):
    """Repli : sélecteurs CSS classiques, utilisé seulement si la stratégie
    par regex ne trouve rien (au cas où Jumia a changé la structure des liens)."""
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.prd") or soup.select("a.core")

    results = []
    seen = set()
    for art in articles:
        img_tag = art.find("img")
        if not img_tag:
            continue

        img_url = img_tag.get("data-src") or img_tag.get("src")
        if img_url and img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url and img_url.startswith("/"):
            img_url = base_url + img_url

        titre_tag = art.find("h3", class_="name") or art.find("div", class_="name")
        name = titre_tag.text.strip() if titre_tag else (img_tag.get("alt") or "Sans titre").strip()

        prix_tag = art.find("div", class_="prc")
        price = prix_tag.get_text(strip=True) if prix_tag else ""

        link_tag = art if art.name == "a" else art.find("a", href=True)
        link = urljoin(base_url, link_tag["href"]) if link_tag and link_tag.get("href") else None

        key = (name, img_url)
        if key in seen:
            continue
        seen.add(key)
        results.append({"name": name, "price": price, "image_url": img_url, "link": link})

    return results


def _extraire_produits(html):
    produits = _parse_products_by_link(html)
    if not produits:
        logger.info("Regex n'a rien trouvé, repli sur les sélecteurs CSS.")
        produits = _parse_products_by_css(html)
    return produits



# SCORE DE PERTINENCE


def _score_pertinence(nom, mots_cle):
    nom_lower = nom.lower()
    return sum(1 for mot in mots_cle if mot in nom_lower)



# RECHERCHE PRINCIPALE


def rechercher_jumia(mot_cle, max_results=5, max_pages_safety=MAX_PAGES_SAFETY):
    """
    Cherche `mot_cle` sur Jumia.ci et retourne jusqu'à `max_results` produits
    pertinents, triés par score de pertinence décroissant(dans notre cas 5 Max).

    S'arrête dès qu'assez de pages ont été scannées pour avoir un pool
    correct de candidats (au moins 3x max_results, ou dès qu'il n'y a plus
    de nouveaux produits.
    """
    if not mot_cle or not mot_cle.strip():
        logger.error("Mot-clé vide.")
        return []

    # Garde-fou : on impose toujours entre 3 et 5 résultats
    max_results = max(3, min(5, max_results))

    mots_cle = mot_cle.strip().lower().split()
    mot_cle_encode = quote_plus(mot_cle.strip())

    candidats = []
    seen_links = set()
    pool_target = max(max_results * 3, 15)  # on veut un pool suffisant pour bien trier

    with requests.Session() as session:
        page = 1
        while page <= max_pages_safety:
            url = SEARCH_URL.format(query=mot_cle_encode)
            if page > 1:
                url += f"&page={page}"

            logger.info(f"Récupération page {page} : {url}")
            html = _fetch_page(url, session)
            if html is None:
                logger.warning("Erreur réseau, arrêt de la pagination.")
                break

            produits_page = _extraire_produits(html)
            if not produits_page:
                logger.info(f"Aucun produit sur la page {page}, fin de la pagination.")
                break

            nouveaux = 0
            for p in produits_page:
                if p["link"] and p["link"] in seen_links:
                    continue
                if p["link"]:
                    seen_links.add(p["link"])
                candidats.append(p)
                nouveaux += 1

            logger.info(f"Page {page} : {len(produits_page)} produits ({nouveaux} nouveaux)")

            if nouveaux == 0:
                logger.info("Page sans nouveau produit, fin de la pagination.")
                break

            if len(candidats) >= pool_target or len(candidats) >= MAX_RESULTS_SAFETY:
                break

            page += 1
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    if not candidats:
        logger.warning("Aucun résultat obtenu, utilisation des résultats de secours.")
        return _fallback_results(mot_cle, max_results)

    for p in candidats:
        p["_score"] = _score_pertinence(p["name"], mots_cle)
    candidats.sort(key=lambda p: p["_score"], reverse=True)

    meilleurs = candidats[:max_results]
    for p in meilleurs:
        p.pop("_score", None)

    return meilleurs


# TÉLÉCHARGEMENT D'IMAGE (nécessaire pour le modèle DL)


def telecharger_image(url_image, dossier="images", nom_fichier="produit.jpg"):
    """Télécharge une image produit en local et retourne son chemin,
    pour que model_DL/predict.py puisse la charger."""
    if not url_image:
        return None

    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, nom_fichier)

    try:
        response = requests.get(url_image, headers=HEADERS, timeout=10)
        response.raise_for_status()
        with open(chemin, "wb") as f:
            f.write(response.content)
        logger.info(f"Image enregistrée : {chemin}")
        return chemin
    except requests.RequestException as e:
        logger.error(f"Échec du téléchargement de l'image : {e}")
        return None



# RÉSULTATS DE SECOURS (site down / structure changée / bloqué)


def _fallback_results(query, n=5):
    return [
        {
            "name": f"{query} (résultat de démonstration {i + 1})",
            "price": "N/A",
            "image_url": None,
            "link": None,
        }
        for i in range(n)
    ]



# TEST EN LIGNE DE COMMANDE


def main():
    mot_cle = input("Entrez le mot-clé du produit que vous recherchez : ").strip()
    if not mot_cle:
        print("Mot-clé vide.")
        return

    print(f"\nRecherche de '{mot_cle}' sur Jumia.ci...\n")
    produits = rechercher_jumia(mot_cle)

    if not produits:
        print("Aucun produit trouvé.")
        return

    for idx, p in enumerate(produits, start=1):
        print(f"{idx}. {p['name'][:80]}")
        print(f"   Prix  : {p['price']}")
        print(f"   Image : {p['image_url']}")
        print(f"   Lien  : {p['link']}\n")


if __name__ == "__main__":
    main()
