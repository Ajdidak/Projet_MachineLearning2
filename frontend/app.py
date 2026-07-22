"""
DeepCycle — Frontend Streamlit.
Ne contient QUE l'affichage : toute la logique métier (scraping + IA)
est déléguée à Backend.pipeline, qui fait le lien avec Scraper et Model_Dl.
"""

import sys
import html
import random
import pathlib
import base64

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from backend.pipeline import search_products, classify_product
from model_DL.model_utils import CATEGORY_COLORS, CATEGORY_LABELS, predict_from_image

_ASSETS_DIR = pathlib.Path(__file__).resolve().parent / "assets"

# logo.png est en RGB sans canal alpha : son fond noir forme un carré opaque,
# discret sur le thème sombre mais très visible sur le thème clair. Le
# pictogramme a donc été détouré (fond transparent, mot « DeepCycle » retiré
# puisque le titre est déjà écrit à côté). On garde l'original en repli.
LOGO_PATH = _ASSETS_DIR / "logo_transparent.png"
if not LOGO_PATH.exists():
    LOGO_PATH = _ASSETS_DIR / "logo.png"

# L'icône d'onglet du navigateur reste l'image d'origine : elle est carrée et
# son fond sombre n'y pose aucun problème.
FAVICON_PATH = _ASSETS_DIR / "logo.png"


def _load_logo_base64():
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

LOGO_B64 = _load_logo_base64()
#st.set_page_config(page_title="DeepCycle", page_icon="♻️", layout="wide")
st.set_page_config(
    page_title="DeepCycle",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "♻️",
    layout="wide",
)

MAX_SEARCH_RESULTS = 5  # la recherche renvoie toujours 5 résultats, pas plus

# --- Thème : DOIT être initialisé AVANT l'injection du CSS -------------------
# Le widget st.toggle plus bas utilise key="dark_mode", donc Streamlit lit et
# écrit automatiquement st.session_state.dark_mode. Au rerun qui suit un clic,
# la valeur est déjà à jour ici, tout en haut du script : le CSS injecté
# correspond donc toujours à l'état du bouton.
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # sombre par défaut


def classify_uploaded_image(image) -> dict:
    """
    Classifie une photo fournie directement par l'utilisateur, sans passer par
    Jumia. Retourne le même dictionnaire que classify_product() du backend :
    {"category": str, "source": "ia" | "demo", "confidence": float | None}

    Contrairement à un produit Jumia, il n'y a ici aucun nom : aucun repli par
    mots-clés n'est possible. Le Bac D3E est donc inatteignable par cette voie,
    cette classe étant absente du dataset Kaggle sur lequel le modèle a été
    entraîné. L'interface en avertit l'utilisateur.
    """
    category, confidence = predict_from_image(image)

    if category is not None:
        return {"category": category, "source": "ia", "confidence": confidence}

    # Aucun modèle chargé : on annonce clairement le mode démo plutôt que de
    # faire croire à une analyse. « electronique » est exclu du tirage, car le
    # modèle réel ne peut jamais produire cette classe par cette voie : la
    # proposer contredirait l'avertissement affiché juste en dessous.
    return {
        "category": random.choice([c for c in CATEGORY_LABELS if c != "electronique"]),
        "source": "demo",
        "confidence": None,
    }


def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# --- Design tokens : blanc dominant, bleu en accent, orange très discret ---

BIN_COLORS_ORDERED = [
    ("jaune", "#F2C94C", "Jaune"),
    ("vert", "#27AE60", "Vert"),
    ("bleu", "#2D9CDB", "Bleu"),
    ("electronique", "#7D7D7D", "D3E"),
    ("marron", "#6D4C41", "Marron"),
]

SOURCE_LABELS = {
    "ia": "🧠 Prédit par le modèle de Deep Learning",
    "mots-cles": "🔤 Détecté par mots-clés (règle D3E / complément)",
    "demo": "🎲 Mode démo — aucun modèle chargé pour l'instant",
}

CATEGORY_DESCRIPTIONS = {
    "jaune": "Emballages légers : bouteilles plastique, canettes, boîtes de conserve, briques de lait, flacons, cartons.",
    "vert": "Uniquement le verre d'emballage : bouteilles, pots de confiture, bocaux (vaisselle cassée interdite).",
    "bleu": "Papiers graphiques propres : prospectus, journaux, magazines, cahiers, livres, enveloppes.",
    "electronique": "Tout appareil à pile, batterie ou prise : smartphones, écouteurs, chargeurs, mixeurs, montres.",
    "marron": "Déchets résiduels non recyclables : restes alimentaires, sachets souples, produits d'hygiène.",
}

CATEGORY_TITLES = {
    "jaune": "Poubelle JAUNE",
    "vert": "Poubelle VERTE",
    "bleu": "Poubelle BLEUE",
    "electronique": "Bac D3E — Électronique",
    "marron": "Poubelle MARRON",
}

