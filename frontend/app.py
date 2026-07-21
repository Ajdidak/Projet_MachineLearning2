"""
DeepCycle — Frontend Streamlit.
Ne contient QUE l'affichage : toute la logique métier (scraping + IA)
est déléguée à Backend.pipeline, qui fait le lien avec Scraper et Model_Dl.
"""

import sys
import html
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from backend.pipeline import search_products, classify_product
from model_DL.model_utils import CATEGORY_COLORS, CATEGORY_LABELS

st.set_page_config(page_title="DeepCycle", page_icon="♻️", layout="wide")

MAX_SEARCH_RESULTS = 5  # la recherche renvoie toujours 5 résultats, pas plus


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

HOW_IT_WORKS = [
    ("🔍", "1. Recherchez", "Tapez le nom d'un produit vendu sur Jumia."),
    ("🛍️", "2. Choisissez", "Sélectionnez parmi les 5 résultats les plus pertinents."),
    ("♻️", "3. Triez juste", "L'IA analyse le produit et indique la bonne poubelle."),
]

PLACEHOLDER_IMG = (
    "data:image/svg+xml;charset=UTF-8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E"
    "%3Crect width='100%25' height='100%25' fill='%23F2F2F2'/%3E"
    "%3Ctext x='50%25' y='50%25' font-family='sans-serif' font-size='14' "
    "fill='%23999999' text-anchor='middle' dy='.3em'%3EImage indisponible%3C/text%3E"
    "%3C/svg%3E"
)


