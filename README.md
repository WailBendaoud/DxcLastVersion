# Plateforme d'analyse et de gestion de CV

Ce projet est une application complète de gestion, d'analyse et de recherche de CV, conçue pour les besoins RH, utilisant Python, Streamlit, MongoDB et l'IA (OpenAI, Ollama).

## Fonctionnalités principales

- **Upload de CV** : Ajout manuel ou automatique (par e-mail) de CV au format PDF.
- **Extraction et normalisation des compétences** : Analyse automatique des CV pour extraire les compétences techniques, normalisées selon un référentiel stocké en base MongoDB.
- **Recherche avancée** : Filtrage des CV par technologies, années d'expérience, titre, etc.
- **Assistant RH** : Génération de requêtes MongoDB à partir de requêtes en langage naturel grâce à l'IA.
- **Statistiques** : Visualisation des technologies les plus présentes dans les CV.
- **Nettoyage automatique** : Suppression des doublons ou sous-parties de technologies dans le référentiel via embeddings et LLM.
- **Galerie de CV** : Visualisation, export (Excel/PDF) et téléchargement des CV filtrés.

## Structure du projet

- `main.py` : Point d'entrée Streamlit, navigation entre les différentes pages.
- `Analyse.py` : Extraction, normalisation et analyse des compétences des CV.
- `nettoyage.py` : Nettoyage du référentiel de technologies (suppression des sous-parties, doublons).
- `analyse_auto.py` : Lancement automatique et périodique de l'analyse des nouveaux CV.
- `views/` : Contient toutes les pages Streamlit (upload, recherche, statistiques, assistant RH, galerie, extraction par mail).
- `pieces_jointes/` : Dossier de stockage des CV originaux.
- `static/pdfs/` : Dossier pour la visualisation des PDF dans l'interface.
- `pyproject.toml`, `uv.lock` : Dépendances Python.

## Installation


1. **Cloner le dépôt**
2. **Installer les dépendances avec [uv](https://github.com/astral-sh/uv)** :
   
   uv pip install --system .
   ```
   > Vous pouvez aussi utiliser `uv venv` pour créer un environnement virtuel, ou installer via `pyproject.toml` :
   
  
   uv pip install --system .
   ```
3. **Configurer l'environnement** :
   - Créer un fichier `.env` avec vos clés API (OpenAI, Ollama, etc.)
   - S'assurer que MongoDB est lancé localement (`mongodb://localhost:27017/`)
4. **Lancer l'application** :
   ```bash
   streamlit run main.py
   ```

## Technologies utilisées

- Python 3.13+
- Streamlit
- MongoDB
- LangChain, OpenAI, Ollama (embeddings, LLM)
- Diverses librairies : pandas, plotly, tqdm, PyMuPDF, etc.

## Organisation des pages principales

- **Accueil** : Navigation entre les modules.
- **Upload CV** : Ajout manuel de CV PDF.
- **Extraction par mail** : Récupération automatique des CV reçus par e-mail.
- **Recherche par technologie** : Filtrage multi-critères des CV.
- **Assistant RH** : Génération de requêtes MongoDB à partir de besoins RH en langage naturel.
- **Statistiques** : Graphiques sur la répartition des technologies.
- **Galerie** : Tableau filtrable/exportable de tous les CV.

## Notes

- L'application nécessite des clés API valides pour OpenAI et/ou Ollama.
- Le nettoyage du référentiel techno utilise des embeddings et un LLM pour détecter les sous-parties.
- Les CV sont stockés en base MongoDB avec leurs compétences extraites et normalisées.

## Auteur

Wail Bendaoud
