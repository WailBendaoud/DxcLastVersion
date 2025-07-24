import streamlit as st
import os

# Dossier commun
ATTACHMENTS_DIR = "pieces_jointes"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Configuration de la page
st.set_page_config(page_title="Uploader CV", page_icon="📤")
st.title("Ajouter des CV manuellement")
st.markdown("Sélectionnez vos fichiers PDF, puis cliquez sur **Confirmer l’ajout** pour les enregistrer.")

# Étape 1 : Upload de fichiers PDF
uploaded_files = st.file_uploader(
    "Sélectionner un ou plusieurs fichiers PDF",
    type=["pdf"],
    accept_multiple_files=True
)

# Étape 2 : Bouton de confirmation
if uploaded_files:
    st.info(f"{len(uploaded_files)} fichier(s) sélectionné(s).")
    if st.button("📥 Confirmer l'ajout"):
        for uploaded_file in uploaded_files:
            save_path = os.path.join(ATTACHMENTS_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f" Fichier enregistré : {uploaded_file.name}")
else:
    st.warning("Aucun fichier sélectionné.")
