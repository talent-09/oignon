import serial
import json
import time
import os
import requests

PORT = 'COM3'
BAUDRATE = 115200
FICHIER_JSON = 'donnee/suivi.json'
FIREBASE_URL = 'https://pourriture-d-oignon-2-default-rtdb.firebaseio.com/courant.json'

historique = {
    "temperature": [],
    "humidite": [],
    "gaz": [],
    "labels": []
}

def oignon():
    try:
        arduino = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"Connexion au port {PORT} réussie.")
        time.sleep(2)

        # Charger les anciennes données si le fichier existe
        if os.path.exists(FICHIER_JSON):
            with open(FICHIER_JSON, 'r', encoding='utf-8') as f:
                try:
                    suivi_data = json.load(f)
                    if not isinstance(suivi_data, list):
                        suivi_data = []
                except json.JSONDecodeError:
                    suivi_data = []
        else:
            suivi_data = []

        while True:
            ligne = arduino.readline().decode('utf-8', errors='ignore').strip()
            if ligne:
                try:
                    donnee = json.loads(ligne)
                    print("✅ Données reçues :", donnee)

                    t = donnee.get("temperature")
                    h = donnee.get("humidite")
                    g = donnee.get("gaz")
                    ts = time.strftime("%Y-%m-%d %H:%M:%S")

                    if all(v is not None for v in [t, h, g]):
                        historique["temperature"].append(t)
                        historique["humidite"].append(h)
                        historique["gaz"].append(g)
                        historique["labels"].append(time.strftime("%H:%M:%S"))

                        for key in historique:
                            historique[key] = historique[key][-20:]

                        donnee["historique"] = historique
                        donnee["date"] = ts

                        # ➕ Ajout aux données locales
                        suivi_data.append(donnee)
                        suivi_data = suivi_data[-100:]

                        # 💾 Enregistrement dans le fichier JSON local
                        with open(FICHIER_JSON, 'w', encoding='utf-8') as f:
                            json.dump(suivi_data, f, indent=2, ensure_ascii=False)

                        # 📤 Envoi vers Firebase
                        try:
                            response = requests.put(FIREBASE_URL, data=json.dumps(donnee), headers={'Content-Type': 'application/json'})
                            if response.status_code == 200:
                                print("✅ Données envoyées à Firebase.")
                            else:
                                print(f"❌ Erreur Firebase : {response.status_code}")
                        except requests.exceptions.RequestException as e:
                            print("🚫 Problème de connexion à Firebase :", e)

                except json.JSONDecodeError:
                    print("❌ Ligne non JSON:", ligne)

    except serial.SerialException:
        print(f"Erreur : impossible d'ouvrir le port {PORT}")

if __name__ == '__main__':
    os.makedirs('donnee', exist_ok=True)
    oignon()