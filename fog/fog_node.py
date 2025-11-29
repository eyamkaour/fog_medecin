"""
FOG NODE 1 - Instance avec Coopération
Port: 5001
Spécialité: General / Surveillance générale
"""

import numpy as np
import os
import time
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import requests
from datetime import datetime

# NOUVEAU: Import de la coopération
from fog_cooperation import create_fog_cooperation, DEFAULT_FOG_NODES

app = Flask(__name__)

# ==================== CONFIGURATION ====================
FOG_NODE_ID = "FOG-001"
FOG_PORT = 5001
FOG_SPECIALTY = "general"
MODEL_PATH = "models/ecg_cnn.h5"
CLOUD_API_URL = "http://localhost:8070/api/receive_data"

# NOUVEAU: Créer l'instance de coopération
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

# NOUVEAU: Mapper les classes aux niveaux de criticité
CRITICALITY_MAP = {
    0: "normal",      # Normal Beat
    1: "warning",     # Supraventricular
    2: "critical"  # Ventricular (dangereux)

}

def predict_signal(signal):
    """Fonction de prédiction améliorée avec criticité"""
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
        
        # NOUVEAU: Déterminer la criticité
        status = CRITICALITY_MAP.get(class_id, "normal")
        alert = (class_id != 0) and (confidence > 0.7)
        
        return class_id, class_name, confidence, alert, status
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        return 0, "Error", 0.0, False, "normal"

@app.route("/predict", methods=["POST"])
def predict():
    """Endpoint de prédiction AVEC coopération"""
    try:
        data = request.json
        patient_id = data.get("patient_id", "unknown")
        signal = data.get("signal")
        
        if not signal or len(signal) != 187:
            return jsonify({"error": "Signal invalide"}), 400
        
        print(f"\n{'='*70}")
        print(f"🔍 [{FOG_NODE_ID}] Analyse patient {patient_id}")
        
        # Prédiction locale
        class_id, class_name, confidence, alert, status = predict_signal(signal)
        
        # NOUVEAU: Enrichir les données avec le status
        enriched_data = data.copy()
        enriched_data['status'] = status
        enriched_data['prediction_class'] = class_id
        enriched_data['confidence'] = confidence
        
        # NOUVEAU: Vérifier si ce fog est optimal pour ce cas
        optimal_node = fog_coop.get_node_by_specialty(enriched_data)
        
        # Si un autre fog est plus spécialisé ET c'est un cas critique/warning
        if optimal_node['id'] != FOG_NODE_ID and status in ['critical', 'warning']:
            print(f"🔀 Cas {status} - Délégation vers {optimal_node['id']} ({optimal_node['specialty']})")
            
            # Demander à l'autre fog d'analyser
            delegated_result = fog_coop.request_analysis_from_peer(
                enriched_data,
                optimal_node['specialty']
            )
            
            if delegated_result:
                print(f"✅ Analyse déléguée avec succès à {delegated_result.get('analyzed_by')}")
                return jsonify(delegated_result), 200
            else:
                print(f"⚠️ Délégation échouée, traitement local")
        
        # Traitement local si optimal ou délégation échouée
        print(f"🏥 [{FOG_NODE_ID}] Traitement local | {class_name} | Conf: {confidence:.2%} | Alerte: {alert}")
        
        # Préparer le résultat
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
            "fog_processing_time": datetime.now().isoformat()
        }
        
        # NOUVEAU: Si critique, partager l'alerte avec tous les fogs
        if status == 'critical' and confidence > 0.7:
            alert_data = {
                'alert_id': f"ALERT-{patient_id}-{int(time.time())}",
                'patient_id': patient_id,
                'severity': 'high',
                'class_name': class_name,
                'confidence': confidence,
                'message': f"Rythme cardiaque critique détecté: {class_name}"
            }
            
            shared_count = fog_coop.share_alert(alert_data)
            print(f"🚨 ALERTE CRITIQUE partagée avec {shared_count} fog nodes")
            analysis_result['alert_shared'] = True
            analysis_result['alert_recipients'] = shared_count
        
        # NOUVEAU: Synchroniser les données avec les autres fogs
        synced_fogs = fog_coop.sync_patient_data(patient_id, analysis_result)
        print(f"🔄 Données synchronisées avec: {synced_fogs}")
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

# ==================== NOUVELLES ROUTES DE COOPÉRATION ====================

@app.route("/alerts/share", methods=["POST"])
def receive_alert():
    """Recevoir une alerte critique d'un autre fog"""
    try:
        alert_data = request.json
        fog_coop.receive_shared_alert(alert_data)
        
        source_fog = alert_data.get('source_fog', 'unknown')
        patient_id = alert_data.get('patient_id', 'unknown')
        message = alert_data.get('message', '')
        
        print(f"\n{'='*70}")
        print(f"📢 [{FOG_NODE_ID}] ALERTE REÇUE de {source_fog}")
        print(f"   Patient: {patient_id}")
        print(f"   Message: {message}")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "alert_received", "fog_node": FOG_NODE_ID}), 200
        
    except Exception as e:
        print(f"❌ Erreur réception alerte: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/sync/patient", methods=["POST"])
def sync_patient():
    """Recevoir les données de synchronisation d'un autre fog"""
    try:
        sync_data = request.json
        patient_id = sync_data.get('patient_id', 'unknown')
        source_fog = sync_data.get('source_fog', 'unknown')
        
        print(f"🔄 [{FOG_NODE_ID}] Sync patient {patient_id} reçue de {source_fog}")
        
        # Ici vous pouvez stocker localement l'historique si besoin
        # patient_history[patient_id] = sync_data
        
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
        print(f"🚨 [{FOG_NODE_ID}] ÉVÉNEMENT CRITIQUE")
        print(f"   Source: {event_data.get('source_fog')}")
        print(f"   Type: {event_data.get('event_type')}")
        print(f"   Message: {event_data.get('message')}")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "event_received"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cooperation/status", methods=["GET"])
def cooperation_status():
    """État de la coopération entre fogs"""
    try:
        # Vérifier la santé des autres fogs
        health_status = fog_coop.get_system_health()
        
        # Récupérer les alertes partagées
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

# ==================== ROUTES EXISTANTES ====================

@app.route("/health", methods=["GET"])
def health():
    """Health check amélioré"""
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
    """Informations détaillées du fog node"""
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
    print(f"🌫️  [{FOG_NODE_ID}] FOG NODE avec Coopération - Démarrage")
    print("="*70)
    print(f"Port: {FOG_PORT}")
    print(f"Spécialité: {FOG_SPECIALTY}")
    print(f"Modèle: {MODEL_PATH}")
    print(f"Coopération: Activée avec {len(DEFAULT_FOG_NODES)-1} autres fogs")
    print("="*70 + "\n")
    
    app.run(host="0.0.0.0", port=FOG_PORT, debug=False, threaded=True)