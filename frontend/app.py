"""
EcoSort-Search — Frontend Streamlit.
Design premium inspiré de Jumia (orange #F55203) avec transitions CSS
avancées (morphing, fade-in, hover) pour une interface dynamique.
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
from Backend.pipeline import search_products, classify_product
from Model_Dl.model_utils import CATEGORY_COLORS, CATEGORY_LABELS

st.set_page_config(page_title="EcoSort-Search", page_icon="♻️", layout="wide")

MAX_RESULTS = 5


def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


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

PLACEHOLDER_IMG = (
    "data:image/svg+xml;charset=UTF-8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='200'%3E"
    "%3Crect width='100%25' height='100%25' fill='%23F2F2F2'/%3E"
    "%3Ctext x='50%25' y='50%25' font-family='sans-serif' font-size='14' "
    "fill='%23999999' text-anchor='middle' dy='.3em'%3EImage indisponible%3C/text%3E"
    "%3C/svg%3E"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class^="css"], [class*=" css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #F7F7FB; }

/* ---------- En-tête avec blob animé (effet "morphose") ---------- */

.eco-header {
    position: relative;
    text-align: center;
    padding: 26px 0 6px 0;
    overflow: hidden;
}
.eco-blob {
    position: absolute;
    top: 50%; left: 50%;
    width: 360px; height: 360px;
    background: linear-gradient(135deg, #F55203, #FFB37A);
    filter: blur(75px);
    opacity: 0.30;
    z-index: 0;
    animation: blobMorph 14s ease-in-out infinite;
}
@keyframes blobMorph {
    0%, 100% { border-radius: 42% 58% 65% 35% / 45% 45% 55% 55%; transform: translate(-50%,-50%) rotate(0deg); }
    33%      { border-radius: 58% 42% 35% 65% / 55% 62% 38% 45%; transform: translate(-50%,-50%) rotate(10deg); }
    66%      { border-radius: 50% 50% 60% 40% / 40% 55% 45% 60%; transform: translate(-50%,-50%) rotate(-8deg); }
}
.eco-header-content { position: relative; z-index: 1; animation: fadeInUp 0.6s cubic-bezier(.4,0,.2,1) both; }

.eco-eyebrow {
    font-family: 'Poppins', sans-serif; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase; color: #F55203; margin-bottom: 6px;
}
.eco-dot {
    display: inline-block; width: 14px; height: 14px; border-radius: 50%;
    background: #F55203; margin-right: 8px; vertical-align: middle;
    animation: pulseDot 2.2s ease-in-out infinite;
}
@keyframes pulseDot {
    0%, 100% { box-shadow: 0 0 0 0 rgba(245,82,3,0.45); }
    50%      { box-shadow: 0 0 0 9px rgba(245,82,3,0); }
}
.eco-title { font-family: 'Poppins', sans-serif; font-size: 2.3rem; font-weight: 800; color: #17181C; }
.eco-title-accent { color: #F55203; }
.eco-subtitle { color: #6B6F76; font-size: 0.98rem; margin: 8px 0 20px 0; font-family: 'Inter', sans-serif; }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Bandeau des 5 couleurs officielles ---------- */

.bin-card {
    background: #FFFFFF; border: 1px solid #ECECF2; border-radius: 14px;
    padding: 16px 18px 12px 18px; margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(20,20,30,0.04);
    animation: fadeInUp 0.6s cubic-bezier(.4,0,.2,1) both; animation-delay: 0.08s;
}
.bin-stripe { display: flex; width: 100%; height: 10px; border-radius: 6px; overflow: hidden; margin-bottom: 5px; }
.bin-stripe div { flex: 1; transition: transform 0.25s ease; }
.bin-stripe div:hover { transform: scaleY(1.6); }
.bin-stripe-labels {
    display: flex; width: 100%; font-size: 0.68rem; color: #8A8E95;
    letter-spacing: 0.05em; text-transform: uppercase; font-family: 'Poppins', sans-serif; font-weight: 600;
}
.bin-stripe-labels div { flex: 1; text-align: center; }

/* ---------- Légende des consignes ---------- */

.legend-row {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 12px; border-radius: 10px; margin-bottom: 4px;
    transition: background-color 0.2s ease;
}
.legend-row:nth-child(odd) { background: #FAFAFC; }
.legend-row:hover { background: #FFF1E8; }
.legend-dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid rgba(0,0,0,0.08); flex-shrink: 0; }
.legend-text { color: #232323; font-size: 0.92rem; line-height: 1.45; font-family: 'Inter', sans-serif; }
.legend-text b { color: #101010; font-family: 'Poppins', sans-serif; }

/* ---------- Section résultats ---------- */

.section-eyebrow {
    font-family: 'Poppins', sans-serif; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase; color: #F55203; margin-bottom: 2px;
}
.section-title { font-family: 'Poppins', sans-serif; font-size: 1.28rem; font-weight: 700; color: #17181C; margin-bottom: 16px; }

.product-card {
    background: #FFFFFF; border: 1px solid #ECECF2; border-radius: 14px;
    padding: 14px 14px 10px 14px; text-align: center;
    height: 252px; display: flex; flex-direction: column;
    box-shadow: 0 2px 10px rgba(20,20,30,0.05);
    transition: transform 0.3s cubic-bezier(.4,0,.2,1), box-shadow 0.3s cubic-bezier(.4,0,.2,1);
    animation: fadeInUp 0.5s cubic-bezier(.4,0,.2,1) both;
}
.product-card:hover { transform: translateY(-6px); box-shadow: 0 16px 28px rgba(20,20,30,0.12); }
.product-card img {
    width: 100%; height: 118px; object-fit: contain;
    background: #FFFFFF; margin-bottom: 8px;
}
.product-name {
    font-family: 'Inter', sans-serif; font-size: 0.82rem; font-weight: 500; color: #232323;
    line-height: 1.3; margin-bottom: 6px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; flex-grow: 1;
}
.product-price { font-family: 'Poppins', sans-serif; color: #17181C; font-weight: 700; font-size: 0.95rem; }

/* ---------- Boutons homogénéisés ---------- */

div.stButton { margin-top: 8px; }
div.stButton > button {
    background: linear-gradient(135deg, #F55203, #FF7A33);
    color: white; border: none; border-radius: 12px;
    width: 100%; min-height: 48px;
    font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 0.92rem;
    letter-spacing: 0.01em;
    box-shadow: 0 2px 8px rgba(245,82,3,0.25);
    transition: all 0.25s cubic-bezier(.4,0,.2,1);
}
div.stButton > button:hover {
    transform: translateY(-2px) scale(1.015);
    box-shadow: 0 10px 22px rgba(245,82,3,0.35);
    background: linear-gradient(135deg, #FF6A1A, #F55203);
    color: white;
}
div.stButton > button:active { transform: translateY(0) scale(0.98); }

.stTextInput > div > div > input {
    border-radius: 12px !important; min-height: 30px;
    font-family: 'Inter', sans-serif;
}

/* ---------- Bandeau de résultat ---------- */

.result-banner {
    padding: 48px 20px; border-radius: 18px; text-align: center; color: white;
    margin-top: 8px; animation: scaleIn 0.5s cubic-bezier(.4,0,.2,1) both;
    box-shadow: 0 16px 32px rgba(0,0,0,0.14);
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.93); }
    to   { opacity: 1; transform: scale(1); }
}
.result-banner h1 { font-family: 'Poppins', sans-serif; font-size: 1.75rem; font-weight: 700; margin: 0 0 12px 0; color: white; }
.result-source {
    display: inline-block; background: rgba(255,255,255,0.22);
    padding: 5px 16px; border-radius: 20px; font-size: 0.8rem;
    font-family: 'Inter', sans-serif; letter-spacing: 0.02em;
}
.confidence-track { width: 220px; height: 6px; background: rgba(255,255,255,0.3); border-radius: 4px; margin: 18px auto 0 auto; overflow: hidden; }
.confidence-fill { height: 100%; background: white; border-radius: 4px; animation: growBar 1.1s cubic-bezier(.4,0,.2,1) both; }
@keyframes growBar { from { width: 0%; } }
.confidence-caption { margin-top: 6px; font-size: 0.78rem; font-family: 'Inter', sans-serif; }

.eco-footer { text-align: center; color: #A5A5AF; font-size: 0.75rem; margin-top: 46px; font-family: 'Inter', sans-serif; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

stripe_segments = "".join(f'<div style="background:{c};"></div>' for _, c, _ in BIN_COLORS_ORDERED)
stripe_labels = "".join(f"<div>{label}</div>" for _, _, label in BIN_COLORS_ORDERED)

st.markdown(
    f"""
    <div class="eco-header">
        <div class="eco-blob"></div>
        <div class="eco-header-content">
            <div class="eco-eyebrow">Tri intelligent des déchets</div>
            <div class="eco-title"><span class="eco-dot"></span>EcoSort<span class="eco-title-accent">Search</span></div>
            <div class="eco-subtitle">Entrez un produit, on retrouve ses 5 meilleures fiches sur Jumia et on vous dit dans quelle poubelle il finit.</div>
        </div>
    </div>
    <div class="bin-card">
        <div class="bin-stripe">{stripe_segments}</div>
        <div class="bin-stripe-labels">{stripe_labels}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("ℹ️ Voir le détail des consignes de tri"):
    descriptions = {
        "jaune": "Emballages légers : bouteilles plastique, canettes, boîtes de conserve, briques de lait, flacons, cartons.",
        "vert": "Uniquement le verre d'emballage : bouteilles, pots de confiture, bocaux (vaisselle cassée interdite).",
        "bleu": "Papiers graphiques propres : prospectus, journaux, magazines, cahiers, livres, enveloppes.",
        "electronique": "Tout appareil à pile, batterie ou prise : smartphones, écouteurs, chargeurs, mixeurs, montres.",
        "marron": "Déchets résiduels non recyclables : restes alimentaires, sachets souples, produits d'hygiène.",
    }
    for key, color, label in BIN_COLORS_ORDERED:
        st.markdown(
            f"""<div class="legend-row"><div class="legend-dot" style="background:{color};"></div>
            <div class="legend-text"><b>{label}</b> — {descriptions[key]}</div></div>""",
            unsafe_allow_html=True,
        )

