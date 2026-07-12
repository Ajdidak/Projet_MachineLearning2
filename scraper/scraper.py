import os
import time
import random
import logging
import requests
from bs4 import BeautifulSoup

# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_URL = "https://www.jumia.ci"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s : %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================================
# TELECHARGEMENT D'UNE PAGE
# ==========================================================

def fetch_page(url, session, retries=3):
    """
    Télécharge une page HTML.

    Paramètres
    ----------
    url : str
        URL de la page.
    session : requests.Session
        Session HTTP.
    retries : int
        Nombre maximum de tentatives.

    Retour
    ------
    str ou None
    """

    for tentative in range(1, retries + 1):

        try:

            logger.info(f"Téléchargement : {url}")

            response = session.get(
                url,
                headers=HEADERS,
                timeout=10
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as e:

            logger.warning(
                f"Tentative {tentative}/{retries} échouée."
            )

            if tentative < retries:

                attente = random.uniform(1, 2)
                time.sleep(attente)

            else:

                logger.error(e)

    return None


# ==========================================================
# EXTRACTION DES PRODUITS
# ==========================================================

def parse_products(html):
    """
    Extrait les produits du HTML.

    Retourne une liste de dictionnaires.
    """

    soup = BeautifulSoup(html, "html.parser")

    cartes = soup.find_all("a", class_="core")

    produits = []

    vus = set()

    for carte in cartes:

        nom = carte.find(class_="name")

        prix = carte.find("div", class_="prc")

        image = carte.find("img")

        nom = nom.get_text(strip=True) if nom else "Non disponible"

        prix = prix.get_text(strip=True) if prix else "Non disponible"

        if image:

            image = image.get("data-src") or image.get("src")

        else:

            image = None

        cle = (nom, image)

        if cle in vus:
            continue

        vus.add(cle)

        produits.append({

            "nom": nom,

            "prix": prix,

            "image": image

        })

    return produits


# ==========================================================
# RECHERCHE D'UN PRODUIT
# ==========================================================

def rechercher_produits(mot_cle, limite=5):
    """
    Recherche un produit sur Jumia.

    Retourne les premiers résultats.
    """

    if not mot_cle.strip():

        logger.error("Mot-clé vide.")

        return []

    mot_cle = mot_cle.strip()

    url = f"{BASE_URL}/catalog/?q={mot_cle}"

    with requests.Session() as session:

        html = fetch_page(url, session)

        if html is None:

            return []

        produits = parse_products(html)

    logger.info(f"{len(produits)} produits récupérés.")

    return produits[:limite]


# ==========================================================
# TELECHARGEMENT D'UNE IMAGE
# ==========================================================

def telecharger_image(url_image,
                      dossier="images",
                      nom_fichier="produit.jpg"):
    """
    Télécharge une image.
    """

    if url_image is None:

        return None

    os.makedirs(dossier, exist_ok=True)

    chemin = os.path.join(dossier, nom_fichier)

    try:

        response = requests.get(
            url_image,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        with open(chemin, "wb") as f:

            f.write(response.content)

        logger.info(f"Image enregistrée : {chemin}")

        return chemin

    except requests.RequestException as e:

        logger.error(e)

        return None


# ==========================================================
# TEST
# ==========================================================

def main():

    mot = input("Entrez le nom du produit : ")

    produits = rechercher_produits(mot)

    if not produits:

        print("Aucun produit trouvé.")

        return

    print()

    for i, produit in enumerate(produits, start=1):

        print("=" * 60)

        print(f"Produit {i}")

        print(f"Nom   : {produit['nom']}")

        print(f"Prix  : {produit['prix']}")

        print(f"Image : {produit['image']}")

    choix = input(
        "\nTélécharger l'image de quel produit ? (0 pour quitter) : "
    )

    if choix.isdigit():

        choix = int(choix)

        if 1 <= choix <= len(produits):

            telecharger_image(
                produits[choix - 1]["image"],
                nom_fichier=f"produit_{choix}.jpg"
            )


if __name__ == "__main__":

    main()