CATEGORY_ICONS = {
    "jaune": "🟡",
    "vert": "🟢",
    "bleu": "🔵",
    "electronique": "🎛️",
    "marron": "🟤",
}

# Exemples cliquables sous la barre de recherche. Choisis pour couvrir quatre
# poubelles différentes : l'utilisateur découvre la variété des cas traités
# sans avoir à chercher quoi taper devant une page vide.
# Paires (libellé affiché, terme réellement recherché). Sur cinq colonnes,
# « bouteille d'eau » ou « sachet plastique » passaient à la ligne et
# déformaient la rangée : on affiche court, on cherche précis.
SUGGESTIONS = [
    ("bouteille", "bouteille d'eau"),
    ("confiture", "pot de confiture"),
    ("écouteurs", "écouteurs"),
    ("journal", "journal"),
    ("sachet", "sachet plastique"),
]

PLACEHOLDER_IMG = (
    "data:image/svg+xml;charset=UTF-8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E"
    "%3Crect width='100%25' height='100%25' fill='%23F2F2F2'/%3E"
    "%3Ctext x='50%25' y='50%25' font-family='sans-serif' font-size='14' "
    "fill='%23999999' text-anchor='middle' dy='.3em'%3EImage indisponible%3C/text%3E"
    "%3C/svg%3E"
)


# --- Palettes des deux thèmes ------------------------------------------------
# Une seule source de vérité par thème. Le CSS ne contient plus qu'un
# marqueur __THEME_VARS__ remplacé à l'exécution par la palette choisie :
# inutile de dupliquer les règles, tout le reste du CSS lit les variables.

THEMES = {
    "dark": {
        "bg-main": "#0A0E1A",
        "bg-card": "#131A2B",
        "border-card": "#1F2937",
        "text-primary": "#F0F2F5",
        "text-secondary": "#9BA3B0",
        "footer-color": "#6B7280",
        "input-bg": "#131A2B",
        # Texte indicatif du champ : blanc atténué, lisible sur fond sombre
        # sans concurrencer le texte réellement saisi.
        "placeholder": "rgba(255, 255, 255, 0.42)",
        # Sur fond sombre, une ombre noire marquée donne du relief.
        "shadow-card": "0 1px 3px rgba(0, 0, 0, 0.30)",
        "shadow-hover": "0 10px 24px rgba(46, 213, 115, 0.15)",
        "shadow-banner": "0 10px 30px rgba(0, 0, 0, 0.40)",
    },
    "light": {
        "bg-main": "#F7F9FC",
        "bg-card": "#FFFFFF",
        "border-card": "#E4E8EE",
        "text-primary": "#1A1F2B",
        "text-secondary": "#5B6472",
        "footer-color": "#9AA3AF",
        "input-bg": "#FFFFFF",
        # En mode clair, un placeholder blanc serait invisible sur fond blanc :
        # on utilise ici un gris foncé, lui aussi atténué.
        "placeholder": "rgba(26, 31, 43, 0.40)",
        # Sur fond clair, la même ombre noire ferait sale : on l'adoucit
        # nettement et on la teinte de bleu-gris.
        "shadow-card": "0 1px 3px rgba(16, 24, 40, 0.08)",
        "shadow-hover": "0 10px 24px rgba(46, 213, 115, 0.22)",
        "shadow-banner": "0 10px 30px rgba(16, 24, 40, 0.18)",
    },
}


def build_theme_vars(is_dark: bool) -> str:
    """Transforme la palette choisie en bloc CSS `:root { --xxx: valeur; }`."""
    palette = THEMES["dark" if is_dark else "light"]
    declarations = "\n    ".join(f"--{name}: {value};" for name, value in palette.items())
    return f":root {{\n    {declarations}\n}}"


FONT_SIZES = {
    "logo_size": "3.2rem",               # "DeepCycle" dans le bloc d'accueil centré
    "logo_size_compact": "1.6rem",       # "DeepCycle" une fois la recherche lancée
    "subtitle_size": "1.05rem",          # accroche sous le logo
    "section_title_size": "1.5rem",      # titres de section ("Résultats de recherche"...)
    "legend_label_size": "1.02rem",      # nom court dans la vitrine des catégories
    # 1.08rem était trop gros pour 5 colonnes : c'est ce qui forçait la
    # troncature des descriptions. Réduit pour que le texte tienne entier.
    "legend_text_size": "0.86rem",       # description dans la vitrine des catégories
    "product_name_size": "0.8rem",       # nom du produit affiché sur chaque carte
    "product_price_size": "0.92rem",     # prix affiché sur chaque carte
    "button_text_size": "0.95rem",       # texte à l'intérieur des boutons (Rechercher, Choisir...)
    "result_title_size": "1.7rem",       # nom de la poubelle dans la fenêtre de résultat
    "result_source_size": "0.8rem",      # badge "🧠 Prédit par le modèle..." dans la fenêtre
    "footer_size": "0.75rem",            # ligne de crédit tout en bas de la page
}
# ============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

