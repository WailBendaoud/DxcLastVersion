
import streamlit as st

st.set_page_config(page_title="Accueil", page_icon="🏠")



analyse=st.Page(
    page="views/Analyse.py",
    title="Analyse",
    default=True
    
    )

mail=st.Page(
    page="views/RecuperationDuMail .py",
    title="Récuperation des cv"
)
upload=st.Page(
    page="views/UploadCv.py",
    title="Télecherger vos cv"
)

pg=st.navigation(pages=[analyse,mail,upload])
pg.run()
