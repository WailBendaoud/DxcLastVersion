import os
import re
import json
import unicodedata
import shutil
from langchain_openai import ChatOpenAI
from pymongo import MongoClient
from langchain.prompts import PromptTemplate
import streamlit as st
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer

# === CONFIGURATION ===
load_dotenv()
STATIC_PDF_DIR = "static/pdfs"
SOURCE_PDF_DIR = "pieces_jointes"
os.makedirs(STATIC_PDF_DIR, exist_ok=True)

# === Connexion MongoDB ===
client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
cv_collection = db["CV"]
techno_collection = db["techno"]

# === Charger les technos de référence ===
technos_references = [t["tech"] for t in techno_collection.find({}, {"tech": 1})]
technos_references_str = ", ".join(technos_references)

def normaliser_chaine(texte):
    return unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode("utf-8").lower()

# === LLM OpenAI ===
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# === Prompt ===
prompt = PromptTemplate(
    input_variables=["message", "technos_references"],
    template="""
Tu es un assistant RH spécialisé en requêtes MongoDB.

À partir du message RH ci-dessous, génère une **requête MongoDB** compatible avec la base de données suivante :

Structure de la collection `CV` :
- "titre": string
- "technologies": liste d’objets contenant :
    - "nom": nom de la technologie (ex: Spring Boot)
    - "niveau": niveau de compétence (débutant, intermédiaire, avancé)
- "annees_experience": entier

⚠️ Très important :
- Ne filtre que sur les noms de technologies présents dans ce référentiel :
{technos_references}
- Utilise un ou plusieurs filtres `"$elemMatch"` pour rechercher dans `"technologies"` :
  Exemple :
  {{
    "technologies": {{
      "$elemMatch": {{
        "nom": {{ "$regex": "Spring Boot", "$options": "i" }}
      }}
    }}
  }}
- Si le RH demande un **niveau** spécifique (ex: "avancé"), ajoute-le dans le `$elemMatch`
- Si plusieurs technologies sont mentionnées, combine-les avec `"$and"`
- Ignore toute techno non référencée

Message RH :
{message}

⛔ Retourne uniquement l’objet JSON de la requête MongoDB (aucun texte ou commentaire autour).
"""
)

chain = prompt | llm

# === Interface Streamlit ===
st.set_page_config(page_title="Assistant RH", page_icon="🤖")
st.title("🤖 Assistant RH")

# Historique session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Champ d'entrée RH
if prompt_input := st.chat_input("Quel est votre besoin RH ?"):
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        with st.spinner("Génération en cours..."):
            try:
                reponse = chain.invoke({
                    "message": prompt_input,
                    "technos_references": technos_references_str
                })

                # Nettoyage de la réponse
                cleaned = re.sub(r"```json|```", "", reponse.content).strip()
                match = re.search(r"\{[\s\S]*\}", cleaned)

                if not match:
                    st.error(" Aucune requête MongoDB détectée.")
                else:
                    query = json.loads(match.group(0))
                    resultats = list(cv_collection.find(query))

                    # Réponse principale
                    reponse_finale = f" **Requête MongoDB générée :**\n```js\n{json.dumps(query, indent=2)}\n```"
                    if not resultats:
                        reponse_finale += "\n Aucun CV trouvé."
                    else:
                        reponse_finale += f"\n {len(resultats)} CV trouvé(s) :"
                        for i, cv in enumerate(resultats, 1):
                            nom = cv.get("nom_fichier", f"cv_{i}.pdf")
                            titre = cv.get("titre", "Sans titre")

                            # Vérification et copie dans le dossier static
                            source_path = os.path.join(SOURCE_PDF_DIR, nom)
                            static_path = os.path.join(STATIC_PDF_DIR, nom)
                            public_path = f"../{STATIC_PDF_DIR}/{nom}"

                            if os.path.exists(source_path):
                                if not os.path.exists(static_path):
                                    shutil.copyfile(source_path, static_path)
                                reponse_finale += f"\n- `{titre}`"
                            else:
                                reponse_finale += f"\n- `{titre}` (❌ Fichier introuvable)"

                    # Affichage du résumé texte
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reponse_finale
                    })
                    st.markdown(reponse_finale)

                    # Affichage PDF
                    for cv in resultats:
                        nom = cv.get("nom_fichier")
                        titre = cv.get("titre", "Sans titre")
                        chemin_pdf = os.path.join(STATIC_PDF_DIR, nom)

                        if os.path.exists(chemin_pdf):
                            st.markdown(f"###  Aperçu du CV : {titre}")
                            pdf_viewer(f"../{STATIC_PDF_DIR}/{nom}", height=600)

            except Exception as e:
                st.error(f" Erreur : {str(e)}")
