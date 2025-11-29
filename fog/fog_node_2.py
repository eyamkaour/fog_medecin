"""
FOG NODE 2 - EXPLIQUÉ EN DÉTAIL
Port: 5002
Spécialité: Critical Care (Soins intensifs)

CE FOG EST SPÉCIALISÉ DANS LES CAS CRITIQUES !
Il reçoit les patients graves et alerte tous les autres fogs
"""

import numpy as np
import os
import time
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import requests
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# PARTIE 1: IMPORT DE LA COOPÉRATION
# ═══════════════════════════════════════════════════════════════════════════
# EXPLICATION: Cette ligne importe le système de coopération entre fogs
# fog_cooperation.py contient toutes les fonctions pour communiquer entre fogs
from fog_cooperation import create_fog_cooperation, DEFAULT_FOG_NODES

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# PARTIE 2: CONFIGURATION DE CE FOG NODE
# ═══════════════════════════════════════════════════════════════════════════

FOG_NODE_ID = "FOG-002"          # Mon identifiant unique
FOG_PORT = 5002                  # Mon port (différent des autres fogs)
FOG_SPECIALTY = "critical_care"  # Ma spécialité = CAS CRITIQUES
MODEL_PATH = "models/ecg_cnn.h5"
CLOUD_API_URL = "http://localhost:8070/api/receive_data"

# ═══════════════════════════════════════════════════════════════════════════
# PARTIE 3: CRÉATION DE L'INSTANCE DE COOPÉRATION
# ═══════════════════════════════════════════════════════════════════════════
# EXPLICATION IMPORTANTE:
# fog_coop = C'est mon "téléphone" pour parler aux autres fogs !
# 
# DEFAULT_FOG_NODES contient la liste de TOUS les fogs:
# [
#   {"id": "FOG-001", "url": "http://localhost:5001", "specialty": "general"},
#   {"id": "FOG-002", "url": "http://localhost:5002", "specialty": "critical_care"}, <- MOI
#   {"id": "FOG-003", "url": "http://localhost:5003", "specialty": "pediatric"}
# ]
#
# Grâce à fog_coop, je peux:
# - Envoyer des alertes à FOG-001 et FOG-003
# - Demander à un autre fog d'analyser un patient
# - Synchroniser les données patients
# - Vérifier si les autres fogs sont en ligne

print(f"[{FOG_NODE_ID}] Initialisation de la coopération...")
fog_coop = create_fog_cooperation(FOG_NODE_ID, DEFAULT_FOG_NODES)
# Maintenant fog_coop SAIT que je suis FOG-002 et connaît FOG-001 et FOG-003

# Charger le modèle IA
print(f"[{FOG_NODE_ID}] Chargement du modèle...")
model = load_model(MODEL_PATH)

CLASS_LABELS = {
    0: "Normal Beat",
    1: "Supraventricular", 
    2: "Ventricular"        # <- CAS CRITIQUE !

}

# ═══════════════════════════════════════════════════════════════════════════
# PARTIE 4: MAPPING DES NIVEAUX DE CRITICITÉ
# ═══════════════════════════════════════════════════════════════════════════
# EXPLICATION:
# Chaque classe de rythme cardiaque a un niveau de gravité
# - normal   = tout va bien, pas urgent
# - warning  = à surveiller
# - critical = URGENCE MÉDICALE !
#
# FOG-002 est SPÉCIALISÉ dans les "critical"

CRITICALITY_MAP = {
    0: "normal",      # Normal Beat = pas grave
    1: "warning",     # Supraventricular = à surveiller
    2: "critical"    # Ventricular = DANGER ! <- MON EXPERTISE
  
}

# ═══════════════════════════════════════════════════════════════════════════
# FONCTION DE PRÉDICTION
# ═══════════════════════════════════════════════════════════════════════════
def predict_signal(signal):
    """Analyse le signal ECG et retourne la prédiction"""
    try:
        # Normalisation du signal (votre code existant)
        signal_array = np.array(signal, dtype=np.float32)
        signal_std = signal_array.std()
        
        if signal_std < 1e-8:
            signal_norm = signal_array - signal_array.mean()
        else:
            signal_norm = (signal_array - signal_array.mean()) / signal_std
        
        # Prédiction avec le modèle IA
        x = signal_norm.reshape(1, 187, 1)
        pred = model.predict(x, verbose=0)[0]
        class_id = int(np.argmax(pred))
        confidence = float(np.max(pred))
        class_name = CLASS_LABELS.get(class_id, f"Unknown Class {class_id}")
        
        # NOUVEAU: Déterminer le niveau de criticité
        status = CRITICALITY_MAP.get(class_id, "normal")
        alert = (class_id != 0) and (confidence > 0.7)
        
        return class_id, class_name, confidence, alert, status
        
    except Exception as e:
        print(f"❌ Erreur prédiction: {e}")
        return 0, "Error", 0.0, False, "normal"