FONT_SIZES = {
    "logo_size": "2.7rem",               # "DeepCycle" en haut à gauche
    "subtitle_size": "1.05rem",          # phrase juste sous la barre du haut
    "section_title_size": "1.5rem",      # titres de section ("Résultats de recherche"...)
    "legend_label_size": "1.12rem",      # nom court dans la vitrine des catégories
    "legend_text_size": "1.08rem",       # description dans la vitrine des catégories
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

html, body, [class^="css"], [class*=" css"] { font-family: 'Poppins', sans-serif; }

.stApp { background-color: #FFFFFF; }

.block-container { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }

[data-testid="stHorizontalBlock"] { align-items: center; }

div[data-testid="stTextInput"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
    background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important;
    border-radius: 999px !important; box-shadow: 0 1px 4px rgba(20,33,61,0.06);
    color-scheme: light;
}
div[data-testid="stTextInput"] input {
    background-color: #FFFFFF !important; border: none; height: 48px;
    padding-left: 22px; font-size: __BUTTON_TEXT_SIZE__;
    color: #14213D !important; -webkit-text-fill-color: #14213D !important;
    caret-color: #14213D;
}
div[data-testid="stTextInput"] input::placeholder { color: #8B93A3 !important; opacity: 1; }
div[data-testid="stTextInput"] input:focus { box-shadow: none; }

button[kind="primary"] {
    background-color: #F55203 !important; color: white !important;
    border-radius: 999px !important; height: 46px !important;
    font-weight: 700 !important; border: none !important;
    box-shadow: 0 3px 10px rgba(245,82,3,0.4) !important;
    margin-left: -14px;
}
button[kind="primary"]:hover { background-color: #D94600 !important; }

.eco-topbar { display: flex; align-items: center; height: 48px; padding: 0; margin: 0; line-height: 1; }
.eco-logo { display: inline-flex; align-items: center; line-height: 1; }

/* Masquer l'indication native Streamlit "Press Enter to apply" */
div[data-testid="stTextInput"] div[data-testid="InputInstructions"],
div[data-testid="stTextInput"] small {
    display: none !important;
}
.eco-logo { font-size: __LOGO_SIZE__; font-weight: 700; color: #14213D; white-space: nowrap; }
.eco-logo-accent { color: #2563EB; }
.eco-subtitle { color: #4B5563; font-size: __SUBTITLE_SIZE__; margin: 0 0 28px 0; font-style: italic; }

.section-title {
    color: #14213D; font-size: __SECTION_TITLE_SIZE__; font-weight: 700; margin: 34px 0 16px 0;
    border-left: 5px solid #2563EB; padding-left: 12px;
}

.step-card {
    background: #F8FAFC; border: 1px solid #E7ECF3; border-radius: 14px;
    padding: 26px 18px; text-align: center; height: 180px;
    display: flex; flex-direction: column; justify-content: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.step-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(20,33,61,0.08); }
.step-icon { font-size: 2.1rem; margin-bottom: 10px; }
.step-title { font-weight: 700; color: #14213D; font-size: 1.02rem; margin-bottom: 6px; }
.step-desc { color: #5B6478; font-size: 0.86rem; line-height: 1.5; }

.bin-showcase-card {
    background: #FFFFFF; border: 1px solid #E7ECF3; border-radius: 12px;
    padding: 20px 12px; text-align: center; height: 240px;
    display: flex; flex-direction: column; justify-content: flex-start;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.bin-showcase-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(20,33,61,0.08); }
.bin-showcase-bar { height: 4px; border-radius: 4px; margin: -20px -12px 14px -12px; flex-shrink: 0; }
.bin-showcase-icon { font-size: 1.7rem; margin-bottom: 8px; flex-shrink: 0; }
.bin-showcase-title { font-weight: 700; color: #14213D; font-size: __LEGEND_LABEL_SIZE__; margin-bottom: 6px; flex-shrink: 0; }
.bin-showcase-desc {
    color: #5B6478; font-size: __LEGEND_TEXT_SIZE__; line-height: 1.4;
    display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical;
    overflow: hidden;
}

.product-card {
    background: #FFFFFF; border: 1px solid #E7ECF3; border-radius: 10px 10px 0 0;
    padding: 12px 12px 8px 12px; text-align: center;
    height: 250px; display: flex; flex-direction: column;
    box-shadow: 0 1px 3px rgba(20,33,61,0.05);
}
.product-card img {
    width: 100%; height: 120px; object-fit: contain;
    background: #FFFFFF; margin-bottom: 8px;
}
.product-name {
    font-size: __PRODUCT_NAME_SIZE__; font-weight: 500; color: #1F2937;
    line-height: 1.3; margin-bottom: 6px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; flex-grow: 1;
}
.product-price { color: #2563EB; font-weight: 700; font-size: __PRODUCT_PRICE_SIZE__; }

div.stButton > button {
    background-color: #2563EB; color: white; border: none;
    border-radius: 0 0 10px 10px; width: 100%;
    font-family: 'Poppins', sans-serif; font-weight: 600; padding: 9px 0;
    font-size: __BUTTON_TEXT_SIZE__;
    transition: background-color 0.15s ease;
}
div.stButton > button:hover { background-color: #1D4ED8; color: white; }

.result-banner {
    padding: 40px 28px 32px 28px; border-radius: 20px; text-align: center; color: white;
    margin-top: 6px; box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}
.result-icon-circle {
    width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,0.22);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.1rem; margin: 0 auto 16px auto;
}
.result-banner h1 { font-size: __RESULT_TITLE_SIZE__; margin: 0 0 8px 0; color: white; font-weight: 700; }
.result-description {
    font-size: 0.92rem; color: rgba(255,255,255,0.92); max-width: 380px;
    margin: 0 auto 16px auto; line-height: 1.5;
}
.result-source {
    display: inline-block; background: rgba(255,255,255,0.22);
    padding: 5px 16px; border-radius: 20px; font-size: __RESULT_SOURCE_SIZE__;
}
.confidence-track { width: 220px; height: 6px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 16px auto 0 auto; overflow: hidden; }
.confidence-fill { height: 100%; background: white; }
.confidence-caption { margin-top: 6px; font-size: 0.78rem; }

.eco-footer { text-align: center; color: #9CA3AF; font-size: __FOOTER_SIZE__; margin-top: 50px; }
</style>
"""

for _key, _value in FONT_SIZES.items():
    CUSTOM_CSS = CUSTOM_CSS.replace(f"__{_key.upper()}__", _value)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Barre du haut : logo à gauche, recherche au centre --------------------

col_logo, col_search, col_search_btn, col_spacer = st.columns([2, 3, 1, 1])
with col_logo:
    st.markdown(
        '<div class="eco-topbar"><span class="eco-logo">♻️ Deep<span class="eco-logo-accent">Cycle</span></span></div>',
        unsafe_allow_html=True,
    )
with col_search:
    query = st.text_input(
        "Nom du produit", placeholder="Cherchez un produit, une marque ou une catégorie",
        label_visibility="collapsed",
    )
with col_search_btn:
    search_clicked = st.button("Rechercher", type="primary")
with col_spacer:
    st.write("")

st.markdown(
    '<div class="eco-subtitle">Cherchez. Trouvez. Triez juste.</div>',
    unsafe_allow_html=True,
)

# --- État de session ---------------------------------------------------------

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "prediction" not in st.session_state:
    st.session_state.prediction = None

if search_clicked:
    if not query.strip():
        st.warning("Merci d'indiquer un nom de produit avant de lancer la recherche.")
    else:
        with st.spinner("Recherche en cours sur Jumia..."):
            st.session_state.search_results = search_products(query.strip(), max_results=MAX_SEARCH_RESULTS)
        st.session_state.selected_product = None
        st.session_state.prediction = None
        if not st.session_state.search_results:
            st.info("Aucun résultat trouvé, réessayez avec un autre mot-clé.")


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
    st.markdown('<div class="section-title">Résultats de recherche (top 5)</div>', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.search_results))
    for i, (col, product) in enumerate(zip(cols, st.session_state.search_results)):
        with col:
            render_product_card(product, "search", i)

    if st.button("✕ Effacer la recherche"):
        st.session_state.search_results = []
        st.session_state.selected_product = None
        st.session_state.prediction = None
        _rerun()

# --- Comment ça marche : 3 étapes -------------------------------------------

st.markdown('<div class="section-title">Comment ça marche</div>', unsafe_allow_html=True)
cols = st.columns(3)
for col, (icon, title, desc) in zip(cols, HOW_IT_WORKS):
    with col:
        st.markdown(
            f"""
            <div class="step-card">
                <div class="step-icon">{icon}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- Vitrine permanente des 5 catégories officielles de tri -----------------

st.markdown('<div class="section-title">Les 5 catégories de tri</div>', unsafe_allow_html=True)
cols = st.columns(5)
for col, (key, color, label) in zip(cols, BIN_COLORS_ORDERED):
    with col:
        st.markdown(
            f"""
            <div class="bin-showcase-card">
                <div class="bin-showcase-bar" style="background:{color};"></div>
                <div class="bin-showcase-icon">{CATEGORY_ICONS[key]}</div>
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
