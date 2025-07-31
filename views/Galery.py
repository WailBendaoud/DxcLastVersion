import shutil
import streamlit as st
import os
import pandas as pd
import io
from pymongo import MongoClient
from streamlit_pdf_viewer import pdf_viewer
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
cv_collection = db["CV"]

# Dossiers
ATTACHMENTS_DIR = "pieces_jointes"
STATIC_PDF_DIR = "static/pdfs"
os.makedirs(STATIC_PDF_DIR, exist_ok=True)

# Initialisation état du popup
if "popup_filename" not in st.session_state:
    st.session_state.popup_filename = None

# Configuration Streamlit
st.set_page_config(page_title=" CV", page_icon="📂", layout="wide")
st.title(" Tous les CV enregistrés")

# Récupération uniquement des CV qui ont au moins une technologie
cvs = [
    cv for cv in cv_collection.find()
    if "technologies" in cv and isinstance(cv["technologies"], list) and len(cv["technologies"]) > 0
]

# Récupération des technologies uniques
all_technos = sorted(
    list({tech["nom"] for cv in cvs for tech in cv["technologies"]})
)

# Sélecteur multichoix pour filtrer par technologie
selected_technos = st.multiselect(" Filtrer par technologies :", all_technos)

# Appliquer le filtre si une ou plusieurs technos sont sélectionnées
if selected_technos:
    cvs = [
        cv for cv in cvs
        if any(tech["nom"] in selected_technos for tech in cv["technologies"])
    ]

if not cvs:
    st.warning("Aucun CV trouvé pour les critères sélectionnés.")
else:
    # Construction du DataFrame pour affichage et export
    data = []
    for cv in cvs:
        data.append({
            "Nom": cv.get("nom", "Inconnu"),
            "Nom du fichier": cv.get("nom_fichier", "non_disponible.pdf"),
            "Technologies": ", ".join(tech["nom"] for tech in cv.get("technologies", []))
        })
    df = pd.DataFrame(data)

    st.markdown("###  Tableau de CV")

    # Configuration AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=5)
    gb.configure_default_column(wrapText=True, autoHeight=True)
    gb.configure_column("Technologies", wrapText=True, autoHeight=True)
    grid_options = gb.build()

    AgGrid(
        df,
        gridOptions=grid_options,
        height=300,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True
    )

    # Export Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="CVs")
    st.download_button(
        label=" Télécharger en Excel",
        data=excel_buffer.getvalue(),
        file_name="cv_tableau.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Export PDF
    def generate_pdf(dataframe):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        elements.append(Paragraph("Tableau des CV filtrés", styles["Title"]))
        elements.append(Spacer(1, 12))

        # Transformation des cellules en Paragraphs (mais technologies restent sur une ligne)
        wrapped_data = []
        for index, row in dataframe.iterrows():
            row_data = []
            for col in dataframe.columns:
                cell = str(row[col])
                if col == "Technologies":
                    # Garde les technologies séparées par virgules, sans <br/>
                    cell = Paragraph(cell, styles["Normal"])
                else:
                    cell = Paragraph(cell, styles["Normal"])
                row_data.append(cell)
            wrapped_data.append(row_data)

        table_data = [list(dataframe.columns)] + wrapped_data

        table = Table(table_data, repeatRows=1, colWidths=[120, 120, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer



    pdf_buffer = generate_pdf(df)
    st.download_button(
        label=" Télécharger en PDF",
        data=pdf_buffer,
        file_name="cv_tableau.pdf",
        mime="application/pdf"
    )

    
# === POPUP CENTRAL (affiche le CV en grand centré) ===
if st.session_state.popup_filename:
    st.markdown("###  Aperçu du CV sélectionné", unsafe_allow_html=True)

    filepath = os.path.join(ATTACHMENTS_DIR, st.session_state.popup_filename)
    static_path = os.path.join(STATIC_PDF_DIR, st.session_state.popup_filename)

    if not os.path.exists(static_path):
        shutil.copyfile(filepath, static_path)

    viewer_path = f"./{STATIC_PDF_DIR}/{st.session_state.popup_filename}"

    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    pdf_viewer(
        viewer_path,
        width=900,
        height=1000,
        zoom_level=1.2,
        viewer_align="center",
        show_page_separator=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.button(" Fermer", on_click=lambda: st.session_state.update({"popup_filename": None}))
