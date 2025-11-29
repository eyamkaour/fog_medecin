"""
FOG NODE 3 - Instance avec Coopération
Port: 5003
Spécialité: Pediatric / Pédiatrie (cas normaux et suivi)
"""

import numpy as np
import os
import time
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import requests
from datetime import datetime

# Import de la coopération
from fog_cooperation import create_fog_cooperation, DEFAULT_FOG_NODES

app = Flask(__name__)

# ==================== CONFIGURATION ====================
FOG_NODE_ID = "FOG-003"
FOG_PORT = 5003
FOG_SPECIALTY = "pediatric"
MODEL_PATH = "models/ecg_cnn.h5"
CLOUD_API_URL = "http://localhost:8070/api/receive_data"

# Créer l'instance de coopération
print(f"[{FOG_NODE_ID}] Initialisation de la coopération...")
fog_coop = create_fog_cooperation(FOG_NODE_ID, DEFAULT_FOG_NODES)

# Charger le modèle
print(f"[{FOG_NODE_ID}] Chargement du modèle...")
model = load_model(MODEL_PATH)

CLASS_LABELS = {
    0: "Normal Beat",
    1: "Supraventricular", 
    2: "Ventricular"
}

CRITICALITY_MAP = {
    0: "normal",      # FOG-003 est spécialisé pour ces cas
    1: "warning",
    2: "critical"
   
}

def predict_signal(signal):
    """Fonction de prédiction avec criticité"""
    try:
        signal_array = np.array(signal, dtype=np.float32)
        signal_std = signal_array.std()
        
        if signal_std < 1e-8:
            signal_norm = signal_array - signal_array.mean()
        else:
            signal_norm = (signal_array - signal_array.mean()) / signal_std
        
        x = signal_norm.reshape(1, 187, 1)
        pred = model.predict(x, verbose=0)[0]
        class_id = int(np.argmax(pred))
        confidence = float(np.max(pred))
        class_name = CLASS_LABELS.get(class_id, f"Unknown Class {class_id}")
        status = CRITICALITY_MAP.get(class_id, "normal")
        alert = (class_id != 0) and (confidence > 0.7)
        
        return class_id, class_name, confidence, alert, status
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        return 0, "Error", 0.0, False, "normal"

@app.route("/predict", methods=["POST"])
def predict():
    """Endpoint de prédiction - Spécialisé en suivi normal"""
    try:
        data = request.json
        patient_id = data.get("patient_id", "unknown")
        signal = data.get("signal")
        
        if not signal or len(signal) != 187:
            return jsonify({"error": "Signal invalide"}), 400
        
        print(f"\n{'='*70}")
        print(f"🔍 [{FOG_NODE_ID}] 👶 SUIVI PÉDIATRIQUE - Patient {patient_id}")
        
        # Prédiction locale
        class_id, class_name, confidence, alert, status = predict_signal(signal)
        
        enriched_data = data.copy()
        enriched_data['status'] = status
        enriched_data['prediction_class'] = class_id
        enriched_data['confidence'] = confidence
        
        # Si c'est un cas critique ou warning, déléguer aux spécialistes
        optimal_node = fog_coop.get_node_by_specialty(enriched_data)
        
        if optimal_node['id'] != FOG_NODE_ID and status in ['critical', 'warning']:
            print(f"🔀 Cas {status} - Transfert vers {optimal_node['id']} ({optimal_node['specialty']})")
            print(f"   >>> Patient nécessite surveillance spécialisée")
            
            delegated_result = fog_coop.request_analysis_from_peer(
                enriched_data,
                optimal_node['specialty']
            )
            
            if delegated_result:
                print(f"✅ Patient transféré avec succès")
                return jsonify(delegated_result), 200
            else:
                print(f"⚠️ Transfert échoué, traitement local d'urgence")
        
        # Traitement local (cas normaux principalement)
        print(f"🏥 [{FOG_NODE_ID}] 👍 SUIVI | {class_name} | Conf: {confidence:.2%} | Alerte: {alert}")
        
        analysis_result = {
            "patient_id": patient_id,
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "class_id": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "alert": alert,
            "status": status,
            "fog_node_id": FOG_NODE_ID,
            "fog_specialty": FOG_SPECIALTY,
            "care_level": "routine" if status == "normal" else "elevated",
            "fog_processing_time": datetime.now().isoformat()
        }
        
        # Même en suivi pédiatrique, partager les alertes si anormal
        if status in ['critical', 'warning'] and confidence > 0.7:
            alert_data = {
                'alert_id': f"ALERT-{patient_id}-{int(time.time())}",
                'patient_id': patient_id,
                'severity': 'high' if status == 'critical' else 'medium',
                'class_name': class_name,
                'confidence': confidence,
                'message': f"Anomalie détectée en suivi pédiatrique: {class_name}"
            }
            
            shared_count = fog_coop.share_alert(alert_data)
            print(f"⚠️ Alerte partagée avec {shared_count} fog nodes (surveillance renforcée)")
            analysis_result['alert_shared'] = True
            analysis_result['alert_recipients'] = shared_count
        
        # Synchroniser (important pour historique patient)
        synced_fogs = fog_coop.sync_patient_data(patient_id, analysis_result)
        print(f"🔄 Historique patient synchronisé avec: {synced_fogs}")
        analysis_result['synced_with'] = synced_fogs
        
        # Envoyer au Cloud
        cloud_status = "N/A"
        try:
            r = requests.post(CLOUD_API_URL, json=analysis_result, timeout=5)
            cloud_status = r.status_code
            print(f"☁️ Envoyé au Cloud: {cloud_status}")
        except Exception as e:
            cloud_status = f"Erreur: {str(e)}"
            print(f"❌ Erreur Cloud: {e}")
        
        analysis_result['cloud_status'] = cloud_status
        
        print(f"{'='*70}\n")
        
        return jsonify(analysis_result), 200
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== ROUTES DE COOPÉRATION ====================