__THEME_VARS__

html, body, [class^="css"], [class*=" css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background-color: var(--bg-main);
}

/* La barre d'outils Streamlit garde sinon sa couleur par défaut et forme
   un bandeau clair incohérent en haut de la page en mode sombre. */
header[data-testid="stHeader"] {
    background-color: transparent;
    height: 0;
}

/* Streamlit réserve par défaut 6rem de marge en haut du conteneur principal
   (et 10rem en bas), pensées pour des tableaux de bord avec barre latérale.
   Sur une page d'accueil centrée, ça repousse le logo et la recherche très
   bas et laisse un grand vide en fin de page. C'est la cause principale de
   l'espace au-dessus de la barre de recherche — les marges de .eco-hero ne
   représentaient qu'une petite part du total. */
div.block-container,
div[data-testid="stAppViewBlockContainer"] {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Texte des blocs st.markdown / st.write (ex. « Produit : ... » dans la
   fenêtre de résultat) : sans ça il reste noir et devient illisible sur le
   fond sombre de la modale. */
div[data-testid="stMarkdownContainer"] {
    color: var(--text-primary);
}

/* Fenêtre modale du résultat (st.dialog) : elle est rendue hors de .stApp,
   elle n'hérite donc d'aucun de nos styles si on ne la cible pas. */
div[role="dialog"] {
    background-color: var(--bg-main) !important;
}

div[role="dialog"] h1,
div[role="dialog"] h2,
div[role="dialog"] h3 {
    color: var(--text-primary);
}

/* Interrupteur de thème : petit et discret, aligné avec la barre du haut. */
div[data-testid="stToggle"] label,
div[data-testid="stCheckbox"] label {
    color: var(--text-secondary) !important;
    font-size: 0.82rem;
}

.theme-switch-wrapper {
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

/* --- Puces de suggestion ---------------------------------------------------
   Ce sont de vrais st.button (donc cliquables), re-stylés en pastilles.
   Problème : ils partagent le sélecteur div.stButton avec les boutons
   « Choisir ce produit ». Impossible de les distinguer dans le DOM sous
   Streamlit 1.38, qui n'expose pas encore la clé du widget en classe CSS.
   Solution : les deux ne sont JAMAIS affichés en même temps — les puces sur
   l'écran d'accueil, les boutons produit une fois la recherche faite. Le bloc
   ci-dessous n'est donc injecté que sur l'écran d'accueil (voir
   __SUGGESTION_CSS__ côté Python), où il surcharge sans risque. */
__SUGGESTION_CSS__

.suggestion-label {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin: 20px 0 9px 0;
}

/* --- Zone d'envoi de photo -------------------------------------------------
   st.file_uploader affiche par défaut un grand encadré « Drag and drop file
   here » qui écraserait la barre de recherche. On le réduit à une bande
   discrète, cohérente avec le reste. */
div[data-testid="stFileUploader"] section {
    background: var(--bg-card);
    border: 1px dashed var(--border-card);
    border-radius: 14px;
    padding: 10px 14px;
}

div[data-testid="stFileUploader"] section:hover {
    border-color: #2ED573;
}

/* Traduction en français des libellés codés en dur par Streamlit.
   Streamlit n'expose aucun paramètre pour ces textes : on masque donc les
   originaux anglais et on injecte les versions françaises via ::before /
   ::after. La ligne principale (« Drag and drop… ») et la ligne de limite
   (« Limit 200MB… ») sont deux enfants du même bloc d'instructions. */
div[data-testid="stFileUploaderDropzoneInstructions"] span,
div[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: none;
}

div[data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "Glissez-déposez une image ici";
    display: block;
    color: var(--text-primary);
    font-size: 0.9rem;
}

div[data-testid="stFileUploaderDropzoneInstructions"]::after {
    content: "200 Mo maximum par fichier · PNG, JPG, JPEG, WEBP";
    display: block;
    color: var(--text-secondary);
    font-size: 0.78rem;
    margin-top: 2px;
}

/* Bouton « Browse files » -> « Parcourir ». On annule sa taille de police
   pour effacer le texte anglais, puis on écrit le français via ::after. */
div[data-testid="stFileUploader"] section button {
    font-size: 0 !important;
    color: #2ED573 !important;
    border: 1px solid rgba(46, 213, 115, 0.5) !important;
    background: transparent !important;
}

div[data-testid="stFileUploader"] section button::after {
    content: "Parcourir";
    font-size: 0.82rem;
    font-weight: 600;
}

div[data-testid="stFileUploader"] small {
    color: var(--text-secondary);
}

.uploaded-preview {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 14px;
    padding: 14px;
    text-align: center;
}

/* L'interrupteur ne doit pas peser une ligne entière : sans ça, ses marges
   par défaut ajoutent une vingtaine de pixels au-dessus du logo. */
div[data-testid="stToggle"] {
    margin-bottom: 0;
}

/* --- Alignement de la barre de recherche -----------------------------------
   Le champ et le bouton vivent dans deux colonnes Streamlit distinctes.
   Chacune apporte ses propres marges, et le champ est enveloppé de plusieurs
   div baseweb qui ajoutent un espacement invisible : le bouton se retrouvait
   décalé vers le bas de quelques pixels malgré une hauteur identique.
   On neutralise ces marges et on centre verticalement les deux colonnes. */
div[data-testid="stForm"] {
    padding: 0;
    border: none;
}

div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
    align-items: center;
    gap: 10px;
}

div[data-testid="stForm"] div[data-testid="stTextInput"],
div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
    margin-bottom: 0;
}

