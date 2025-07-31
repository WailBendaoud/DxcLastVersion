import streamlit as st
import os
import shutil
from pymongo import MongoClient
from streamlit_pdf_viewer import pdf_viewer

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
techno_collection = db["techno"]
cv_collection = db["CV"]

# Configuration Streamlit
st.set_page_config(page_title="Technologies", page_icon="🧠")
st.title("Filtres par technologies")

# Dossiers
CV_DIR = "pieces_jointes"
STATIC_DIR = "static/pdfs"
os.makedirs(STATIC_DIR, exist_ok=True)

# État pour les technos sélectionnées
if "selected_technos" not in st.session_state:
    st.session_state.selected_technos = []

# 🔍 Chargement de toutes les technologies uniques
toutes_technos = sorted({t["tech"] for t in techno_collection.find({}, {"tech": 1})})
tech_choisie = st.selectbox("Ajouter une technologie :", [""] + toutes_technos)

# Ajout à la liste
if tech_choisie and tech_choisie not in st.session_state.selected_technos:
    st.session_state.selected_technos.append(tech_choisie)

# Affichage des technologies sélectionnées
st.markdown("Technologies sélectionnées :")
if st.session_state.selected_technos:
    for tech in st.session_state.selected_technos:
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown(f"- `{tech}`")
        with col2:
            if st.button("❌", key=f"remove_{tech}"):
                st.session_state.selected_technos.remove(tech)
                st.rerun()
else:
    st.info("Aucune technologie sélectionnée.")

# 🔢 Filtre par années d'expérience
annee_exp_min = st.slider("Années d'expérience minimales :", 0, 20, 0)

# 📌 Filtre par titre
titres_bruts = [
    cv.get("titre", "").strip()
    for cv in cv_collection.find({}, {"titre": 1})
    if cv.get("titre")
]
titre_map = {}
for titre in titres_bruts:
    key = titre.lower()
    if key not in titre_map:
        titre_map[key] = titre
titres_uniques = sorted(titre_map.values())
titre_choisi = st.selectbox("Filtrer par titre :", [""] + titres_uniques)

# 🔍 Recherche
if st.button(" Rechercher les CV correspondants"):
    mongo_query = {
        "annees_experience": {"$gte": annee_exp_min}
    }

    if st.session_state.selected_technos:
        mongo_query["technologies"] = {
            "$all": [
                {"$elemMatch": {"nom": {"$regex": f"^{tech}$", "$options": "i"}}}
                for tech in st.session_state.selected_technos
            ]
        }

    if titre_choisi:
        mongo_query["titre"] = {"$regex": f"^{titre_choisi}$", "$options": "i"}

    resultats = list(cv_collection.find(mongo_query))

    st.markdown(f"###  {len(resultats)} CV trouvé(s)")
    if not resultats:
        st.error("Aucun CV correspondant.")
    else:
        for i, cv in enumerate(resultats, 1):
            nom_fichier = cv.get("nom_fichier", "")
            titre = cv.get("titre", "Sans titre")
            nom = cv.get("nom", "Candidat inconnu")
            fichier_path = os.path.join(CV_DIR, nom_fichier)
            static_path = os.path.join(STATIC_DIR, nom_fichier)

            st.markdown(f"---\n### {i}. {nom} — *{titre}*")

            if os.path.exists(fichier_path):
                # Copier vers static/ si pas déjà présent
                if not os.path.exists(static_path):
                    shutil.copyfile(fichier_path, static_path)

                # Visualisation avec streamlit-pdf-viewer
                with st.expander("👁️ Voir le CV en PDF"):
                    pdf_viewer(f"./{static_path}", height=600)

                # Bouton téléchargement
                with open(fichier_path, "rb") as file:
                    file_bytes = file.read()

                st.download_button(
                    label="📥 Télécharger le CV",
                    data=file_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    key=f"download_{nom_fichier}"
                )
            else:
                st.error("Fichier PDF introuvable")

    # Réinitialisation des technos après recherche
    st.session_state.selected_technos = []
