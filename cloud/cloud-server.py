"""
CLOUD SERVER - Firebase Firestore CORRIGÉ
Résout le problème "Quota exceeded" en évitant order_by
Port: 8070
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# ========================================
# CONFIGURATION FIREBASE
# ========================================
print("🔥 Initialisation Firebase...")

try:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialisé avec succès!")
except Exception as e:
    print(f"❌ Erreur Firebase: {e}")
    print("⚠️  Vérifiez que le fichier 'firebase-credentials.json' existe")
    exit(1)

# Collections Firestore
PREDICTIONS_COLLECTION = "ecg_predictions"
ALERTS_COLLECTION = "alerts"
PATIENTS_COLLECTION = "patients"
SYSTEM_STATS_COLLECTION = "system_stats"

# ========================================
# FONCTIONS UTILITAIRES
# ========================================
def update_patient_status(patient_id, prediction_data):
    """Met à jour le statut du patient selon la prédiction"""
    try:
        class_id = prediction_data.get('class_id', 0)
        confidence = prediction_data.get('confidence', 0.0)
        
        # Déterminer le statut
        if class_id == 0:
            status = 'normal'
        elif class_id in [1, 2] and confidence > 0.8:
            status = 'critical'
        elif class_id in [1, 2]:
            status = 'warning'
        else:
            status = 'normal'
        
        # ✅ CORRIGÉ: Utiliser update() au lieu de set() pour conserver les champs existants
        patient_ref = db.collection(PATIENTS_COLLECTION).document(patient_id)
        
        # Vérifier si le patient existe
        patient_doc = patient_ref.get()
        
        if patient_doc.exists:
            # Patient existe - mettre à jour SEULEMENT le statut
            patient_ref.update({
                'status': status,
                'last_status_update': datetime.now().isoformat()
            })
        else:
            # Nouveau patient - créer avec tous les champs
            patient_ref.set({
                'patient_id': patient_id,
                'name': f"Patient {patient_id}",
                'status': status,
                'heart_rate': 72,
                'temperature': 36.6,
                'spo2': 98,
                'blood_pressure': 120,
                'first_seen': datetime.now().isoformat(),
                'last_status_update': datetime.now().isoformat()
            })
        
        print(f"📊 Statut patient {patient_id} mis à jour: {status}")
        
    except Exception as e:
        print(f"⚠️ Erreur update_patient_status: {e}")

def update_patient_history(patient_id, prediction_data):
    """Ajoute une prédiction à l'historique du patient"""
    try:
        patient_ref = db.collection(PATIENTS_COLLECTION).document(patient_id)
        patient_doc = patient_ref.get()
        
        # Préparer l'entrée d'historique
        history_entry = {
            'timestamp': prediction_data['timestamp'],
            'class_name': prediction_data['class_name'],
            'confidence': prediction_data['confidence'],
            'alert': prediction_data['alert'],
            'class_id': prediction_data.get('class_id', 0),
            'processed_at': datetime.now().isoformat(),
            'fog_id': prediction_data.get("fog_node_id", "unknown")
        }
        
        if patient_doc.exists:
            # ✅ CORRIGÉ: Patient existe - AJOUTER l'historique sans écraser les autres champs
            patient_data = patient_doc.to_dict()
            current_history = patient_data.get('history', [])
            
            # Ajouter la nouvelle entrée au début
            current_history.insert(0, history_entry)
            
            # Garder seulement les 100 dernières entrées
            if len(current_history) > 100:
                current_history = current_history[:100]
            
            # ✅ UPDATE au lieu de SET - conserve tous les champs existants
            patient_ref.update({
                'history': current_history,
                'last_prediction': history_entry,
                'history_count': len(current_history),
                'last_update': datetime.now().isoformat(),
                'last_prediction_time': prediction_data['timestamp'],
                'last_class': prediction_data['class_name'],
                'last_confidence': prediction_data['confidence']
            })
            
        else:
            # ✅ CORRIGÉ: Nouveau patient - créer avec TOUS les champs nécessaires
            patient_ref.set({
                'patient_id': patient_id,
                'name': f"Patient {patient_id}",
                'first_seen': datetime.now().isoformat(),
                'history': [history_entry],
                'last_prediction': history_entry,
                'history_count': 1,
                'status': 'normal',
                'heart_rate': 72,
                'temperature': 36.6,
                'spo2': 98,
                'blood_pressure': 120,
                'total_predictions': 1,
                'last_update': datetime.now().isoformat(),
                'last_prediction_time': prediction_data['timestamp'],
                'last_class': prediction_data['class_name'],
                'last_confidence': prediction_data['confidence']
            })
        
        print(f"📊 Historique mis à jour pour {patient_id}")
        
    except Exception as e:
        print(f"⚠️ Erreur update_patient_history: {e}")