# ═══════════════════════════════════════════════════════════════════════════
# ROUTE PRINCIPALE /predict - AVEC COOPÉRATION
# ═══════════════════════════════════════════════════════════════════════════
@app.route("/predict", methods=["POST"])
def predict():
    """
    Cette fonction est appelée quand un patient arrive
    Elle analyse le signal ECG et COOPÈRE avec les autres fogs
    """
    try:
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 1: RECEVOIR LES DONNÉES DU PATIENT
        # ───────────────────────────────────────────────────────────────────
        data = request.json
        patient_id = data.get("patient_id", "unknown")
        signal = data.get("signal")  # Signal ECG (187 points)
        
        if not signal or len(signal) != 187:
            return jsonify({"error": "Signal invalide"}), 400
        
        print(f"\n{'='*70}")
        print(f"🔍 [{FOG_NODE_ID}] 🚨 SOINS INTENSIFS - Patient {patient_id}")
        print(f"    Signal reçu: {len(signal)} points")
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 2: ANALYSER LE SIGNAL AVEC L'IA
        # ───────────────────────────────────────────────────────────────────
        class_id, class_name, confidence, alert, status = predict_signal(signal)
        
        print(f"    Résultat IA: {class_name} (confidence: {confidence:.2%})")
        print(f"    Niveau: {status.upper()}")
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 3: ENRICHIR LES DONNÉES AVEC LE STATUS
        # ───────────────────────────────────────────────────────────────────
        # EXPLICATION:
        # On ajoute le "status" aux données du patient pour que les autres
        # fogs sachent si c'est grave ou pas
        enriched_data = data.copy()
        enriched_data['status'] = status
        enriched_data['prediction_class'] = class_id
        enriched_data['confidence'] = confidence
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 4: VÉRIFIER SI JE SUIS LE BON FOG POUR CE CAS
        # ───────────────────────────────────────────────────────────────────
        # EXPLICATION COOPÉRATION #1: ROUTING INTELLIGENT
        # 
        # fog_coop.get_node_by_specialty(enriched_data) regarde le "status"
        # et décide quel fog est le MEILLEUR pour ce patient:
        #
        # - status = "critical"  → FOG-002 (MOI, Critical Care)
        # - status = "warning"   → FOG-001 (General)
        # - status = "normal"    → FOG-003 (Pediatric)
        #
        # Cette fonction retourne quelque chose comme:
        # {"id": "FOG-002", "url": "http://localhost:5002", "specialty": "critical_care"}
        
        optimal_node = fog_coop.get_node_by_specialty(enriched_data)
        print(f"    Fog optimal pour ce cas: {optimal_node['id']} ({optimal_node['specialty']})")
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 5: DÉLÉGUER SI NÉCESSAIRE
        # ───────────────────────────────────────────────────────────────────
        # EXPLICATION COOPÉRATION #2: DÉLÉGATION
        #
        # Si optimal_node['id'] != "FOG-002", ça veut dire qu'un AUTRE fog
        # est plus qualifié pour traiter ce patient
        #
        # EXEMPLE:
        # - Si j'ai reçu un patient "normal" (pas ma spécialité)
        # - Je vais demander à FOG-003 (spécialiste du suivi normal) de le traiter
        # - C'est comme un médecin urgentiste qui transfère un patient stable
        #   vers un médecin généraliste
        
        if optimal_node['id'] != FOG_NODE_ID and status == 'normal':
            print(f"🔀 Patient {status} - Pas ma spécialité")
            print(f"    Délégation vers {optimal_node['id']}...")
            
            # COOPÉRATION: Envoyer la requête à l'autre fog
            # Cette fonction fait un POST vers l'URL de l'autre fog
            # Exemple: POST http://localhost:5003/predict
            delegated_result = fog_coop.request_analysis_from_peer(
                enriched_data,
                optimal_node['specialty']
            )
            
            if delegated_result:
                print(f"✅ Patient transféré avec succès vers {optimal_node['id']}")
                # Retourner le résultat de l'autre fog
                return jsonify(delegated_result), 200
            else:
                print(f"⚠️ Transfert échoué, je traite quand même")
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 6: TRAITEMENT LOCAL (JE SUIS LE BON FOG)
        # ───────────────────────────────────────────────────────────────────
        # Si on arrive ici, c'est que:
        # - SOIT je suis le fog optimal (cas critique = ma spécialité)
        # - SOIT la délégation a échoué et je dois traiter quand même
        
        print(f"🏥 [{FOG_NODE_ID}] 🚨 TRAITEMENT LOCAL")
        print(f"    Type: {class_name}")
        print(f"    Confiance: {confidence:.2%}")
        print(f"    Alerte: {'OUI' if alert else 'NON'}")
        
        # Préparer le résultat de l'analyse
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
            "priority": "CRITICAL" if status == "critical" else "NORMAL",
            "fog_processing_time": datetime.now().isoformat()
        }
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 7: PARTAGER L'ALERTE SI C'EST CRITIQUE
        # ───────────────────────────────────────────────────────────────────
        # EXPLICATION COOPÉRATION #3: PARTAGE D'ALERTES
        #
        # Si le patient est en état CRITIQUE, je dois PRÉVENIR tous les autres fogs !
        # C'est comme sonner l'alarme dans tout l'hôpital
        #
        # COMMENT ÇA MARCHE:
        # 1. Je crée un message d'alerte avec les infos importantes
        # 2. fog_coop.share_alert() envoie ce message à FOG-001 et FOG-003
        # 3. Ces fogs reçoivent l'alerte via leur route /alerts/share
        # 4. Maintenant TOUS les fogs savent qu'il y a une urgence
        
        if status == 'critical' and confidence > 0.7:
            print(f"\n🚨🚨 URGENCE MÉDICALE DÉTECTÉE 🚨🚨")
            
            # Créer le message d'alerte
            alert_data = {
                'alert_id': f"CRITICAL-{patient_id}-{int(time.time())}",
                'patient_id': patient_id,
                'severity': 'critical',
                'class_name': class_name,
                'confidence': confidence,
                'message': f"⚠️ URGENCE: {class_name} détecté en soins intensifs"
            }
            
            # COOPÉRATION: Partager avec TOUS les autres fogs
            # Cette fonction fait:
            # - POST http://localhost:5001/alerts/share (vers FOG-001)
            # - POST http://localhost:5003/alerts/share (vers FOG-003)
            shared_count = fog_coop.share_alert(alert_data)
            
            print(f"📢 Alerte envoyée à {shared_count} fogs (FOG-001 et FOG-003)")
            print(f"    Tous les fogs sont maintenant au courant !")
            
            analysis_result['alert_shared'] = True
            analysis_result['alert_recipients'] = shared_count
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 8: SYNCHRONISER LES DONNÉES PATIENT
        # ───────────────────────────────────────────────────────────────────
        # EXPLICATION COOPÉRATION #4: SYNCHRONISATION
        #
        # Après avoir analysé le patient, je partage mon résultat avec
        # tous les autres fogs. Comme ça, si ce patient revient plus tard
        # vers FOG-001 ou FOG-003, ils auront son HISTORIQUE MÉDICAL !
        #
        # C'est comme mettre à jour le dossier médical partagé du patient
        #
        # COMMENT ÇA MARCHE:
        # 1. fog_coop.sync_patient_data() envoie mon analyse à tous les fogs
        # 2. Les autres fogs reçoivent via leur route /sync/patient
        # 3. Ils stockent l'info localement pour référence future
        
        print(f"\n🔄 SYNCHRONISATION DES DONNÉES")
        synced_fogs = fog_coop.sync_patient_data(patient_id, analysis_result)
        print(f"    Données envoyées à: {synced_fogs}")
        print(f"    Les autres fogs ont maintenant l'historique de {patient_id}")
        
        analysis_result['synced_with'] = synced_fogs
        
        # ───────────────────────────────────────────────────────────────────
        # ÉTAPE 9: ENVOYER AU CLOUD (COMME AVANT)
        # ───────────────────────────────────────────────────────────────────
        cloud_status = "N/A"
        try:
            r = requests.post(CLOUD_API_URL, json=analysis_result, timeout=5)
            cloud_status = r.status_code
            print(f"\n☁️ Envoyé au Cloud: {cloud_status}")
        except Exception as e:
            cloud_status = f"Erreur: {str(e)}"
            print(f"❌ Erreur Cloud: {e}")
        
        analysis_result['cloud_status'] = cloud_status
        
        print(f"{'='*70}\n")
        
        # Retourner le résultat
        return jsonify(analysis_result), 200
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES DE COOPÉRATION - POUR RECEVOIR DES MESSAGES DES AUTRES FOGS
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/alerts/share", methods=["POST"])
def receive_alert():
    """
    Cette route est appelée quand UN AUTRE FOG m'envoie une alerte
    
    EXEMPLE CONCRET:
    - FOG-001 détecte un cas critique
    - FOG-001 appelle fog_coop.share_alert()
    - fog_coop fait: POST http://localhost:5002/alerts/share (vers MOI)
    - Cette fonction receive_alert() reçoit le message
    - J'affiche l'alerte pour que mon équipe soit au courant
    """
    try:
        # Recevoir le message d'alerte
        alert_data = request.json
        
        # Stocker l'alerte localement (dans fog_coop)
        fog_coop.receive_shared_alert(alert_data)
        
        # Extraire les informations importantes
        source_fog = alert_data.get('source_fog', 'unknown')
        patient_id = alert_data.get('patient_id', 'unknown')
        message = alert_data.get('message', '')
        severity = alert_data.get('severity', 'unknown')
        
        # Afficher l'alerte dans mes logs
        print(f"\n{'='*70}")
        print(f"📢 [{FOG_NODE_ID}] ALERTE REÇUE !")
        print(f"    De: {source_fog}")
        print(f"    Patient: {patient_id}")
        print(f"    Gravité: {severity}")
        print(f"    Message: {message}")
        print(f"    >>> Mon équipe soins intensifs est maintenant alertée")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "alert_received", "fog_node": FOG_NODE_ID}), 200
        
    except Exception as e:
        print(f"❌ Erreur réception alerte: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/sync/patient", methods=["POST"])
