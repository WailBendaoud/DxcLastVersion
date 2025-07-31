import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
cv_collection = db["CV"]

st.set_page_config(page_title="Technologies & CV", page_icon="📊")
st.title(" Statistiques des technologies utilisées dans les CV")

# 🧮 Pipeline d'agrégation
pipeline = [
    {"$unwind": "$technologies"},
    {"$group": {
        "_id": "$technologies.nom",
        "nombre_cv": {"$sum": 1},
        "cv_ids": {"$addToSet": "$_id"}
    }},
    {"$sort": {"nombre_cv": -1}}
]

resultats = list(cv_collection.aggregate(pipeline))


data = []
for res in resultats:
    data.append({
        "Technologie": res["_id"],
        "Nombre de CV": res["nombre_cv"],
        "IDs": res["cv_ids"]
    })

df = pd.DataFrame(data)

# 📈 Graphique
if not df.empty:
    fig = px.bar(df, x="Technologie", y="Nombre de CV", title="Nombre de CV par technologie", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # 📋 Tableau
    st.subheader("📄 Tableau des technologies")

    st.dataframe(df[["Technologie", "Nombre de CV"]], use_container_width=True)

   
else:
    st.warning("Aucune technologie trouvée.")