@app.route("/alerts/share", methods=["POST"])
def receive_alert():
    """Recevoir une alerte d'un autre fog"""
    try:
        alert_data = request.json
        fog_coop.receive_shared_alert(alert_data)
        
        source_fog = alert_data.get('source_fog', 'unknown')
        patient_id = alert_data.get('patient_id', 'unknown')
        message = alert_data.get('message', '')
        severity = alert_data.get('severity', 'unknown')
        
        print(f"\n{'='*70}")
        print(f"📢 [{FOG_NODE_ID}] ALERTE REÇUE de {source_fog}")
        print(f"   Patient: {patient_id}")
        print(f"   Sévérité: {severity}")
        print(f"   Message: {message}")
        print(f"   >>> Équipe pédiatrique informée")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "alert_received", "fog_node": FOG_NODE_ID}), 200
        
    except Exception as e:
        print(f"❌ Erreur réception alerte: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/sync/patient", methods=["POST"])
def sync_patient():
    """Recevoir les données de synchronisation"""
    try:
        sync_data = request.json
        patient_id = sync_data.get('patient_id', 'unknown')
        source_fog = sync_data.get('source_fog', 'unknown')
        
        print(f"🔄 [{FOG_NODE_ID}] Sync patient {patient_id} de {source_fog} (dossier médical)")
        
        return jsonify({"status": "synced", "fog_node": FOG_NODE_ID}), 200
        
    except Exception as e:
        print(f"❌ Erreur sync: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/events/critical", methods=["POST"])
def receive_critical_event():
    """Recevoir un événement système critique"""
    try:
        event_data = request.json
        
        print(f"\n{'='*70}")
        print(f"🚨 [{FOG_NODE_ID}] ÉVÉNEMENT SYSTÈME CRITIQUE")
        print(f"   Source: {event_data.get('source_fog')}")
        print(f"   Type: {event_data.get('event_type')}")
        print(f"   Message: {event_data.get('message')}")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "event_received"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cooperation/status", methods=["GET"])
def cooperation_status():
    """État de la coopération"""
    try:
        health_status = fog_coop.get_system_health()
        shared_alerts = fog_coop.get_shared_alerts()
        
        return jsonify({
            "current_fog": FOG_NODE_ID,
            "specialty": FOG_SPECIALTY,
            "fog_nodes_health": health_status,
            "shared_alerts_count": len(shared_alerts),
            "recent_alerts": shared_alerts[-5:] if shared_alerts else []
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "fog_node_id": FOG_NODE_ID,
        "specialty": FOG_SPECIALTY,
        "model_loaded": True,
        "cooperation_enabled": True,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/info", methods=["GET"])
def info():
    """Informations du fog node"""
    return jsonify({
        "fog_node_id": FOG_NODE_ID,
        "port": FOG_PORT,
        "specialty": FOG_SPECIALTY,
        "model": "ecg_cnn.h5",
        "status": "active",
        "cooperation": "enabled",
        "connected_fogs": len(DEFAULT_FOG_NODES) - 1
    }), 200

if __name__ == "__main__":
    print("\n" + "="*70)
    print(f"🌫️  [{FOG_NODE_ID}] 👶 FOG NODE PÉDIATRIQUE - Démarrage")
    print("="*70)
    print(f"Port: {FOG_PORT}")
    print(f"Spécialité: {FOG_SPECIALTY.upper()} (Suivi routine)")
    print(f"Modèle: {MODEL_PATH}")
    print(f"Coopération: Activée avec {len(DEFAULT_FOG_NODES)-1} autres fogs")
    print("="*70 + "\n")
    
    app.run(host="0.0.0.0", port=FOG_PORT, debug=False, threaded=True)