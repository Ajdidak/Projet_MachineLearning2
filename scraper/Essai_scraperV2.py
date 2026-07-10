import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def _fetch_page(url, session, max_retries=3, backoff=2):
    """Récupère une page avec retry + backoff exponentiel."""
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


def _extraire_produits(html, base_url="https://www.jumia.ci"):
    """Parse le HTML d'une page de résultats et retourne une liste de (titre, url_image)."""
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


def _detecter_page_suivante(html):
    """Vérifie s'il existe un lien vers la page suivante."""
    soup = BeautifulSoup(html, 'html.parser')
    # Jumia utilise souvent un lien avec aria-label="Next Page" ou une classe 'pg'
    next_link = soup.select_one('a[aria-label="Next Page"]') or soup.select_one('a.pg[aria-label*="Next"]')
    return next_link is not None


def _score_pertinence(titre, mots_cle):
    """
    Calcule un score = nombre de mots du mot-clé présents dans le titre (en minuscules).
    """
    titre_lower = titre.lower()
    return sum(1 for mot in mots_cle if mot in titre_lower)


def rechercher_jumia(mot_cle, max_pages=50, delai_min=1.0, delai_max=2.5):
    """
    Récupère tous les produits sur Jumia.ci pour un mot-clé donné, en parcourant
    toutes les pages jusqu'à la dernière (ou jusqu'à max_pages pour sécurité).

    Retourne la liste complète de (titre, url_image).
    """
    if not mot_cle or not mot_cle.strip():
        logger.error("Mot-clé vide.")
        return []

    mots_cle = mot_cle.strip().lower().split()  # pour le scoring
    mot_cle_encode = mot_cle.strip().replace(' ', '%20')
    produits_total = []
    vus = set()

    with requests.Session() as session:
        page = 1
        while page <= max_pages:
            if page == 1:
                url = f"https://www.jumia.ci/catalog/?q={mot_cle_encode}"
            else:
                url = f"https://www.jumia.ci/catalog/?q={mot_cle_encode}&page={page}"

            logger.info(f"Récupération page {page} : {url}")
            html = _fetch_page(url, session)

            if html is None:
                logger.warning("Erreur réseau, arrêt de la pagination.")
                break

            produits_page = _extraire_produits(html)
            if not produits_page:
                logger.info(f"Aucun produit sur la page {page}, fin de la pagination.")
                break

            # Ajout des nouveaux produits (déduplication)
            nouveaux = 0
            for titre, img_url in produits_page:
                cle = (titre, img_url)
                if cle not in vus:
                    vus.add(cle)
                    produits_total.append(cle)
                    nouveaux += 1

            logger.info(f"Page {page} : {len(produits_page)} produits ({nouveaux} nouveaux)")

            # Vérifier s'il y a une page suivante
            if not _detecter_page_suivante(html):
                logger.info("Pas de page suivante détectée, fin de la pagination.")
                break

            # Pause aléatoire avant la prochaine requête
            pause = random.uniform(delai_min, delai_max)
            time.sleep(pause)

            page += 1

        if page > max_pages:
            logger.warning(f"Limite de {max_pages} pages atteinte, arrêt.")

    # Calcul du score de pertinence pour chaque produit
    for idx, (titre, url) in enumerate(produits_total):
        score = _score_pertinence(titre, mots_cle)
        # On stocke le score dans un nouveau tuple ou on modifie la liste ?
        # On va reconstruire une liste de tuples (titre, url, score)
        produits_total[idx] = (titre, url, score)

    # Trier par score décroissant
    produits_total.sort(key=lambda x: x[2], reverse=True)

    # On retourne uniquement les 5 premiers (ou moins)
    top_n = 5
    meilleurs = produits_total[:top_n]

    # On remet au format (titre, url) pour la sortie
    return [(titre, url) for titre, url, _ in meilleurs]


def main():
    mot_cle = input("Entrez le mot-clé du produit recherché : ").strip()
    if not mot_cle:
        print("Mot-clé vide.")
        return

    print(f"\nRecherche de '{mot_cle}' sur Jumia.ci (toutes les pages)...")
    print("Cela peut prendre quelques secondes...\n")

    produits = rechercher_jumia(mot_cle)

    if not produits:
        print("Aucun produit trouvé.")
        print("Vérifiez votre connexion ou que le mot-clé existe.")
        return

    print(f"\nVoici les {len(produits)} images les plus pertinentes pour '{mot_cle}':\n")
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