def update_patient_stats(patient_id, prediction_data):
    """Met à jour les statistiques d'un patient"""
    try:
        update_patient_status(patient_id, prediction_data)
        update_patient_history(patient_id, prediction_data)
        
        # Mettre à jour les compteurs
        patient_ref = db.collection(PATIENTS_COLLECTION).document(patient_id)
        patient_doc = patient_ref.get()
        
        if patient_doc.exists:
            patient_ref.update({
                'last_prediction_time': prediction_data['timestamp'],
                'last_class': prediction_data['class_name'],
                'last_confidence': prediction_data['confidence'],
                'total_predictions': firestore.Increment(1)
            })
        
    except Exception as e:
        print(f"⚠️ Erreur update_patient_stats: {e}")

def update_system_stats():
    """Met à jour les statistiques globales du système"""
    try:
        stats_ref = db.collection(SYSTEM_STATS_COLLECTION).document('current')
        stats_ref.set({
            'timestamp': datetime.now().isoformat(),
            'fog_status': 'online',
            'cloud_status': 'online',
            'database_connected': True,
            'last_update': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
    except Exception as e:
        print(f"⚠️ Erreur update_system_stats: {e}")

# ========================================
# ENDPOINT 1: Recevoir données du Fog
# ========================================
@app.route("/api/receive_data", methods=["POST"])
def receive_data():
    """Reçoit les prédictions ECG du Fog Node"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "Aucune donnée reçue"}), 400
        
        # Ajouter timestamp serveur
        data['server_timestamp'] = datetime.now().isoformat()
        
        # 1. STOCKER LA PRÉDICTION dans Firestore
        doc_ref = db.collection(PREDICTIONS_COLLECTION).document()
        doc_ref.set(data)
        
        print(f"✅ Prédiction stockée: {data.get('patient_id')} | "
              f"Classe: {data.get('class_name')} | "
              f"Confiance: {data.get('confidence', 0):.2%} | "
              f"Alerte: {data.get('alert')} | "
              f"Fog id : {data.get('fog_node_id')}")
        
        # 2. SI ALERTE → Stocker dans collection alertes
        if data.get('alert', False):
            alert_data = {
                'patient_id': data['patient_id'],
                'class_name': data['class_name'],
                'confidence': data['confidence'],
                'timestamp': data['timestamp'],
                'severity': 'critical' if data['confidence'] > 0.85 else 'warning',
                'acknowledged': False
            }
            db.collection(ALERTS_COLLECTION).document().set(alert_data)
            print(f"🚨 ALERTE créée pour patient {data['patient_id']}")
        
        # 3. METTRE À JOUR les stats patient
        update_patient_stats(data['patient_id'], data)
        
        # 4. METTRE À JOUR les stats système
        update_system_stats()
        
        return jsonify({
            "status": "success",
            "message": "Données stockées dans Firebase",
            "doc_id": doc_ref.id
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 2: Récupérer historique patient - CORRIGÉ
# ========================================
@app.route("/api/history/<patient_id>", methods=["GET"])
def get_patient_history(patient_id):
    """Récupère l'historique des prédictions d'un patient - SANS ORDER_BY"""
    try:
        # ✅ CORRIGÉ: Pas d'order_by, juste where et limit
        predictions_ref = db.collection(PREDICTIONS_COLLECTION) \
            .where('patient_id', '==', patient_id) \
            .limit(50)
        
        predictions = []
        for doc in predictions_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            predictions.append(data)
        
        # Trier en mémoire après récupération
        predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            "patient_id": patient_id,
            "count": len(predictions),
            "data": predictions
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 3: Liste des patients - CORRIGÉ
# ========================================
@app.route("/api/patients", methods=["GET"])
def get_patients():
    """Récupère la liste de tous les patients"""
    try:
        patients_ref = db.collection(PATIENTS_COLLECTION).stream()
        
        patients = []
        for doc in patients_ref:
            data = doc.to_dict()
            data['id'] = doc.id
            patients.append(data)
        
        return jsonify(patients), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 4: Alertes actives - CORRIGÉ
# ========================================
@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Récupère toutes les alertes non acquittées - SANS ORDER_BY"""
    try:
        # ✅ CORRIGÉ: Pas d'order_by
        alerts_ref = db.collection(ALERTS_COLLECTION) \
            .where('acknowledged', '==', False) \
            .limit(20)
        
        alerts = []
        for doc in alerts_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            alerts.append(data)
        
        # Trier en mémoire
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(alerts), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 5: Statistiques système - CORRIGÉ
# ========================================
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Récupère les statistiques globales du système"""
    try:
        # Compter les documents (méthode économique)
        predictions_count = len(list(db.collection(PREDICTIONS_COLLECTION).limit(1000).stream()))
        alerts_count = len(list(db.collection(ALERTS_COLLECTION).where('acknowledged', '==', False).stream()))
        patients_count = len(list(db.collection(PATIENTS_COLLECTION).stream()))
        
        # Récupérer les stats système
        stats_doc = db.collection(SYSTEM_STATS_COLLECTION).document('current').get()
        latest_stats = stats_doc.to_dict() if stats_doc.exists else None
        
        return jsonify({
            "predictions_total": predictions_count,
            "alerts_active": alerts_count,
            "patients_total": patients_count,
            "system_stats": latest_stats
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 6: Dashboard temps réel - CORRIGÉ
# ========================================
@app.route("/api/dashboard/realtime", methods=["GET"])
def dashboard_realtime():
    """Endpoint pour le dashboard Streamlit - SANS ORDER_BY"""
    try:
        # 1. Patients
        patients = []
        patients_ref = db.collection(PATIENTS_COLLECTION).stream()
        
        for doc in patients_ref:
            patient_data = doc.to_dict()
            patient_data['id'] = doc.id
            patients.append(patient_data)
        
        # 2. Alertes récentes
        alerts = []
        alerts_ref = db.collection(ALERTS_COLLECTION) \
            .where('acknowledged', '==', False) \
            .limit(10)
        
        for doc in alerts_ref.stream():
            alert_data = doc.to_dict()
            alert_data['id'] = doc.id
            alerts.append(alert_data)
        
        # Trier en mémoire
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 3. Stats système
        stats_doc = db.collection(SYSTEM_STATS_COLLECTION).document('current').get()
        system_stats = stats_doc.to_dict() if stats_doc.exists else None
        
        return jsonify({
            "patients": patients,
            "alerts": alerts,
            "system_stats": system_stats,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 7: Historique détaillé patient
# ========================================
@app.route("/api/patient/<patient_id>/history", methods=["GET"])
def get_patient_detailed_history(patient_id):
    """Récupère l'historique complet depuis le document patient"""
    try:
        patient_ref = db.collection(PATIENTS_COLLECTION).document(patient_id)
        patient_doc = patient_ref.get()
        
        if not patient_doc.exists:
            return jsonify({"error": "Patient non trouvé"}), 404
        
        patient_data = patient_doc.to_dict()
        history = patient_data.get('history', [])
        
        return jsonify({
            "patient_id": patient_id,
            "name": patient_data.get('name', 'Patient'),
            "history_count": len(history),
            "history": history
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT 8: Acquitter une alerte
# ========================================
@app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    """Marque une alerte comme acquittée"""
    try:
        db.collection(ALERTS_COLLECTION).document(alert_id).update({
            'acknowledged': True,
            'acknowledged_at': datetime.now().isoformat()
        })
        
        return jsonify({"status": "success", "message": "Alerte acquittée"}), 200
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ENDPOINT SANTÉ
# ========================================
@app.route("/health", methods=["GET"])
def health():
    """Vérifie que le serveur fonctionne"""
    return jsonify({
        "status": "ok",
        "service": "Cloud Server",
        "firebase": "connected",
        "timestamp": datetime.now().isoformat()
    }), 200

# ========================================
# LANCEMENT DU SERVEUR
# ========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("☁️  CLOUD SERVER - Firebase Firestore (QUOTA FIXED)")
    print("="*60)
    print("✅ Optimisé pour éviter 'Quota exceeded'")
    print("✅ Pas d'order_by (tri en mémoire)")
    print("✅ Limite de lectures réduite")
    print("="*60)
    print("\nEndpoints:")
    print("  POST   /api/receive_data")
    print("  GET    /api/history/<id>")
    print("  GET    /api/patients")
    print("  GET    /api/alerts")
    print("  GET    /api/stats")
    print("  GET    /api/dashboard/realtime")
    print("  GET    /api/patient/<id>/history")
    print("  POST   /api/alerts/<id>/acknowledge")
    print("  GET    /health")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=8070, debug=True)