# --- État de session --------------------------------------------------------

if "results" not in st.session_state:
    st.session_state.results = []
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "prediction" not in st.session_state:
    st.session_state.prediction = None

# --- Étape 1 : recherche ----------------------------------------------------

col_input, col_btn = st.columns([4, 1])
with col_input:
    query = st.text_input(
        "Nom du produit",
        placeholder="ex : bouteille de shampooing, smartphone Samsung, pot de confiture...",
    )
with col_btn:
    st.write("")
    search_clicked = st.button("🔍 Rechercher")

if search_clicked:
    if not query.strip():
        st.warning("Merci d'indiquer un nom de produit avant de lancer la recherche.")
    else:
        with st.spinner("Recherche en cours sur Jumia..."):
            st.session_state.results = search_products(query.strip(), max_results=MAX_RESULTS)
        st.session_state.selected_product = None
        st.session_state.prediction = None
        if not st.session_state.results:
            st.info("Aucun résultat trouvé, réessayez avec un autre mot-clé.")

# --- Étape 2 : résultats (5 max, une seule rangée) --------------------------

if st.session_state.results:
    st.markdown(
        f'<div class="section-eyebrow">Résultats</div>'
        f'<div class="section-title">Top {len(st.session_state.results)} produits les plus pertinents</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(st.session_state.results))
    for i, (col, product) in enumerate(zip(cols, st.session_state.results)):
        with col:
            img_src = product.get("image_url") or PLACEHOLDER_IMG
            safe_name = html.escape(product.get("name", "") or "Produit sans nom")
            safe_price = html.escape(product.get("price") or "") or "Prix non communiqué"
            st.markdown(
                f"""
                <div class="product-card" style="animation-delay:{i * 0.08}s;">
                    <img src="{img_src}" onerror="this.onerror=null;this.src='{PLACEHOLDER_IMG}';" />
                    <div class="product-name">{safe_name}</div>
                    <div class="product-price">{safe_price}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Choisir ce produit", key=f"select_{i}"):
                st.session_state.selected_product = product
                st.session_state.prediction = None

# --- Étape 3 : classification -----------------------------------------------

if st.session_state.selected_product:
    product = st.session_state.selected_product
    st.divider()
    st.markdown(
        f'<div class="section-eyebrow">Analyse</div>'
        f'<div class="section-title">{html.escape(product.get("name", ""))}</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.prediction is None:
        with st.spinner("Analyse du produit en cours..."):
            st.session_state.prediction = classify_product(product)

    result = st.session_state.prediction
    category = result["category"]
    source = result["source"]
    confidence = result["confidence"]

    color = CATEGORY_COLORS.get(category, "#CCCCCC")
    label = CATEGORY_LABELS.get(category, "Catégorie inconnue")
    source_label = SOURCE_LABELS.get(source, "")

    confidence_html = ""
    if confidence is not None:
        pct = round(confidence * 100)
        confidence_html = f"""
        <div class="confidence-track"><div class="confidence-fill" style="width:{pct}%;"></div></div>
        <div class="confidence-caption">Confiance du modèle : {pct}%</div>
        """

    st.markdown(
        f"""
        <div class="result-banner" style="background-color:{color};">
            <h1>{label}</h1>
            <span class="result-source">{source_label}</span>
            {confidence_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Nouvelle recherche"):
        st.session_state.results = []
        st.session_state.selected_product = None
        st.session_state.prediction = None
        _rerun()

st.markdown('<div class="eco-footer">EcoSort-Search — Projet de fin de module</div>', unsafe_allow_html=True)
