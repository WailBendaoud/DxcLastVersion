import streamlit as st
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
techno_collection = db["techno"]
cv_collection = db["CV"]

st.set_page_config(page_title="Technologies", page_icon="🧠")
st.title(" Filtres par technologies")


if "selected_technos" not in st.session_state:
    st.session_state.selected_technos = []

# 🔍 Chargement des technologies depuis "tech"
toutes_technos = sorted({t["tech"] for t in techno_collection.find({}, {"tech": 1})})
tech_choisie = st.selectbox("Ajouter une technologie :", [""] + toutes_technos)

# ➕ Ajouter si non vide et pas déjà sélectionnée
if tech_choisie and tech_choisie not in st.session_state.selected_technos:
    st.session_state.selected_technos.append(tech_choisie)


st.markdown(" Technologies sélectionnées :")
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


if st.button("🔍 Rechercher les CV correspondants"):
    if not st.session_state.selected_technos:
        st.warning("Veuillez sélectionner au moins une technologie.")
    else:
        # Créer la requête MongoDB
        mongo_query = {
            "technologies": {
                "$all": [
                    {"$elemMatch": {"nom": {"$regex": f"^{tech}$", "$options": "i"}}}
                    for tech in st.session_state.selected_technos
                ]
            }
        }

        # Exécuter la requête
        resultats = list(cv_collection.find(mongo_query))

        st.markdown(f"### 📄 {len(resultats)} CV trouvé(s)")

        if not resultats:
            st.error(" Aucun CV correspondant.")
        else:
            for i, cv in enumerate(resultats, 1):
                nom = cv.get("nom_fichier", "non_disponible.pdf")
                titre = cv.get("titre", "Sans titre")
                st.markdown(f"- {i}. `{nom}` — *{titre}*")

        
        st.session_state.selected_technos = []  