/* La bordure verte n'est dessinée que sur le conteneur LE PLUS EXTERNE.
   Auparavant la même règle visait aussi les deux div baseweb imbriqués à
   l'intérieur : trois bordures superposées étaient peintes, et celle du div
   le plus interne débordait sur la droite — c'est le trait vertical vert qui
   apparaissait entre le champ et le bouton Rechercher. */
div[data-testid="stTextInput"] > div {
    height: __SEARCH_INPUT_HEIGHT__;
    display: flex;
    align-items: center;
    background-color: var(--input-bg) !important;
    border: 1px solid #2ED573 !important;
    border-radius: 999px !important;
    box-shadow: var(--shadow-card);
    overflow: hidden;
}

/* Les wrappers internes deviennent totalement neutres : ni bordure, ni fond,
   ni ombre. Ils ne servent qu'à porter l'input. */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 999px !important;
}

/* Hauteur et taille de police du champ : plus grandes sur l'écran d'accueil
   (la recherche est l'action principale), réduites une fois les résultats
   affichés. Les deux valeurs sont injectées depuis Python — un simple div
   enveloppant ne marcherait pas, Streamlit rend chaque bloc comme un frère
   dans le DOM, jamais comme un parent. */
div[data-testid="stTextInput"] input {
    background-color: var(--input-bg) !important;
    border: none;
    height: __SEARCH_INPUT_HEIGHT__;
    padding-left: 22px;
    font-size: __SEARCH_INPUT_FONT__;
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    caret-color: var(--text-primary);
}

/* Texte indicatif (« Cherchez un produit... ») : blanc atténué en mode
   sombre, gris foncé atténué en mode clair (voir --placeholder dans THEMES).
   -webkit-text-fill-color est nécessaire : sur les moteurs WebKit/Blink, la
   seule propriété `color` ne suffit pas à repeindre le placeholder. */
div[data-testid="stTextInput"] input::placeholder {
    color: var(--placeholder) !important;
    -webkit-text-fill-color: var(--placeholder) !important;
    opacity: 1;
}

/* --- Bloc d'accueil (hero) -------------------------------------------------
   Deux états : « plein » tant qu'aucune recherche n'a été lancée, puis
   « compact » une fois les résultats affichés — le logo rétrécit et les
   marges se resserrent pour laisser la vedette aux produits. */

.eco-hero {
    text-align: center;
    /* Marge haute volontairement faible : l'interrupteur de thème occupe déjà
       une ligne au-dessus, et le conteneur Streamlit apporte son propre
       padding. Trop d'air ici et la recherche tombe sous la ligne de flottaison. */
    padding: 0.4rem 0 1.4rem 0;
}

.eco-hero.is-compact {
    padding: 0.6rem 0 0.4rem 0;
}

.eco-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: var(--text-primary);
    font-size: __LOGO_SIZE__;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
}

.eco-hero.is-compact .eco-logo {
    font-size: __LOGO_SIZE_COMPACT__;
}

/* Le « Cycle » de DeepCycle : c'est lui qui porte la couleur de la marque. */
.eco-logo-accent {
    color: #2ED573;
}

/* Le pictogramme est détouré, donc plus large que haut : on le dimensionne
   sur la hauteur du texte pour qu'il reste solidaire du mot « DeepCycle »
   quelle que soit la taille de police (accueil ou mode compact). */
.eco-logo img {
    height: 1.15em;
    width: auto;
}

.eco-subtitle {
    color: var(--text-secondary);
    font-size: __SUBTITLE_SIZE__;
    margin-top: 10px;
    font-weight: 400;
}

.eco-hero.is-compact .eco-subtitle {
    display: none;
}

.section-title {
    color: var(--text-primary);
    font-size: __SECTION_TITLE_SIZE__;
    font-weight: 700;
    /* La couleur seule ne suffisait pas : sans width ni style, aucune bordure
       n'est peinte. Les trois propriétés sont obligatoires. */
    border-left: 4px solid #2ED573;
    padding-left: 12px;
    margin: 2.2rem 0 1.1rem 0;
    line-height: 1.3;
}

