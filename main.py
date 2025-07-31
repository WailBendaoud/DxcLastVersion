
import time
import streamlit as st
from Analyse import analyser_cv


st.set_page_config(page_title="Accueil", page_icon="🏠")





mail=st.Page(
    page="views/RecuperationDuMail .py",
    title="Récuperation des cv via mail "
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
    title="Statistique"
)
cv=st.Page(
    page="views/Galery.py",
    title="CV"
)
pg=st.navigation(pages=[mail,upload,chatbot,techno,technos,cv])
pg.run()

        

