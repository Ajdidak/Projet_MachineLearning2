import requests
from bs4 import BeautifulSoup

# Demander à l'utilisateur le produit à rechercher
recherche = input("Entrez le nom du produit : ").strip()

# Construire l'URL de recherche
url = f"https://www.jumia.ci/catalog/?q={recherche}"

try:
    # Envoyer une requête HTTP vers Jumia
    response = requests.get(
        url,
        headers={
             "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
        },
        timeout=10
    )

    # Vérifier que la requête a réussi
    if response.status_code == 200:

        # Récupérer le code HTML de la page
        html = response.text

        # Enregistrer le HTML dans un fichier (utile pour le débogage)
        with open("jumia.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("Le fichier jumia.html a été enregistré avec succès.")

        # Analyser le HTML avec BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Récupérer tous les produits
        produits = soup.find_all("a", class_="core")

        print(f"\n{len(produits)} produits trouvés.\n")

        # Liste qui va contenir les informations des produits
        liste_produits = []

        # Parcourir les 5 premiers produits
        for i, produit in enumerate(produits[:5], start=1):

            # Récupérer le nom
            nom = produit.find(class_="name")
            nom = nom.get_text(strip=True) if nom else "Non disponible"

            # Récupérer le prix
            prix = produit.find("div", class_="prc")
            prix = prix.get_text(strip=True) if prix else "Non disponible"

            # Récupérer l'image
            img = produit.find("img")
            if img:
                image = img.get("data-src") or img.get("src")
            else:
                image = "Non disponible"

            # Récupérer le lien
            href = produit.get("href")
            if href:
                lien = "https://www.jumia.ci" + href
            else:
                lien = "Non disponible"

            # Ajouter les informations dans la liste
            liste_produits.append({
                "nom": nom,
                "prix": prix,
                "image": image,
                "lien": lien
            })

            # Afficher les informations
            print("=" * 60)
            print(f"Produit {i}")
            print(f"Nom   : {nom}")
            print(f"Prix  : {prix}")
            print(f"Image : {image}")
            print(f"Lien  : {lien}")

        # Afficher la liste complète
        print("\n===== Liste des produits récupérés =====\n")

        for produit in liste_produits:
            print(produit)

    else:
        print(f"Erreur HTTP : {response.status_code}")

except requests.exceptions.RequestException as e:
    print("Erreur de connexion :", e)

print("\nFin du programme.")