/* Les colonnes Streamlit s'étirent déjà à la même hauteur ; en donnant
   height:100% à la carte, toutes les cartes d'une rangée s'alignent sur la
   plus haute SANS qu'on ait à figer une hauteur en pixels. C'est ce qui
   permet de supprimer la troncature du texte. */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.bin-showcase-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 12px;
    padding: 0 14px 18px 14px;
    text-align: center;
    height: 100%;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.bin-showcase-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
}

/* Le bandeau de couleur épouse le haut de la carte. Les coins arrondis ne
   valent que pour lui, d'où le border-radius partiel. */
.bin-showcase-bar {
    height: 5px;
    width: calc(100% + 28px);
    margin: 0 -14px 16px -14px;
    border-radius: 12px 12px 0 0;
    flex-shrink: 0;
}

/* Pastille colorée : la couleur de la poubelle est reprise en fond translucide
   derrière l'icône, ce qui lie visuellement l'icône au bandeau du haut. */
.bin-showcase-icon {
    font-size: 1.35rem;
    width: 46px;
    height: 46px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    flex-shrink: 0;
}

.bin-showcase-title {
    font-weight: 700;
    color: var(--text-primary);
    font-size: __LEGEND_LABEL_SIZE__;
    margin-bottom: 7px;
    flex-shrink: 0;
}

/* Plus de -webkit-line-clamp : c'est lui qui coupait les descriptions au
   milieu d'un mot (« flacons, cartons, » sans fin). La carte s'adapte
   désormais au texte au lieu de l'inverse. */
.bin-showcase-desc {
    color: var(--text-secondary);
    font-size: __LEGEND_TEXT_SIZE__;
    line-height: 1.45;
}

.product-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 10px 10px 0 0;
    padding: 12px 12px 8px 12px;
    text-align: center;
    height: 250px;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-card);
}

/* La carte réagit au survol comme les autres : sans ça, elle était le seul
   élément cliquable de la page à paraître inerte. */
.product-card:hover {
    border-color: rgba(46, 213, 115, 0.55);
}

.product-card img {
    width: 100%;
    height: 120px;
    object-fit: contain;
    /* Fond blanc volontaire dans les deux thèmes : les photos produit de
       Jumia sont détourées sur blanc, un fond sombre ferait apparaître un
       rectangle blanc disgracieux autour de chaque article. */
    background: #FFFFFF;
    margin-bottom: 8px;
    border-radius: 6px;
}

.product-name {
    font-size: __PRODUCT_NAME_SIZE__;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.3;
    margin-bottom: 6px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex-grow: 1;
}

.product-price {
    color: #2ED573;
    font-weight: 700;
    font-size: __PRODUCT_PRICE_SIZE__;
}

/* Boutons « Choisir ce produit » : soudés sous la carte produit, d'où les
   coins hauts carrés.
   Ils passent en style « contour » : répété cinq fois côte à côte, le dégradé
   plein saturait la rangée et entrait en concurrence avec le bouton
   Rechercher. Le dégradé ne remplit plus le bouton qu'au survol, ce qui
   désigne clairement l'élément visé. */
div.stButton > button {
    background: transparent;
    color: #2ED573;
    border: 1px solid rgba(46, 213, 115, 0.5);
    border-top: none;
    border-radius: 0 0 10px 10px;
    width: 100%;
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    padding: 9px 0;
    font-size: __BUTTON_TEXT_SIZE__;
    transition: background 0.15s ease, color 0.15s ease;
}

/* Bouton « Rechercher ». Streamlit rend les boutons de formulaire dans
   stFormSubmitButton, PAS dans stButton : sans ce sélecteur dédié, la règle
   ci-dessus ne l'atteint pas et `type="primary"` lui laisse le rouge corail
   par défaut de Streamlit. Le !important est nécessaire car les styles
   internes de Streamlit sont plus spécifiques. */
div[data-testid="stFormSubmitButton"] button,
button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"] {
    background: linear-gradient(90deg, #2E86FF, #2ED573) !important;
    color: white !important;
    border: none !important;
    border-radius: 999px !important;
    width: 100%;
    height: __SEARCH_INPUT_HEIGHT__;
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: __SEARCH_INPUT_FONT__;
    transition: opacity 0.15s ease;
}

div[data-testid="stFormSubmitButton"] button:hover,
button[kind="primaryFormSubmit"]:hover,
button[kind="secondaryFormSubmit"]:hover {
    opacity: 0.88;
    color: white !important;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #2E86FF, #2ED573);
    border-color: transparent;
    color: white;
}

.result-banner {
    padding: 40px 28px 32px 28px;
    border-radius: 20px;
    text-align: center;
    color: white;
    margin-top: 6px;
    box-shadow: var(--shadow-banner);
}

