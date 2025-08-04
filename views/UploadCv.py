import streamlit as st
import os
import uuid

# Dossier commun
ATTACHMENTS_DIR = "pieces_jointes"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


st.set_page_config(page_title="Uploader CV", page_icon="📤")
st.title("Ajouter des CV manuellement")
st.markdown("Sélectionnez vos fichiers PDF, puis cliquez sur **Confirmer l’ajout** pour les enregistrer.")


uploaded_files = st.file_uploader(
    "Sélectionner un ou plusieurs fichiers PDF",
    type=["pdf"],
    accept_multiple_files=True
)


if uploaded_files:
    st.info(f"{len(uploaded_files)} fichier(s) sélectionné(s).")
    if st.button("📥 Confirmer l'ajout"):
        for uploaded_file in uploaded_files:
            base, ext = os.path.splitext(uploaded_file.name)
            unique_id = uuid.uuid4().hex  # identifiant unique
            unique_name = f"{base}_{unique_id}{ext}"
            save_path = os.path.join(ATTACHMENTS_DIR, unique_name)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f" Fichier enregistré : {unique_name}")
else:
    st.warning("Aucun fichier sélectionné.")
