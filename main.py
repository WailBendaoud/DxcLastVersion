
import time
import streamlit as st
from an import analyser_cv


st.set_page_config(page_title="Accueil", page_icon="🏠")





mail=st.Page(
    page="views/RecuperationDuMail .py",
    title="Récuperation des cv"
)
upload=st.Page(
    page="views/UploadCv.py",
    title="Télecherger vos cv"
)
chatbot=st.Page(
    page="views/ChatbotRh.py",
    title="ChatBot",default=True
)
techno=st.Page(
    page="views/RechercheParTechno.py",
    title="Recherche par technologie"
)
technos=st.Page(
    page="views/Technos.py",
    title="Test par technologie"
)
pg=st.navigation(pages=[mail,upload,chatbot,techno,technos])
pg.run()
while True:
        print("\n Lancement de l'analyse automatique des CV...")
        analyser_cv()
        print("Attente de 10 minutes avant le prochain scan...")
        time.sleep(600)  
        