.result-icon-circle {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.22);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.1rem;
    margin: 0 auto 16px auto;
}

.result-banner h1 {
    font-size: __RESULT_TITLE_SIZE__;
    margin: 0 0 8px 0;
    color: white;
    font-weight: 700;
}

.result-description {
    font-size: 0.92rem;
    color: rgba(255, 255, 255, 0.92);
    max-width: 380px;
    margin: 0 auto 16px auto;
    line-height: 1.5;
}

.result-source {
    display: inline-block;
    background: rgba(255, 255, 255, 0.22);
    padding: 5px 16px;
    border-radius: 20px;
    font-size: __RESULT_SOURCE_SIZE__;
}

.confidence-track {
    width: 220px;
    height: 6px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    margin: 16px auto 0 auto;
    overflow: hidden;
}

.confidence-fill {
    height: 100%;
    background: white;
}

.confidence-caption {
    margin-top: 6px;
    font-size: 0.78rem;
    color: rgba(255, 255, 255, 0.85);
}

.eco-footer {
    text-align: center;
    color: var(--footer-color);
    font-size: __FOOTER_SIZE__;
    margin-top: 50px;
}

[data-testid="stAlert"] {
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-card);
}

</style>
"""







# --- État de session ---------------------------------------------------------
# Initialisé AVANT la génération du CSS : la taille du champ de recherche et
# le repliement du bloc d'accueil dépendent tous deux de la présence de
# résultats.

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "prediction" not in st.session_state:
    st.session_state.prediction = None
# Résultat d'une photo envoyée par l'utilisateur : {"image": PIL, "result": dict}
if "photo_result" not in st.session_state:
    st.session_state.photo_result = None

has_results = bool(st.session_state.search_results)
# « Quelque chose à montrer » : résultats Jumia OU analyse de photo. C'est ce
# qui déclenche le repli du bloc d'accueil et le retrait des sections
# pédagogiques — pas uniquement la recherche.
has_content = has_results or st.session_state.photo_result is not None

CUSTOM_CSS = CUSTOM_CSS.replace(
    "__SEARCH_INPUT_HEIGHT__", "48px" if has_content else "56px"
).replace(
    "__SEARCH_INPUT_FONT__", FONT_SIZES["button_text_size"] if has_content else "1.05rem"
)

# Style « pastille » des suggestions : injecté uniquement sur l'écran
# d'accueil, où aucun bouton produit n'est affiché (voir le commentaire dans
# le CSS). Ailleurs, le marqueur est simplement effacé.
SUGGESTION_CSS = """
div.stButton > button {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-card);
    border-top: 1px solid var(--border-card);
    border-radius: 999px;
    padding: 7px 4px;
    font-weight: 400;
    font-size: 0.82rem;
    /* Empêche un libellé un peu long de passer à la ligne et de rendre sa
       pastille plus haute que ses voisines. */
    white-space: nowrap;
    transition: border-color 0.15s ease, color 0.15s ease;
}

div.stButton > button:hover {
    background: transparent;
    border-color: #2ED573;
    color: #2ED573;
}
"""
CUSTOM_CSS = CUSTOM_CSS.replace(
    "__SUGGESTION_CSS__", "" if has_content else SUGGESTION_CSS
)

for _key, _value in FONT_SIZES.items():
    CUSTOM_CSS = CUSTOM_CSS.replace(f"__{_key.upper()}__", _value)

# La palette dépend du thème courant : on l'injecte au dernier moment, juste
# avant d'envoyer la feuille de style au navigateur.
CUSTOM_CSS = CUSTOM_CSS.replace("__THEME_VARS__", build_theme_vars(st.session_state.dark_mode))

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Interrupteur de thème, discret en haut à droite ------------------------

_, col_theme = st.columns([6, 1])
with col_theme:
    st.markdown('<div class="theme-switch-wrapper">', unsafe_allow_html=True)
    # On ne passe QUE `key`, jamais `value` : la valeur initiale a déjà été
    # posée dans st.session_state plus haut. Passer les deux déclencherait
    # l'avertissement Streamlit « widget created with a default value but
    # also had its value set via the Session State API ».
    st.toggle(
        "🌙 Sombre" if st.session_state.dark_mode else "☀️ Clair",
        key="dark_mode",
        help="Basculer entre le thème sombre et le thème clair",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# --- Bloc d'accueil : logo + accroche, centré -------------------------------
# Il se replie automatiquement (classe `is-compact`) dès qu'une recherche a
# renvoyé des résultats, pour ne pas voler la place aux produits.

logo_img_tag = (
    f'<img src="data:image/png;base64,{LOGO_B64}" alt="" />' if LOGO_B64 else "♻️"
)
hero_class = "eco-hero is-compact" if has_content else "eco-hero"

st.markdown(
    f"""
    <div class="{hero_class}">
        <div class="eco-logo">{logo_img_tag}<span>Deep<span class="eco-logo-accent">Cycle</span></span></div>
        <div class="eco-subtitle">La certitude, avant le geste.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Barre de recherche, centrée sous le logo -------------------------------

