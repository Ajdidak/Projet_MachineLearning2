import time
import random
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def _fetch_page(url, session, max_retries=3, backoff=2):
    """
    Récupère une page avec retry + backoff exponentiel.
    Retourne le HTML (str) ou None en cas d'échec définitif.
    """
    for tentative in range(1, max_retries + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Tentative {tentative}/{max_retries} échouée pour {url} : {e}")
            if tentative < max_retries:
                time.sleep(backoff * tentative)  # backoff progressif
    logger.error(f"Abandon après {max_retries} tentatives : {url}")
    return None


def _extraire_produits(html, base_url="https://www.jumia.ci"):
    """
    Parse le HTML d'une page de résultats et retourne une liste de tuples (titre, url_image).
    """
    soup = BeautifulSoup(html, 'html.parser')

    articles = soup.select('article.prd')
    if not articles:
        articles = soup.select('a.core')

    produits = []
    for art in articles:
        img_tag = art.find('img')
        if not img_tag:
            continue
        img_url = img_tag.get('data-src') or img_tag.get('src')
        if not img_url:
            continue

        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = base_url + img_url

        titre_tag = art.find('h3', class_='name') or art.find('div', class_='name')
        if titre_tag:
            titre = titre_tag.text.strip()
        else:
            alt = img_tag.get('alt')
            titre = alt.strip() if alt else "Sans titre"

        produits.append((titre, img_url))

    return produits


def _detecter_derniere_page(html):
    """
    Essaie de détecter s'il existe une page suivante, en cherchant
    un lien/bouton de pagination 'next' dans le HTML.
    Retourne True s'il y a probablement une page suivante.
    """
    soup = BeautifulSoup(html, 'html.parser')
    next_link = soup.select_one('a[aria-label="Next Page"]') or soup.select_one('a.pg[aria-label*="Next"]')
    return next_link is not None


def rechercher_jumia(mot_cle, max_pages=3, delai_min=1.0, delai_max=2.5, limite_produits=None):
    """
    Récupère les produits sur Jumia.ci pour un mot-clé donné, sur plusieurs pages.

    Args:
        mot_cle (str): terme de recherche.
        max_pages (int): nombre maximum de pages à parcourir (protection anti-boucle infinie).
        delai_min / delai_max (float): délai aléatoire (secondes) entre deux requêtes,
            pour limiter le risque de blocage côté serveur.
        limite_produits (int|None): arrête la collecte dès que ce nombre de produits
            est atteint (utile si tu ne veux pas scraper toutes les pages).

    Returns:
        list[tuple[str, str]]: liste de (titre, url_image), dédupliquée.
    """
    if not mot_cle or not mot_cle.strip():
        logger.error("Mot-clé vide.")
        return []

    mot_cle_encode = mot_cle.strip().replace(' ', '%20')
    produits_total = []
    vus = set()  # pour dédupliquer (titre, url_image)

    with requests.Session() as session:
        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"https://www.jumia.ci/catalog/?q={mot_cle_encode}"
            else:
                url = f"https://www.jumia.ci/catalog/?q={mot_cle_encode}&page={page}"

            logger.info(f"Récupération page {page}/{max_pages} : {url}")
            html = _fetch_page(url, session)

            if html is None:
                # Echec réseau définitif sur cette page : on arrête la pagination
                logger.warning("Arrêt de la pagination suite à une erreur réseau.")
                break

            produits_page = _extraire_produits(html)

            if not produits_page:
                logger.info(f"Aucun produit trouvé page {page}, fin de la pagination.")
                break

            nouveaux = 0
            for titre, img_url in produits_page:
                cle = (titre, img_url)
                if cle not in vus:
                    vus.add(cle)
                    produits_total.append(cle)
                    nouveaux += 1

            logger.info(f"Page {page} : {len(produits_page)} produits ({nouveaux} nouveaux).")

            if limite_produits is not None and len(produits_total) >= limite_produits:
                produits_total = produits_total[:limite_produits]
                logger.info(f"Limite de {limite_produits} produits atteinte, arrêt.")
                break

            # Vérifie s'il y a une page suivante avant de continuer
            if not _detecter_derniere_page(html):
                logger.info("Pas de page suivante détectée, fin de la pagination.")
                break

            # Rate limiting : pause aléatoire entre les requêtes (sauf après la dernière page)
            if page < max_pages:
                pause = random.uniform(delai_min, delai_max)
                time.sleep(pause)

    return produits_total


def main():
    mot_cle = input("Entrez le mot-clé du produit recherché : ").strip()
    if not mot_cle:
        print("Mot-clé vide.")
        return

    try:
        max_pages_input = input("Nombre de pages max à scraper (défaut 3) : ").strip()
        max_pages = int(max_pages_input) if max_pages_input else 3
    except ValueError:
        max_pages = 3

    print(f"\nRecherche de '{mot_cle}' sur Jumia.ci (jusqu'à {max_pages} page(s))...\n")
    produits = rechercher_jumia(mot_cle, max_pages=max_pages)

    if not produits:
        print("Aucun produit trouvé.")
        print("Vérifiez votre connexion ou que le mot-clé existe.")
        print("Si le problème persiste, la structure du site a peut-être changé.")
        return

    print(f"\n{len(produits)} produit(s) trouvé(s) au total :\n")
    for idx, (titre, url) in enumerate(produits, start=1):
        aff_titre = titre[:80] + "..." if len(titre) > 80 else titre
        print(f"{idx}. {aff_titre}")
        print(f"   Image : {url}\n")

    try:
        choix = int(input("Entrez le numéro de l'image choisie (ou 0 pour abandonner) : "))
        if choix == 0:
            print("Annulation.")
            return
        if 1 <= choix <= len(produits):
            titre, url = produits[choix - 1]
            print(f"\nVous avez choisi : {titre}")
            print(f"Lien de l'image : {url}")
            print("Copiez ce lien dans votre navigateur pour voir l'image.")
        else:
            print("Numéro invalide.")
    except ValueError:
        print("Veuillez entrer un nombre valide.")


if __name__ == "__main__":
    main()