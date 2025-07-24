from pymongo import MongoClient
import re

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
collection = db["techno"]

# === Définition des librairies connues à exclure ===
language_libraries = {
    "python": [
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "tensorflow", "keras", "pytorch", "scikit-learn",
        "scikit learn", "scikit", "nltk", "spacy", "shap", "xgboost", "statsmodels", "dash", "plotly",
        "django", "spyder", "pycharm", "jupyter", "jupyter notebook", "google colab", "scikit-pandas", "cnn",
        "rnn", "lstm", "gru", "transformer", "eda", "etl", "regex"
    ],
    "r": ["r studio"],
    "java": [],
    "c": ["keil", "pspice", "simulink", "matlab"]
}

# Création d’un set de mots-clés à exclure (normalisés)
def normalize(text):
    text = text.lower()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ùûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = text.replace("programming language", "")
    text = text.replace("software", "")
    text = text.replace("tools", "")
    text = text.replace("tool", "")
    text = text.replace("language", "")
    return text.strip()

# Normaliser toutes les librairies à supprimer
to_exclude = {normalize(lib) for libs in language_libraries.values() for lib in libs}

# Supprimer dans MongoDB
deleted_count = 0
for item in collection.find():
    tech_name = item.get("tech", "")
    norm = normalize(tech_name)
    if norm in to_exclude:
        collection.delete_one({"_id": item["_id"]})
        print(f"❌ Supprimé : {tech_name}")
        deleted_count += 1

print(f"\n✅ Nettoyage terminé. {deleted_count} élément(s) supprimé(s).")