_, col_form, _ = st.columns([1, 6, 1] if has_content else [1, 3, 1])

with col_form:
    with st.form(key="search_form", clear_on_submit=False, border=False):
        col_search, col_search_btn = st.columns([4, 1])
        with col_search:
            query = st.text_input(
                "Nom du produit", placeholder="Cherchez un produit, une marque, ...",
                label_visibility="collapsed",
            )
        with col_search_btn:
            search_clicked = st.form_submit_button("Rechercher", type="primary")


def _launch_search(term: str):
    """Lance une recherche Jumia et relance le script pour rafraîchir la mise
    en page. Factorisé car appelé à deux endroits : le formulaire et les
    puces de suggestion."""
    with st.spinner("Recherche en cours sur Jumia..."):
        st.session_state.search_results = search_products(
            term, max_results=MAX_SEARCH_RESULTS
        )
    st.session_state.selected_product = None
    st.session_state.prediction = None
    st.session_state.photo_result = None
    if st.session_state.search_results:
        # Relance indispensable : `has_content` et le CSS ont été calculés tout
        # en haut du script, AVANT que la recherche ne remplisse
        # search_results. Sans ce rerun, le bloc d'accueil resterait déplié et
        # le champ à sa grande taille pendant tout ce cycle.
        _rerun()
    else:
        st.info("Aucun résultat trouvé, réessayez avec un autre mot-clé.")


if search_clicked:
    if not query.strip():
        st.warning("Merci d'indiquer un nom de produit avant de lancer la recherche.")
    else:
        _launch_search(query.strip())

# --- Puces de suggestion et envoi de photo : écran d'accueil uniquement -----