def sync_patient():
    """
    Cette route est appelée quand UN AUTRE FOG partage des données patient
    
    EXEMPLE CONCRET:
    - FOG-003 analyse le patient P123
    - FOG-003 appelle fog_coop.sync_patient_data()
    - fog_coop fait: POST http://localhost:5002/sync/patient (vers MOI)
    - Cette fonction reçoit les données
    - Je stocke l'historique du patient P123 localement
    """
    try:
        sync_data = request.json
        patient_id = sync_data.get('patient_id', 'unknown')
        source_fog = sync_data.get('source_fog', 'unknown')
        
        print(f"🔄 [{FOG_NODE_ID}] Sync patient {patient_id} reçue de {source_fog}")
        print(f"    J'ai maintenant l'historique médical de {patient_id}")
        
        # ICI: Vous pouvez stocker les données dans une base de données
        # ou un dictionnaire Python pour référence future
        # Exemple: patient_history[patient_id] = sync_data
        
        return jsonify({"status": "synced", "fog_node": FOG_NODE_ID}), 200
        
    except Exception as e:
        print(f"❌ Erreur sync: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/events/critical", methods=["POST"])
def receive_critical_event():
    """
    Pour recevoir des événements système critiques
    (Exemple: panne d'un fog, alerte de sécurité, etc.)
    """
    try:
        event_data = request.json
        
        print(f"\n{'='*70}")
        print(f"🚨 [{FOG_NODE_ID}] ÉVÉNEMENT SYSTÈME CRITIQUE")
        print(f"    Source: {event_data.get('source_fog')}")
        print(f"    Type: {event_data.get('event_type')}")
        print(f"    Message: {event_data.get('message')}")
        print(f"{'='*70}\n")
        
        return jsonify({"status": "event_received"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/cooperation/status", methods=["GET"])
def cooperation_status():
    """
    Pour vérifier l'état de la coopération
    Utile pour le monitoring et le debug
    """
    try:
        # Vérifier si les autres fogs sont en ligne
        health_status = fog_coop.get_system_health()
        
        # Récupérer les alertes que j'ai reçues
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


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES STANDARD (health, info)
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    """Health check standard"""
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
    """Informations sur ce fog node"""
    return jsonify({
        "fog_node_id": FOG_NODE_ID,
        "port": FOG_PORT,
        "specialty": FOG_SPECIALTY,
        "model": "ecg_cnn.h5",
        "status": "active",
        "cooperation": "enabled",
        "connected_fogs": len(DEFAULT_FOG_NODES) - 1
    }), 200


# ═══════════════════════════════════════════════════════════════════════════
# DÉMARRAGE DU SERVEUR
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "="*70)
    print(f"🌫️  [{FOG_NODE_ID}] 🚨 FOG NODE SOINS INTENSIFS - Démarrage")
    print("="*70)
    print(f"Port: {FOG_PORT}")
    print(f"Spécialité: {FOG_SPECIALTY.upper()} (Cas critiques)")
    print(f"Modèle: {MODEL_PATH}")
    print(f"Coopération: Activée avec {len(DEFAULT_FOG_NODES)-1} autres fogs")
    print("="*70 + "\n")
    
    app.run(host="0.0.0.0", port=FOG_PORT, debug=False, threaded=True)