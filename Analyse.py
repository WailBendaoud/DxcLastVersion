import os
import json
import re
import time
import json5
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_ollama import OllamaLLM
from pymongo import MongoClient

PDF_FOLDER = "pieces_jointes"

def recuperer_technologies_reference():
    """Récupère toutes les technologies de référence depuis la collection techno"""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["local"]
    techno_collection = db["techno"]
    
    technologies = []
    for doc in techno_collection.find():
        tech_name = doc.get("tech", "").strip()
        if tech_name:
            technologies.append(tech_name)
    
    client.close()
    return list(set(technologies))  # Supprimer les doublons

def extraire_skills_cv(cv_texte, llm):
    """Première étape : extraire uniquement les skills du CV"""
    prompt_skills = PromptTemplate(
        input_variables=["cv"],
        template="""
Analyse ce CV et extrais TOUTES les compétences techniques mentionnées.

TYPES DE COMPETENCES A EXTRAIRE:
- Langages de programmation (Java, Python, JavaScript, etc.)
- Frameworks (Spring, React, Angular, Laravel, etc.)
- Bases de données (MySQL, MongoDB, Oracle, etc.)
- Outils (Git, Maven, Docker, etc.)
- Technologies web (HTML, CSS, REST, etc.)
- Méthodologies (Scrum, Agile, etc.)

IMPORTANT: Extrais TOUTES les variantes mentionnées.

Retourne UNIQUEMENT ce JSON:
{{
  "skills_detectes": ["skill1", "skill2", "skill3"]
}}

CV:
{cv}
"""
    )
    
    chain = prompt_skills | llm
    reponse = chain.invoke({"cv": cv_texte})
    
    try:
        reponse_nettoyee = reponse.strip()
        match = re.search(r"\{[\s\S]*\}", reponse_nettoyee)
        if not match:
            print(f"❌ Aucun JSON trouvé dans l'extraction skills")
            return []
            
        bloc_json = match.group(0)
        
        try:
            donnees = json.loads(bloc_json)
        except json.JSONDecodeError:
            # Correction automatique
            bloc_json_corrige = bloc_json.replace("'", '"')
            bloc_json_corrige = re.sub(r'(\w+):', r'"\1":', bloc_json_corrige)
            bloc_json_corrige = re.sub(r',\s*}', '}', bloc_json_corrige)
            bloc_json_corrige = re.sub(r',\s*]', ']', bloc_json_corrige)
            
            try:
                donnees = json.loads(bloc_json_corrige)
            except:
                print(f"❌ JSON non parsable: {bloc_json}")
                return []
        
        skills = donnees.get("skills_detectes", [])
        print(f" {len(skills)} compétences extraites")
        return skills
        
    except Exception as e:
        print(f"❌ Erreur extraction skills : {e}")
        return []
