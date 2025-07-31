import os
import re
import json
import requests
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from tqdm import tqdm


load_dotenv()
OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "mxbai-embed-large"
SIMILARITY_THRESHOLD = 0.80


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

relation_prompt = PromptTemplate(
    input_variables=["t1", "t2"],
    template="""
Tu es un expert technique. Réponds uniquement par "SOUS-PARTIE" ou "DISTINCT".

Analyse la relation entre ces deux technologies :
- "{t1}"
- "{t2}"

Si "{t1}" est une fonctionnalité, un outil intégré, une extension, ou une composante de "{t2}", réponds "SOUS-PARTIE".

Sinon, s’il s’agit de deux technologies ou outils différents à part entière, réponds "DISTINCT".

Ta réponse : 
"""
)
relation_chain = relation_prompt | llm


client = MongoClient("mongodb://localhost:27017/")
db = client["local"]
collection = db["techno"]


technos = list({doc["tech"].strip() for doc in collection.find() if "tech" in doc and doc["tech"].strip()})
print(f" {len(technos)} technologies chargées depuis MongoDB.")

def get_ollama_embedding(text):
    response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": text})
    response.raise_for_status()
    return response.json()["embedding"]

print(" Génération des embeddings via Ollama...")
embeddings = {}
for tech in tqdm(technos):
    try:
        embeddings[tech] = get_ollama_embedding(tech)
    except Exception as e:
        print(f" Erreur embedding pour {tech} : {e}")


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def verifier_relation(t1, t2):
    try:
        response = relation_chain.invoke({"t1": t1, "t2": t2})
        return response.content.strip().upper()
    except Exception as e:
        print(f" Erreur LLM pour {t1}/{t2} : {e}")
        return "DISTINCT"


print(" Analyse des paires similaires...")
to_delete = set()

for i in range(len(technos)):
    for j in range(i + 1, len(technos)):
        t1, t2 = technos[i], technos[j]
        if t1.lower() in to_delete or t2.lower() in to_delete:
            continue
        try:
            sim = cosine_similarity(embeddings[t1], embeddings[t2])
            if sim >= SIMILARITY_THRESHOLD:
                relation = verifier_relation(t1, t2)
                if relation == "SOUS-PARTIE":
                    sous_partie = t1  # d'après ton prompt, t1 est la sous-partie
                    to_delete.add(sous_partie.lower())
                    print(f" LLM: '{t1}' est une SOUS-PARTIE de '{t2}' (sim={sim:.2f})")
                    print(f" À supprimer : {sous_partie}")

        except Exception as e:
            print(f" Erreur comparaison {t1}/{t2} : {e}")


print("\n Suppression dans la base MongoDB...")
deleted = 0
for item in collection.find():
    tech = item.get("tech", "").strip().lower()
    if tech in to_delete:
        collection.delete_one({"_id": item["_id"]})
        print(f" Supprimé : {tech}")
        deleted += 1

print(f"\n Nettoyage terminé. {deleted} technologie(s) supprimée(s).")
