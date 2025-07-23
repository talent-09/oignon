from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from functools import wraps
from datetime import datetime
import json
import os
import requests

# Fonction pour envoyer une alerte WhatsApp via CallMeBot
def envoyer_whatsapp(message):
    numero = "221778242154"
    apikey = "4087867"
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": numero,
        "text": message,
        "apikey": apikey
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("✅ Message WhatsApp envoyé avec succès.")
        else:
            print(f"❌ Erreur WhatsApp : {response.text}")
    except Exception as e:
        print(f"❌ Exception WhatsApp : {e}")

# Configuration de l'application Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# Fonction pour enregistrer une alerte dans le fichier JSON
def enregistrer_alerte(donnee_alerte):
    chemin = "donnee/alerte.json"
    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            alertes = json.load(f)
    else:
        alertes = []
    alertes.append(donnee_alerte)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(alertes, f, indent=2, ensure_ascii=False)

# Authentification utilisateur
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Accès réservé à l'administrateur.", "danger")
            return redirect(url_for("accueil"))
        return f(*args, **kwargs)
    return wrapped

@app.route('/')
def accueil():
    return render_template("accueil.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            session["user"] = username
            session["role"] = "admin"
            return redirect(url_for("accueil"))
        elif username == "user" and password == "user":
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("accueil"))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("login"))

@app.route('/suivi')
@login_required
def suivi():
    with open("donnee/suivi.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        flash("Le fichier suivi.json est mal structuré (doit être une liste).", "danger")
        data = []

    dernier = data[-1] if data else {}
    alertes = []

    if dernier.get("gaz", 0) >1000:
        msg = f"🚨 Gaz élevé détecté : {dernier['gaz']} ppm le {dernier['date']}"
        alerte_data = {
            "date": dernier["date"],
            "type": "gaz",
            "niveau": "critique",
            "gaz": dernier["gaz"],
            "message": msg
        }
        alertes.append(alerte_data)
        enregistrer_alerte(alerte_data)

    if dernier.get("temperature", 0) > 30:
        msg = f"🌡 Température élevée : {dernier['temperature']} °C le {dernier['date']}"
        alerte_data = {
            "date": dernier["date"],
            "type": "temperature",
            "niveau": "moyenne",
            "temperature": dernier["temperature"],
            "message": msg
        }
        alertes.append(alerte_data)
        enregistrer_alerte(alerte_data)

    if dernier.get("humidite", 100) < 30:
        msg = f"💧 Humidité faible : {dernier['humidite']} % le {dernier['date']}"
        alerte_data = {
            "date": dernier["date"],
            "type": "humidite",
            "niveau": "basse",
            "humidite": dernier["humidite"],
            "message": msg
        }
        alertes.append(alerte_data)
        enregistrer_alerte(alerte_data)

    for alerte in alertes:
        envoyer_whatsapp(alerte["message"])

    return render_template("suivi.html", data=data)

@app.route('/alerte')
@login_required
def alerte():
    with open("donnee/alerte.json", "r", encoding="utf-8") as f:
        alertes = json.load(f)
        alertes=alertes[::-1]
        alertes.reverse

    for alerte in alertes:
        try:
            alerte["message"] = alerte["message"].encode("latin1").decode("utf-8")
        except:
            pass

    return render_template("alerte.html", alertes=alertes)

@app.route('/stock', methods=["GET", "POST"])
@login_required
@admin_required
def stock():
    stock_file = "donnee/stock.json"
    historique_file = "donnee/historique_stock.json"

    if os.path.exists(stock_file):
        with open(stock_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"quantite": 0, "pourriture": 0}

    if os.path.exists(historique_file):
        with open(historique_file, "r", encoding="utf-8") as f:
            historique = json.load(f)
    else:
        historique = []

    if request.method == "POST":
        action = request.form.get("action")
        try:
            quantite = int(request.form.get("quantite", 0))
        except ValueError:
            quantite = 0

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if action == "ajouter":
            data["quantite"] += quantite
            flash(f"{quantite} kg ajoutés au stock.", "success")
            historique.append({
                "date": now_str,
                "action": "Ajout",
                "quantite": quantite
            })

        elif action == "retirer":
            if quantite > data["quantite"]:
                flash("Quantité à retirer trop élevée.", "danger")
            else:
                data["quantite"] -= quantite
                flash(f"{quantite} kg retirés du stock (vente).", "success")
                historique.append({
                    "date": now_str,
                    "action": "Sortie",
                    "quantite": quantite
                })

        elif action == "retirer_pourriture":
            if quantite > data["quantite"]:
                flash("Quantité à retirer trop élevée.", "danger")
            else:
                data["quantite"] -= quantite
                data["pourriture"] += quantite
                flash(f"{quantite} kg retirés du stock (pourriture).", "warning")
                historique.append({
                    "date": now_str,
                    "action": "Retrait pourriture",
                    "quantite": quantite
                })

        with open(stock_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        with open(historique_file, "w", encoding="utf-8") as f:
            json.dump(historique, f, indent=4, ensure_ascii=False)

    return render_template("stock.html", quantite=data["quantite"], pourriture=data["pourriture"], historique=historique)

@app.route('/stock/effacer_historique', methods=['POST'])
@login_required
@admin_required
def effacer_historique():
    historique_file = "donnee/historique_stock.json"
    if os.path.exists(historique_file):
        os.remove(historique_file)
        flash("Historique effacé avec succès.", "success")
    else:
        flash("Aucun historique à effacer.", "warning")
    return redirect(url_for('stock'))

@app.route('/api/suivi')
def api_suivi():
    try:
        chemin = "donnee/suivi.json"
        if not os.path.exists(chemin):
            return jsonify([])

        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return jsonify(data)
        else:
            print("⚠ Fichier JSON n'est pas une liste :", type(data))
            return jsonify([])

    except json.JSONDecodeError as e:
        print("❌ Erreur JSON :", e)
        return jsonify({"error": "Fichier JSON malformé"}), 500

    except Exception as e:
        print("❌ Erreur inattendue :", e)
        return jsonify({"error": "Erreur lors de la lecture des données"}), 500

# ✅ Corrigé ici aussi
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)