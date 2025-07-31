# analyse_auto.py
import time
from Analyse import analyser_cv

if __name__ == "__main__":
    print(" Analyse automatique lancée")
    while True:
        print("\n Lancement de l'analyse des CV...")
        analyser_cv()
        print(" Attente de 10 minutes avant la prochaine analyse...")
        time.sleep(60)  