def normaliser_skills(skills_cv, technologies_reference, llm):
    """Normalise les skills du CV selon le référentiel techno"""
    if not skills_cv:
        print("❌ Aucun skill à normaliser")
        return []
    
    print(f" Normalisation de {len(skills_cv)} compétences...")

    skills_str = ", ".join(skills_cv)
    techno_str = ", ".join(technologies_reference)
    
    prompt_normalisation = PromptTemplate(
    input_variables=["skills_cv", "technologies_reference"],
    template="""
OBJECTIF CRITIQUE : Mapper les compétences du CV vers le RÉFÉRENTIEL EXISTANT ci-dessous.

CV - COMPÉTENCES DÉTECTÉES :
{skills_cv}

RÉFÉRENTIEL OFFICIEL (UTILISER EXCLUSIVEMENT CES VALEURS, SANS AUCUNE MODIFICATION) :
{technologies_reference}

RÈGLES STRICTES :
1. Tu dois faire correspondre chaque compétence du CV à UNE ET UNE SEULE valeur EXACTE du référentiel.
2. Si plusieurs correspondances sont possibles, choisis celle qui est exactement écrite dans le référentiel.
3. NE PAS :
   - reformuler les acronymes (ex : JMS ≠ Java Message Service)
   - corriger l'orthographe
   - enrichir ou transformer les noms
4. Si une compétence n'existe PAS dans le référentiel, alors :
   - "correspondance_trouvee": false
   - "skill_normalise": doit rester égal au mot du CV
5. Assigne un niveau arbitraire (débutant, intermédiaire, avancé) selon ton jugement.

FORMAT DE RÉPONSE (uniquement ce JSON, sans texte autour) :
{{  
  "technologies_normalisees": [  
    {{  
      "skill_cv_original": "Spring",  
      "skill_normalise": "Spring Boot",  
      "niveau": "intermédiaire",  
      "correspondance_trouvee": true  
    }},  
    {{  
      "skill_cv_original": "TechInconnue",  
      "skill_normalise": "TechInconnue",  
      "niveau": "débutant",  
      "correspondance_trouvee": false  
    }}  
  ]  
}}
"""
)



    chain = prompt_normalisation | llm
    reponse = chain.invoke({
        "skills_cv": skills_str,
        "technologies_reference": techno_str
    })

    try:
        reponse_nettoyee = reponse.strip()
        match = re.search(r"\{[\s\S]*\}", reponse_nettoyee)

        if not match:
            print(" Aucun JSON trouvé dans la normalisation.")
            print(" Réponse brute du LLM :\n", reponse_nettoyee)
            return []

        bloc_json = match.group(0)
        print(" JSON brut détecté (tentative de parsing)...")

        try:
            donnees = json5.loads(bloc_json)
        except Exception as je:
            print(f" Erreur JSON5 : {je}")
            print(" JSON renvoyé par le LLM :\n", bloc_json)
            return []

        technologies_normalisees = donnees.get("technologies_normalisees", [])
        print(f" {len(technologies_normalisees)} compétences normalisées")
        return technologies_normalisees

    except Exception as e:
        print(f"❌ Erreur inattendue lors de la normalisation : {e}")
        return []
def analyser_informations_cv(cv_texte, llm):
    """Extrait les informations personnelles et professionnelles du CV"""
    prompt_infos = PromptTemplate(
        input_variables=["cv"],
        template="""
Extrais ces informations du CV:

1. Nom complet de la personne
2. Titre/profil professionnel (ex: Développeur Full Stack, Data Scientist)
3. Expériences professionnelles (poste, entreprise, dates, missions principales)
4. Années totales d'expérience professionnelle (travail réel uniquement, pas stages/études)

JSON ATTENDU:
{{
  "nom": "nom_complet",
  "titre": "titre_professionnel",
  "experiences": [
    {{
      "poste": "nom_poste",
      "entreprise": "nom_entreprise",
      "dates": "periode",
      "missions": "description_courte"
    }}
  ],
  "annees_experience": 5
}}

CV:
{cv}
"""
    )
    
    chain = prompt_infos | llm
    reponse = chain.invoke({"cv": cv_texte})
    
    try:
        reponse_nettoyee = reponse.strip()
        match = re.search(r"\{[\s\S]*\}", reponse_nettoyee)
        if not match:
            print(f" Aucun JSON trouvé dans l'analyse des infos")
            return None
            
        bloc_json = match.group(0)
        
        try:
            return json.loads(bloc_json)
        except json.JSONDecodeError:
            # Correction automatique
            bloc_json_corrige = bloc_json.replace("'", '"')
            bloc_json_corrige = re.sub(r'(\w+):', r'"\1":', bloc_json_corrige)
            bloc_json_corrige = re.sub(r',\s*}', '}', bloc_json_corrige)
            bloc_json_corrige = re.sub(r',\s*]', ']', bloc_json_corrige)
            
            try:
                return json.loads(bloc_json_corrige)
            except:
                print(f" JSON des infos non corrigeable")
                return None
        
    except Exception as e:
        print(f" Erreur analyse infos : {e}")
        return None