if not has_content:
    _, col_sugg, _ = st.columns([1, 3, 1])
    with col_sugg:
        st.markdown(
            '<div class="suggestion-label">Essayez par exemple</div>',
            unsafe_allow_html=True,
        )
        for chip_col, (libelle, terme) in zip(st.columns(len(SUGGESTIONS)), SUGGESTIONS):
            with chip_col:
                if st.button(libelle, key=f"sugg_{libelle}"):
                    _launch_search(terme)

        st.markdown(
            '<div class="suggestion-label">ou analysez directement votre propre photo</div>',
            unsafe_allow_html=True,
        )
        photo = st.file_uploader(
            "Photo du déchet",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        if photo is not None:
            from PIL import Image

            image = Image.open(photo).convert("RGB")
            with st.spinner("Analyse de votre photo..."):
                st.session_state.photo_result = {
                    "image": image,
                    "result": classify_uploaded_image(image),
                }
            st.session_state.search_results = []
            st.session_state.selected_product = None
            _rerun()


def render_product_card(product, key_prefix, idx):
    img_src = product.get("image_url") or PLACEHOLDER_IMG
    safe_name = html.escape(product.get("name", "") or "Produit sans nom")
    safe_price = html.escape(product.get("price") or "") or "Prix non communiqué"
    st.markdown(
        f"""
        <div class="product-card">
            <img src="{img_src}" onerror="this.onerror=null;this.src='{PLACEHOLDER_IMG}';" />
            <div class="product-name">{safe_name}</div>
            <div class="product-price">{safe_price}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Choisir ce produit", key=f"{key_prefix}_{idx}"):
        st.session_state.selected_product = product
        st.session_state.prediction = None


# --- Section recherche : toujours 5 résultats maximum ----------------------

if st.session_state.search_results:
    n = len(st.session_state.search_results)
    label = "résultat trouvé" if n == 1 else "résultats trouvés"
    st.markdown(
        f'<div class="section-title">Résultats de recherche '
        f'<span style="font-size:0.9rem; color:var(--text-secondary); font-weight:400;">({n} {label})</span></div>',
        unsafe_allow_html=True,
    )
    # On crée TOUJOURS 5 colonnes, même s'il y a moins de produits : avec
    # st.columns(n), deux résultats donnaient deux cartes larges de la moitié
    # de l'écran, avec des photos étirées. Les colonnes en trop restent vides
    # et la carte garde la même largeur quel que soit le nombre de résultats.
    cols = st.columns(MAX_SEARCH_RESULTS)
    for i, product in enumerate(st.session_state.search_results):
        with cols[i]:
            render_product_card(product, "search", i)

    if st.button("✕ Effacer la recherche"):
        st.session_state.search_results = []
        st.session_state.selected_product = None
        st.session_state.prediction = None
        _rerun()

# --- Résultat d'une photo envoyée par l'utilisateur -------------------------

if st.session_state.photo_result is not None:
    st.markdown(
        '<div class="section-title">Votre photo</div>', unsafe_allow_html=True
    )
    col_img, col_verdict = st.columns([1, 2])
    with col_img:
        st.image(st.session_state.photo_result["image"], use_container_width=True)
    with col_verdict:
        _res = st.session_state.photo_result["result"]
        _cat = _res["category"]
        _conf = _res["confidence"]
        _conf_html = ""
        if _conf is not None:
            _pct = round(_conf * 100)
            _conf_html = (
                f'<div class="confidence-track"><div class="confidence-fill" '
                f'style="width:{_pct}%;"></div></div>'
                f'<div class="confidence-caption">Confiance du modèle : {_pct}%</div>'
            )
        st.markdown(
            f"""
            <div class="result-banner" style="background-color:{CATEGORY_COLORS.get(_cat, '#CCCCCC')};">
                <div class="result-icon-circle">{CATEGORY_ICONS.get(_cat, '♻️')}</div>
                <h1>{CATEGORY_TITLES.get(_cat, 'Catégorie inconnue')}</h1>
                <div class="result-description">{CATEGORY_DESCRIPTIONS.get(_cat, '')}</div>
                <span class="result-source">{SOURCE_LABELS.get(_res['source'], '')}</span>
                {_conf_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Le modèle ne connaît pas la classe « électronique » : sans nom de
        # produit, aucun repli par mots-clés n'est possible ici. On prévient
        # plutôt que de laisser croire à une erreur du modèle.
        st.caption(
            "Sur une photo seule, le Bac D3E ne peut pas être détecté : "
            "cette classe est absente du jeu de données d'entraînement. "
            "Pour un appareil électronique, préférez la recherche par nom."
        )

    if st.button("✕ Effacer la photo"):
        st.session_state.photo_result = None
        _rerun()

# --- Sections pédagogiques : uniquement sur l'écran d'accueil ---------------
# Elles servent à expliquer l'outil à qui arrive sur la page. Une fois la
# recherche lancée, l'utilisateur sait déjà où il est : on les retire pour
# que les produits occupent le haut de l'écran sans défilement.

if not has_content:
    st.markdown('<div class="section-title">Les 5 catégories de tri</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for col, (key, color, label) in zip(cols, BIN_COLORS_ORDERED):
        with col:
            st.markdown(
                f"""
                <div class="bin-showcase-card">
                    <div class="bin-showcase-bar" style="background:{color};"></div>
                    <div class="bin-showcase-icon" style="background:{color}26;">{CATEGORY_ICONS[key]}</div>
                    <div class="bin-showcase-title">{label}</div>
                    <div class="bin-showcase-desc">{CATEGORY_DESCRIPTIONS[key]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# --- Classification du produit sélectionné : fenêtre modale ---------------
# S'affiche immédiatement à la sélection (pas en bas de page), fermable via
# le bouton "Fermer". Repli élégant si st.dialog n'existe pas dans la
# version de Streamlit installée (versions plus anciennes).

_dialog_decorator = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)


def _render_result_content(product):
    if st.session_state.prediction is None:
        with st.spinner("Analyse du produit en cours..."):
            st.session_state.prediction = classify_product(product)

    result = st.session_state.prediction
    category = result["category"]
    source = result["source"]
    confidence = result["confidence"]

    color = CATEGORY_COLORS.get(category, "#CCCCCC")
    title = CATEGORY_TITLES.get(category, "Catégorie inconnue")
    icon = CATEGORY_ICONS.get(category, "♻️")
    description = CATEGORY_DESCRIPTIONS.get(category, "")
    source_label = SOURCE_LABELS.get(source, "")

    confidence_html = ""
    if confidence is not None:
        pct = round(confidence * 100)
        confidence_html = f"""
        <div class="confidence-track"><div class="confidence-fill" style="width:{pct}%;"></div></div>
        <div class="confidence-caption">Confiance du modèle : {pct}%</div>
        """

    st.markdown(f"**Produit :** {html.escape(product.get('name', ''))}")
    st.markdown(
        f"""
        <div class="result-banner" style="background-color:{color};">
            <div class="result-icon-circle">{icon}</div>
            <h1>{title}</h1>
            <div class="result-description">{description}</div>
            <span class="result-source">{source_label}</span>
            {confidence_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Fermer", key="close_result_dialog"):
        st.session_state.selected_product = None
        st.session_state.prediction = None
        _rerun()


if _dialog_decorator is not None:
    @_dialog_decorator("Résultat du tri")
    def _show_result_dialog(product):
        _render_result_content(product)
else:
    def _show_result_dialog(product):
        st.divider()
        _render_result_content(product)


if st.session_state.selected_product:
    _show_result_dialog(st.session_state.selected_product)

st.markdown('<div class="eco-footer">DeepCycle — Projet de fin de module</div>', unsafe_allow_html=True)
