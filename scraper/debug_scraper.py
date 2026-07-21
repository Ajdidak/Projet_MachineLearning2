"""
DeepCycle — Script de diagnostic du scraper Jumia.

À lancer si search_jumia() ne renvoie que des résultats de démonstration
(voir _fallback_results dans scraper.py). Ce script interroge Jumia pour un
mot-clé donné, affiche des statistiques, et sauvegarde le HTML brut de la
page dans debug_output.html pour inspection manuelle.

Usage (depuis le dossier Scraper/) :
    python debug_scraper.py "smartphone"
"""

import sys
import requests
from scraper import SEARCH_URL, HEADERS, _parse_product_links


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "smartphone"
    url = SEARCH_URL.format(query=query.replace(" ", "+"))
    print(f"Requête : {url}")

    response = requests.get(url, headers=HEADERS, timeout=12)
    print(f"Statut HTTP : {response.status_code}")
    print(f"URL finale (après redirection éventuelle) : {response.url}")

    html = response.text
    with open("debug_output.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML brut sauvegardé dans debug_output.html "
          "(ouvrez-le dans un navigateur ou un éditeur de texte).")

    html_link_count = html.count('.html"')
    print(f"Occurrences brutes de '.html\"' dans la page : {html_link_count}")

    results = _parse_product_links(html, max_results=50)
    print(f"Produits extraits par le parseur actuel : {len(results)}")
    for r in results[:5]:
        print(" -", r["name"][:70], "|", r["price"], "|", r["image_url"])

    if not results:
        print(
            "\nAucun produit détecté. Ouvrez debug_output.html et cherchez "
            "un vrai lien produit (Ctrl+F 'FCFA' ou '.html') pour vérifier "
            "si l'URL de recherche (SEARCH_URL) ou le motif PRODUCT_LINK_RE "
            "dans scraper.py doivent être ajustés en fonction de ce que "
            "Jumia renvoie réellement à ce moment-là."
        )


if __name__ == "__main__":
    main()