def ajouter_nouvelles_technologies(technologies_normalisees):
    """Ajoute dans le référentiel les technologies non reconnues (nouvelles)"""
    client = MongoClient("mongodb://localhost:27017/")
    db = client["local"]
    techno_collection = db["techno"]

    nouvelles_technos = 0
    for tech in technologies_normalisees:
        correspondance = tech.get("correspondance_trouvee", False)
        nom_tech = tech.get("skill_normalise", "").strip()

        if not nom_tech or nom_tech.lower() in ["n/a", "none", ""]:
            continue  # on saute les valeurs vides ou invalides

        # 💡 Même si elle n'était pas dans le référentiel, on la stocke comme nouvelle techno
        # Pour éviter les doublons exacts
        deja_existe = techno_collection.find_one({"tech": nom_tech})
        if not deja_existe:
            techno_collection.insert_one({
                "tech": nom_tech,
            })
            nouvelles_technos += 1
            print(f" Nouvelle technologie ajoutée: {nom_tech}")

    client.close()
    if nouvelles_technos > 0:
        print(f" {nouvelles_technos} nouvelles technologies ajoutées au référentiel")
    else:
        print(" Aucune nouvelle technologie à ajouter (déjà connues)")

    return nouvelles_technos

def generer_resume_cv(cv_texte, llm):
    """Génère un paragraphe de résumé professionnel du CV"""
    prompt_resume = PromptTemplate(
        input_variables=["cv"],
        template="""
Tu es un assistant RH. Rédige un **paragraphe professionnel de 2 à 3 lignes** qui résume **le contenu du CV**.

🔒 INSTRUCTIONS :
- Pas de titre, pas de bullet points
- Ne commence pas par "Voici le résumé", "Ce CV présente", etc.
- Commence directement par une phrase descriptive sur le candidat
- Langue : française, style formel, objectif

CV :
{cv}
"""

    )
    
    chain = prompt_resume | llm
    try:
        reponse = chain.invoke({"cv": cv_texte}).strip()
        return reponse
    except Exception as e:
        print(f" Erreur génération résumé : {e}")
        return "Résumé non disponible"
    
