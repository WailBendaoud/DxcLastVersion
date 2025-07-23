import streamlit as st
import imaplib
import email
from email.header import decode_header
import os

# Dossier de sauvegarde des pièces jointes
ATTACHMENTS_DIR = "pieces_jointes"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Fonction principale
def extract_unread_pdf_by_subject(email_address, email_password, target_subject):
    try:
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, email_password)
        mail.select("inbox")

        # Rechercher les e-mails non lus
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        if not email_ids:
            return "Aucun e-mail non lu trouvé."

        count = 0
        for eid in email_ids:
            status, data = mail.fetch(eid, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])

            # Décodage du sujet
            raw_subject = msg["Subject"]
            subject, encoding = decode_header(raw_subject)[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            # Vérifie si le sujet correspond
            if target_subject.lower() in subject.lower():
                found_pdf = False
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and filename.lower().endswith(".pdf"):
                            decoded_name, _ = decode_header(filename)[0]
                            if isinstance(decoded_name, bytes):
                                decoded_name = decoded_name.decode(errors="ignore")

                            filepath = os.path.join(ATTACHMENTS_DIR, decoded_name)
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            found_pdf = True
                            count += 1
                            st.success(f"📄 PDF enregistré : {decoded_name}")
                        else:
                            st.info(f" Pièce jointe ignorée : {filename}")
                if found_pdf:
                    mail.store(eid, '+FLAGS', '\\Seen')
        mail.logout()
        return f"Extraction terminée. {count} fichier(s) PDF téléchargé(s)."
    except imaplib.IMAP4.error as e:
        return f"Erreur IMAP : {str(e)}"
    except Exception as e:
        return f"Erreur : {str(e)}"


st.set_page_config(page_title="Extraction de CV", page_icon="📧")

st.title("📧 Extraction de CV par sujet")
st.markdown("Entrez les informations pour extraire les pièces jointes PDF des e-mails non lus avec un sujet spécifique.")

email_input = st.text_input("Adresse e-mail", value="", placeholder="ex: contactcvstage@gmail.com")
password_input = st.text_input("Mot de passe de l'application Gmail", type="password")
subject_input = st.text_input("Sujet de l’e-mail à filtrer", placeholder="CV STAGE")

if st.button("📥 Extraire les fichiers PDF"):
    if email_input and password_input and subject_input:
        with st.spinner("Connexion et extraction en cours..."):
            result = extract_unread_pdf_by_subject(email_input, password_input, subject_input)
            st.success(result)
    else:
        st.warning("Veuillez remplir tous les champs.")
