import numpy as np
import os
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import requests

app = Flask(__name__)

# -------------------------
# Charger modèle ML Keras (.h5)
# -------------------------
MODEL_PATH = "models/ecg_cnn.h5"

if not os.path.exists(MODEL_PATH):
    print(f"ERREUR: Le modèle {MODEL_PATH} n'existe pas!")
    print("Veuillez d'abord exécuter: python train_CNNmodel.py")
    exit(1)

print(f"Chargement du modèle depuis {MODEL_PATH}...")
model = load_model(MODEL_PATH)
print("✓ Modèle chargé avec succès!")

# -------------------------
# Configuration Cloud
# -------------------------
CLOUD_API_URL = "http://localhost:8000/api/receive_data"

# Labels des classes ECG (MIT-BIH Dataset)
CLASS_LABELS = {
    0: "Normal Beat",           # Battement normal
    1: "Supraventricular",      # Battement ectopique supraventriculaire
    2: "Ventricular",           # Battement ectopique ventriculaire
    3: "Fusion Beat",           # Battement de fusion
    4: "Unclassified"          # Non classifié
}

# -------------------------
# Fonction prédiction
# -------------------------
def predict_signal(signal):
    """
    Prédit la classe d'un signal ECG
    Args:
        signal: liste ou array de 187 valeurs
    Returns:
        class_id, class_name, confidence, alert
    """
    try:
        # Normalisation du signal
        signal_array = np.array(signal, dtype=np.float32)
        signal_std = signal_array.std()
        
        # Éviter division par zéro
        if signal_std < 1e-8:
            signal_norm = signal_array - signal_array.mean()
        else:
            signal_norm = (signal_array - signal_array.mean()) / signal_std
        
        # Reshape pour le modèle (1, 187, 1)
        x = signal_norm.reshape(1, 187, 1)
        
        # Prédiction
        pred = model.predict(x, verbose=0)[0]
        class_id = int(np.argmax(pred))
        confidence = float(np.max(pred))
        
        # Récupérer le nom de la classe
        class_name = CLASS_LABELS.get(class_id, f"Unknown Class {class_id}")
        
        # Debug: afficher les probabilités pour toutes les classes
        print(f"  [DEBUG] Probabilités: ", end="")
        for i, prob in enumerate(pred):
            print(f"Classe {i}: {prob:.3f} ", end="")
        print()
        
        # Alerte si anomalie détectée avec confiance élevée
        alert = (class_id != 0) and (confidence > 0.7)
        
        return class_id, class_name, confidence, alert
        
    except Exception as e:
        print(f"❌ Erreur dans predict_signal: {e}")
        return 0, "Error", 0.0, False

# -------------------------
# Endpoint Flask pour recevoir données IoT
# -------------------------
@app.route("/predict", methods=["POST"])
def predict():
    """
    Endpoint pour recevoir les signaux ECG et faire des prédictions
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Aucune donnée reçue"}), 400
        
        patient_id = data.get("patient_id", "unknown")
        signal = data.get("signal")
        
        # Validation du signal
        if not signal:
            return jsonify({"error": "Signal manquant"}), 400
        
        if len(signal) != 187:
            return jsonify({
                "error": f"Signal invalide: {len(signal)} points (187 requis)"
            }), 400
        
        # Prédiction
        class_id, class_name, confidence, alert = predict_signal(signal)
        
        # Affichage dans le terminal avec code couleur
        alert_symbol = "🚨 ALERTE" if alert else "✓"
        print(f"{alert_symbol} Patient: {patient_id} | "
              f"Classe: {class_name} ({class_id}) | "
              f"Confiance: {confidence:.2%} | "
              f"Alerte: {alert}")
        
        # Préparer payload pour Cloud
        payload = {
            "patient_id": patient_id,
            "timestamp": data.get("timestamp", ""),
            "prediction": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "alert": alert,
            "signal": signal  # Optionnel: envoyer le signal complet
        }
        
        # Envoyer au Cloud
        cloud_status = "N/A"
        try:
            r = requests.post(CLOUD_API_URL, json=payload, timeout=5)
            cloud_status = r.status_code
            if r.status_code == 200:
                print(f"  → Données envoyées au Cloud (Status: {cloud_status})")
        except requests.exceptions.ConnectionError:
            cloud_status = "Cloud non disponible"
            print(f"  ⚠ Avertissement: {cloud_status}")
        except Exception as e:
            cloud_status = f"Erreur: {str(e)}"
            print(f"  ⚠ Erreur Cloud: {e}")
        
        # Réponse au client
        return jsonify({
            "patient_id": patient_id,
            "class_id": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "alert": alert,
            "cloud_status": cloud_status
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500

# -------------------------
# Endpoint de santé
# -------------------------
@app.route("/health", methods=["GET"])
def health():
    """Vérifie que le serveur fonctionne"""
    return jsonify({
        "status": "ok",
        "model_loaded": True,
        "model_path": MODEL_PATH
    }), 200

# -------------------------
# Lancer serveur Flask
# -------------------------
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🌫️  FOG NODE SERVER - Démarrage")
    print("="*50)
    print(f"Modèle: {MODEL_PATH}")
    print(f"Cloud API: {CLOUD_API_URL}")
    print(f"Port: 5000")
    print("="*50 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)