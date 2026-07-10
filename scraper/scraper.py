"""
EcoSort-Search — Module de scraping Jumia (v3 — pagination complète).

MÉTHODE (basée sur une inspection réelle de jumia.ci) :
1. Chaque fiche produit est un lien <a href="...-XXXXXXXX.html"> (voir
   PRODUCT_LINK_RE) — ce motif est plus stable que des classes CSS devinées.
2. Le nom complet est dans l'attribut alt="" de l'image (texte
   d'accessibilité, fiable).
3. Les images sont en lazy-loading (data-src), le prix suit le format
   "12 345 FCFA".

EXHAUSTIVITÉ :
Jumia pagine ses résultats (?page=2, ?page=3, ...). Pour renvoyer TOUS les
produits d'une recherche, on parcourt les pages jusqu'à ce qu'une page ne
renvoie plus aucun nouveau produit. Deux garde-fous protègent quand même le
scraper contre les requêtes trop larges (ex: "téléphone" a plusieurs
milliers de résultats sur Jumia) :
- MAX_PAGES_SAFETY : nombre maximum de pages parcourues
- MAX_RESULTS_SAFETY : nombre maximum de produits renvoyés
Ces constantes sont volontairement en haut du fichier pour être ajustées
facilement par l'équipe si besoin. Un court délai entre requêtes
(REQUEST_DELAY_SECONDS) évite de bombarder le serveur de Jumia.
"""

import re
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.jumia.ci/catalog/?q={query}"
BASE_URL = "https://www.jumia.ci"

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
REQUEST_DELAY_SECONDS = 0.6


def _build_search_url(query: str, page: int) -> str:
    url = SEARCH_URL.format(query=query.replace(" ", "+"))
    if page > 1:
        url += f"&page={page}"
    return url


def search_jumia(query: str, max_results: int = None):
    """
    Cherche `query` sur Jumia et retourne la liste EXHAUSTIVE des produits
    (toutes les pages), sous forme de dicts {name, price, image_url, link}.

    - max_results=None (par défaut) : renvoie tout, jusqu'aux garde-fous
      MAX_PAGES_SAFETY / MAX_RESULTS_SAFETY.
    - max_results=N : s'arrête dès que N produits ont été collectés
      (utile pour un aperçu rapide plutôt qu'une recherche complète).
    """
    all_results = []
    seen_links = set()
    page = 1

    while True:
        url = _build_search_url(query, page)
        try:
            response = requests.get(url, headers=HEADERS, timeout=12)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[scraper] Erreur de connexion à Jumia (page {page}) : {e}")
            break

        page_results = _parse_product_links(response.text, max_results=1000)
        new_results = [r for r in page_results if r["link"] not in seen_links]

        if not new_results:
            break  # page vide ou plus rien de nouveau -> fin de la pagination

        for r in new_results:
            seen_links.add(r["link"])
            all_results.append(r)
            if max_results and len(all_results) >= max_results:
                return all_results
            if len(all_results) >= MAX_RESULTS_SAFETY:
                return all_results

        page += 1
        if page > MAX_PAGES_SAFETY:
            break
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_results if all_results else _fallback_results(query)


def _parse_product_links(html: str, max_results: int = 1000):
    """Extrait les fiches produits d'UNE page de résultats Jumia."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen_links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if not PRODUCT_LINK_RE.search(href):
            continue

        link = urljoin(BASE_URL, href)
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

        price_match = PRICE_RE.search(a_tag.get_text(" ", strip=True))
        price = price_match.group(0) if price_match else ""

        results.append(
            {"name": name, "price": price, "image_url": image_url, "link": link}
        )
        seen_links.add(link)

        if len(results) >= max_results:
            break

    return results


def _fallback_results(query: str):
    """Résultats de secours si le scraping échoue (site down, structure changée, etc.)."""
    return [
        {
            "name": f"{query} (résultat de démonstration {i + 1})",
            "price": "N/A",
            "image_url": None,
            "link": None,
        }
        for i in range(3)
    ]
