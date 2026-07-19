"""
EcoSort-Search — Recherche Jumia en ligne de commande.
Permet de tester le scraper directement dans le terminal, sans lancer
l'application Streamlit, et affiche les 5 produits les plus pertinents.

Usage (depuis la racine du projet EcoSort-Search) :
    python Scraper/search_cli.py "smartphone samsung"

Ou sans argument, pour un mode interactif (répète la recherche à volonté) :
    python Scraper/search_cli.py
"""

import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Scraper.scraper import search_jumia

MAX_RESULTS = 5


def print_results(query: str):
    print(f"\nRecherche : \"{query}\"...")
    results = search_jumia(query, max_results=MAX_RESULTS)

    if not results:
        print("Aucun résultat trouvé.")
        return

    print(f"\n{len(results)} résultat(s) trouvé(s) :\n")
    for i, product in enumerate(results, start=1):
        print(f"{i}. {product['name']}")
        print(f"   Prix  : {product.get('price') or 'non communiqué'}")
        print(f"   Image : {product.get('image_url') or 'aucune'}")
        print(f"   Lien  : {product.get('link') or 'aucun'}")
        print()


def main():
    if len(sys.argv) > 1:
        # Mode direct : python search_cli.py "requête"
        query = " ".join(sys.argv[1:])
        print_results(query)
        return

    # Mode interactif : redemande une recherche jusqu'à Ctrl+C ou ligne vide
    print("Mode interactif — tapez une recherche, ou une ligne vide pour quitter.")
    while True:
        try:
            query = input("\nProduit à rechercher > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFin.")
            break
        if not query:
            print("Fin.")
            break
        print_results(query)


if __name__ == "__main__":
    main()