def analyser_cv():
    """Fonction principale d'analyse des CVs"""
    print(" Démarrage de l'analyse des CVs")
    
    # Initialisation
    llm = OllamaLLM(model="llama3.1")
    
    # Récupération du référentiel
    print(" Chargement du référentiel de technologies...")
    technologies_reference = recuperer_technologies_reference()
    print(f" {len(technologies_reference)} technologies de référence chargées")
    
    # Connexion MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["local"]
    collection = db["CV"]

    # Traitement des fichiers
    fichiers_pdf = [f for f in os.listdir(PDF_FOLDER) 
                   if f.lower().endswith(".pdf") and not f.endswith("_done.pdf")]
    
    print(f" {len(fichiers_pdf)} fichiers PDF à traiter")

    for filename in fichiers_pdf:
        filepath = os.path.join(PDF_FOLDER, filename)
        print(f"\n{'='*60}")
        print(f"TRAITEMENT: {filename}")
        print(f"{'='*60}")

        try:
            # Chargement du PDF
            print(" Chargement du PDF...")
            loader = PyMuPDFLoader(filepath)
            documents = loader.load()
            texte_cv = "\n".join([doc.page_content for doc in documents])
            print(f" PDF chargé ({len(texte_cv)} caractères)")

            # Étape 1: Extraction des compétences
            print("\n Extraction des compétences...")
            skills_cv = extraire_skills_cv(texte_cv, llm)
            if not skills_cv:
                print(" Aucune compétence extraite, passage au fichier suivant")
                continue
            
            print(f"📋 Compétences détectées: {', '.join(skills_cv[:10])}{'...' if len(skills_cv) > 10 else ''}")

            # Étape 2: Normalisation (UNE SEULE FOIS)
            print(f"\n Normalisation des compétences...")
            technologies_normalisees = normaliser_skills(skills_cv, technologies_reference, llm)
            if not technologies_normalisees:
                print(" Échec de la normalisation")
                continue

            # Affichage des correspondances avec validation
            print("\n Résultats de la normalisation:")
            correspondances_trouvees = 0
            nouvelles_technologies = 0
            
            for tech in technologies_normalisees:
                correspondance = tech.get("correspondance_trouvee", False)
                original = tech.get("skill_cv_original", "")
                normalise = tech.get("skill_normalise", "")
                niveau = tech.get("niveau", "")
                
                if correspondance:
                    status = " MAPPÉ"
                    correspondances_trouvees += 1
                    # Vérifier que le nom normalisé existe vraiment dans le référentiel
                    if normalise not in technologies_reference:
                        print(f"     ATTENTION: {normalise} n'existe pas dans le référentiel!")
                else:
                    status = " NOUVEAU"
                    nouvelles_technologies += 1
                
                print(f"   {status}: ORIGINAL {original} → NORMALISER {normalise} ({niveau})")
            
            print(f"\nRésumé: {correspondances_trouvees} mappés, {nouvelles_technologies} nouveaux")

            # Étape 3: Analyse des informations personnelles
            print(f"\n Extraction des informations personnelles...")
            infos_cv = analyser_informations_cv(texte_cv, llm)
            resume_cv = generer_resume_cv(texte_cv, llm)
            print(f"\n Résumé généré : {resume_cv}")
            if not infos_cv:
                print("Échec de l'extraction des informations")
                continue

            # Préparation des technologies pour la sauvegarde
            # ✅ Préparation des technologies pour la sauvegarde (filtrage des doublons + niveau max)
            niveau_rang = {"débutant": 1, "intermédiaire": 2, "avancé": 3}
            techno_map = {}

            for tech in technologies_normalisees:
                nom = tech.get("skill_normalise", "").strip()
                niveau = tech.get("niveau", "intermédiaire").strip()

                if not nom:
                    continue

                if nom in techno_map:
                    # Conserver le niveau le plus élevé
                    ancien = techno_map[nom]
                    if niveau_rang[niveau] > niveau_rang[ancien]:
                        techno_map[nom] = niveau
                else:
                    techno_map[nom] = niveau

            # Liste finale sans doublons
            technologies_finales = [{"nom": nom, "niveau": niveau} for nom, niveau in techno_map.items()]


            # Affichage du résumé
            print(f"\n RÉSULTATS FINAUX:")
            print(f" Nom: {infos_cv.get('nom', 'Inconnu')}")
            print(f" Titre: {infos_cv.get('titre', 'Non précisé')}")
            print(f"Expérience: {infos_cv.get('annees_experience', 0)} ans")
            print(f" Technologies: {len(technologies_finales)} compétences")
            print(f" Expériences: {len(infos_cv.get('experiences', []))} postes")

            # Sauvegarde en MongoDB
            print(f"\nSauvegarde en base de données...")
            pdf_name = filename.replace(".pdf", "_done.pdf")
            doc_mongo = {
                "nom_fichier": pdf_name,
                "nom": infos_cv.get("nom", "Inconnu"),
                "titre": infos_cv.get("titre", "Non précisé"),
                "technologies": technologies_finales,  # TOUTES les technologies normalisées
                "experiences": infos_cv.get("experiences", []),
                "annees_experience": infos_cv.get("annees_experience", 0),
                "resume":resume_cv
            }
            
            collection.insert_one(doc_mongo)
            print(" Données sauvegardées dans MongoDB")

            # Mise à jour du référentiel
            nouvelles_technos = ajouter_nouvelles_technologies(technologies_normalisees)

            # Renommage du fichier
            nouveau_chemin = os.path.join(PDF_FOLDER, pdf_name)
            os.rename(filepath, nouveau_chemin)
            print(f" Fichier renommé: {pdf_name}")

            print(f"\n SUCCÈS: {filename} traité avec succès!")
            print(f"    {len(technologies_finales)} technologies sauvegardées")
            print(f"  {nouvelles_technos} nouvelles technologies ajoutées au référentiel")

        except Exception as e:
            print(f"\n ERREUR sur {filename}: {e}")
            import traceback
            print(traceback.format_exc())

    client.close()
    print(f"\n ANALYSE TERMINÉE - Tous les fichiers ont été traités")

       