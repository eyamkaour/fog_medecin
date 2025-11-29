"""
═══════════════════════════════════════════════════════════════════════════
SIMULATEUR IoT MÉDICAL - ECG SIGNAL SENDER
═══════════════════════════════════════════════════════════════════════════
Ce simulateur envoie des signaux ECG réalistes pour tester:
✅ Les 3 Fog Nodes (FOG-001, FOG-002, FOG-003)
✅ Toutes les spécialités (general, critical_care, pediatric)
✅ Load Balancer avec routing intelligent
✅ Coopération entre fogs (alertes, sync, délégation)
✅ Cloud Firebase storage
✅ Dashboard temps réel

Lancement: python iot_simulator.py
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import numpy as np
import time
import random
from datetime import datetime
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# URL du Load Balancer (qui route vers les fogs)
LOAD_BALANCER_URL = "http://localhost:5000/predict"

# Ou envoyer directement à un fog spécifique:
FOG_URLS = {
    "FOG-001": "http://localhost:5001/predict",  # General
    "FOG-002": "http://localhost:5002/predict",  # Critical Care
    "FOG-003": "http://localhost:5003/predict"   # Pediatric
}

# Configuration patients
PATIENTS = [
    {"id": "P001", "name": "Alice Martin", "age": 35, "condition": "normal"},
    {"id": "P002", "name": "Bob Dupont", "age": 58, "condition": "warning"},
    {"id": "P003", "name": "Charlie Bernard", "age": 72, "condition": "critical"},
    {"id": "P004", "name": "Diana Petit", "age": 8, "condition": "pediatric"},
    {"id": "P005", "name": "Eva Moreau", "age": 45, "condition": "normal"}
]

# ═══════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE SIGNAUX ECG RÉALISTES
# ═══════════════════════════════════════════════════════════════════════════

def generate_ecg_signal(signal_type="normal", length=187):
    """
    Génère un signal ECG réaliste
    
    Args:
        signal_type: "normal", "supraventricular", "ventricular"
        length: Longueur du signal (187 points par défaut)
    
    Returns:
        Liste de 187 valeurs simulant un ECG
    """
    t = np.linspace(0, 1, length)
    
    if signal_type == "normal":
        # Rythme cardiaque normal (classe 0)
        # Onde P + complexe QRS + onde T
        signal = (
            0.3 * np.sin(2 * np.pi * 1.2 * t) +  # Onde P
            1.5 * np.sin(2 * np.pi * 2.5 * t) +  # Complexe QRS
            0.4 * np.sin(2 * np.pi * 0.8 * t) +  # Onde T
            0.05 * np.random.randn(length)        # Bruit
        )
        
    elif signal_type == "supraventricular":
        # Arythmie supraventriculaire (classe 1)
        # Fréquence plus rapide, onde P anormale
        signal = (
            0.5 * np.sin(2 * np.pi * 3.5 * t) +   # Onde P rapide
            1.2 * np.sin(2 * np.pi * 4.0 * t) +   # QRS
            0.3 * np.sin(2 * np.pi * 1.5 * t) +   # Onde T
            0.08 * np.random.randn(length)
        )
        
    elif signal_type == "ventricular":
        # Arythmie ventriculaire (classe 2) - CRITIQUE !
        # Complexe QRS large et anormal
        signal = (
            1.8 * np.sin(2 * np.pi * 2.0 * t) +   # QRS large
            0.8 * np.sin(2 * np.pi * 1.0 * t) +   # Onde anormale
            0.4 * np.random.randn(length) +       # Bruit élevé
            0.5 * np.sin(2 * np.pi * 5.5 * t)     # Composante irrégulière
        )
    
    return signal.tolist()


# ═══════════════════════════════════════════════════════════════════════════
# FONCTION D'ENVOI AU FOG
# ═══════════════════════════════════════════════════════════════════════════

def send_to_fog(patient, signal_type, use_load_balancer=True, target_fog=None):
    """
    Envoie un signal ECG au Fog Node
    
    Args:
        patient: Dictionnaire patient
        signal_type: Type de signal à générer
        use_load_balancer: Si True, utilise le load balancer, sinon fog direct
        target_fog: FOG spécifique (FOG-001, FOG-002, FOG-003) si pas de LB
    
    Returns:
        Réponse du fog node
    """
    # Générer le signal
    signal = generate_ecg_signal(signal_type)
    
    # Déterminer la criticité pour le routing
    status_map = {
        "normal": "normal",
        "supraventricular": "warning",
        "ventricular": "critical"
    }
    
    # Préparer les données
    data = {
        "patient_id": patient["id"],
        "patient_name": patient["name"],
        "signal": signal,
        "timestamp": datetime.now().isoformat(),
        "status": status_map.get(signal_type, "normal"),
        "heart_rate": random.randint(60, 140)
    }
    
    # Choisir l'URL
    if use_load_balancer:
        url = LOAD_BALANCER_URL
        target = "Load Balancer"
    else:
        url = FOG_URLS.get(target_fog, FOG_URLS["FOG-001"])
        target = target_fog
    
    # Envoyer
    try:
        start_time = time.time()
        response = requests.post(url, json=data, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "patient": patient["id"],
                "signal_type": signal_type,
                "target": target,
                "fog_processed": result.get("fog_node_id", "Unknown"),
                "prediction": result.get("class_name", "Unknown"),
                "confidence": result.get("confidence", 0),
                "alert": result.get("alert", False),
                "response_time": round(response_time, 3),
                "full_response": result
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "patient": patient["id"]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "patient": patient["id"]
        }


# ═══════════════════════════════════════════════════════════════════════════
# SCÉNARIOS DE TEST
# ═══════════════════════════════════════════════════════════════════════════

def scenario_1_test_load_balancer():
    """
    SCÉNARIO 1: Test du Load Balancer avec routing intelligent
    Envoie différents types de signaux et observe le routing
    """
    print("\n" + "="*80)
    print("📊 SCÉNARIO 1: TEST LOAD BALANCER - Routing Intelligent")
    print("="*80)
    
    test_cases = [
        (PATIENTS[0], "normal", "Devrait aller vers FOG-003 (pediatric)"),
        (PATIENTS[1], "supraventricular", "Devrait aller vers FOG-001 (general)"),
        (PATIENTS[2], "ventricular", "Devrait aller vers FOG-002 (critical_care)"),
        (PATIENTS[3], "normal", "Devrait aller vers FOG-003 (pediatric)"),
        (PATIENTS[4], "ventricular", "Devrait aller vers FOG-002 (critical_care)")
    ]
    
    for i, (patient, signal_type, expected) in enumerate(test_cases, 1):
        print(f"\n🔬 Test {i}/5: Patient {patient['id']} - Signal {signal_type}")
        print(f"   Attente: {expected}")
        
        result = send_to_fog(patient, signal_type, use_load_balancer=True)
        
        if result["success"]:
            print(f"   ✅ Routé vers: {result['fog_processed']}")
            print(f"   📋 Prédiction: {result['prediction']} ({result['confidence']:.2%})")
            print(f"   ⚡ Temps: {result['response_time']}s")
            if result["alert"]:
                print(f"   🚨 ALERTE GÉNÉRÉE!")
        else:
            print(f"   ❌ Erreur: {result['error']}")
        
        time.sleep(1)


def scenario_2_test_cooperation():
    """
    SCÉNARIO 2: Test de la coopération entre fogs
    Envoie des signaux critiques pour tester le partage d'alertes
    """
    print("\n" + "="*80)
    print("🤝 SCÉNARIO 2: TEST COOPÉRATION - Partage d'Alertes & Sync")
    print("="*80)
    
    # Cas critique qui devrait déclencher une alerte partagée
    critical_patients = [PATIENTS[2], PATIENTS[1]]
    
    for patient in critical_patients:
        print(f"\n🚨 Envoi cas CRITIQUE: Patient {patient['id']}")
        
        result = send_to_fog(patient, "ventricular", use_load_balancer=True)
        
        if result["success"]:
            print(f"   ✅ Traité par: {result['fog_processed']}")
            print(f"   📋 {result['prediction']} (conf: {result['confidence']:.2%})")
            
            if "alert_shared" in result["full_response"]:
                shared_count = result["full_response"].get("alert_recipients", 0)
                print(f"   📢 Alerte partagée avec {shared_count} autres fogs")
            
            if "synced_with" in result["full_response"]:
                synced = result["full_response"]["synced_with"]
                print(f"   🔄 Données synchronisées avec: {synced}")
        
        time.sleep(2)


def scenario_3_test_direct_fog():
    """
    SCÉNARIO 3: Test direct de chaque fog node
    Envoie à chaque fog individuellement pour tester toutes les méthodes
    """
    print("\n" + "="*80)
    print("🎯 SCÉNARIO 3: TEST DIRECT - Chaque Fog Individuellement")
    print("="*80)
    
    for fog_id in ["FOG-001", "FOG-002", "FOG-003"]:
        print(f"\n🌫️  Test de {fog_id}")
        print("-" * 40)
        
        # Test avec différents types de signaux
        for signal_type in ["normal", "supraventricular", "ventricular"]:
            patient = random.choice(PATIENTS)
            print(f"  📡 Envoi signal {signal_type} de {patient['id']}")
            
            result = send_to_fog(
                patient, 
                signal_type, 
                use_load_balancer=False, 
                target_fog=fog_id
            )
            
            if result["success"]:
                print(f"     ✅ {result['prediction']} ({result['confidence']:.2%})")
            else:
                print(f"     ❌ {result['error']}")
            
            time.sleep(0.5)


def scenario_4_load_test():
    """
    SCÉNARIO 4: Test de charge
    Envoie beaucoup de requêtes simultanées
    """
    print("\n" + "="*80)
    print("⚡ SCÉNARIO 4: TEST DE CHARGE - 20 Requêtes Rapides")
    print("="*80)
    
    results = []
    
    for i in range(20):
        patient = random.choice(PATIENTS)
        signal_type = random.choice(["normal", "supraventricular", "ventricular"])
        
        print(f"\r📤 Envoi {i+1}/20...", end="", flush=True)
        
        result = send_to_fog(patient, signal_type, use_load_balancer=True)
        results.append(result)
        
        time.sleep(0.2)  # Petite pause entre envois
    
    # Statistiques
    print("\n\n📊 STATISTIQUES:")
    successful = [r for r in results if r["success"]]
    
    print(f"   Total envoyé: 20")
    print(f"   Réussis: {len(successful)}")
    print(f"   Échoués: {20 - len(successful)}")
    
    if successful:
        avg_time = sum(r["response_time"] for r in successful) / len(successful)
        print(f"   Temps moyen: {avg_time:.3f}s")
        
        # Distribution par fog
        fog_counts = {}
        for r in successful:
            fog = r["fog_processed"]
            fog_counts[fog] = fog_counts.get(fog, 0) + 1
        
        print(f"\n   Distribution par Fog:")
        for fog, count in fog_counts.items():
            percentage = (count / len(successful)) * 100
            print(f"     {fog}: {count} requêtes ({percentage:.1f}%)")


def scenario_5_mixed_test():
    """
    SCÉNARIO 5: Test mixte réaliste
    Simule un flux continu de patients avec conditions variées
    """
    print("\n" + "="*80)
    print("🏥 SCÉNARIO 5: SIMULATION RÉALISTE - Flux Continu")
    print("="*80)
    print("Durée: 30 secondes | Simulation vie réelle\n")
    
    start_time = time.time()
    count = 0
    
    while (time.time() - start_time) < 30:
        count += 1
        patient = random.choice(PATIENTS)
        
        # Distribution réaliste: 70% normal, 20% warning, 10% critical
        rand = random.random()
        if rand < 0.7:
            signal_type = "normal"
        elif rand < 0.9:
            signal_type = "supraventricular"
        else:
            signal_type = "ventricular"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 #{count} | "
              f"{patient['id']} | {signal_type:20s}", end=" ")
        
        result = send_to_fog(patient, signal_type, use_load_balancer=True)
        
        if result["success"]:
            icon = "🚨" if result["alert"] else "✅"
            print(f"{icon} {result['fog_processed']} | {result['prediction']}")
        else:
            print(f"❌ Erreur")
        
        time.sleep(random.uniform(1, 3))  # Intervalle réaliste
    
    print(f"\n✅ Simulation terminée: {count} signaux envoyés en 30s")


# ═══════════════════════════════════════════════════════════════════════════
# MENU INTERACTIF
# ═══════════════════════════════════════════════════════════════════════════

def show_menu():
    """Affiche le menu principal"""
    print("\n" + "="*80)
    print("🏥 SIMULATEUR IoT MÉDICAL - ECG SIGNAL SENDER")
    print("="*80)
    print("\nChoisissez un scénario de test:\n")
    print("  1️⃣  Test Load Balancer (Routing Intelligent)")
    print("  2️⃣  Test Coopération (Alertes & Synchronisation)")
    print("  3️⃣  Test Direct (Chaque Fog Individuellement)")
    print("  4️⃣  Test de Charge (20 requêtes rapides)")
    print("  5️⃣  Simulation Réaliste (30 secondes continu)")
    print("  6️⃣  TOUT TESTER (Tous les scénarios)")
    print("  0️⃣  Quitter")
    print("\n" + "="*80)


def main():
    """Programme principal"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          🏥 SIMULATEUR IoT MÉDICAL - ECG SENDER 🏥           ║
    ║                                                               ║
    ║  Architecture: IoT → Load Balancer → Fog Nodes → Cloud       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Vérifier que les services sont en ligne
    print("\n🔍 Vérification des services...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Load Balancer: En ligne")
        else:
            print("   ⚠️  Load Balancer: Réponse anormale")
    except:
        print("   ❌ Load Balancer: HORS LIGNE!")
        print("   💡 Lancez: python load_balancer.py")
        return
    
    # Vérifier les fogs
    for fog_id, url in FOG_URLS.items():
        try:
            response = requests.get(url.replace("/predict", "/health"), timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {fog_id}: En ligne")
            else:
                print(f"   ⚠️  {fog_id}: Réponse anormale")
        except:
            print(f"   ❌ {fog_id}: HORS LIGNE!")
    
    # Menu principal
    while True:
        show_menu()
        
        try:
            choice = input("\n👉 Votre choix: ").strip()
            
            if choice == "1":
                scenario_1_test_load_balancer()
            elif choice == "2":
                scenario_2_test_cooperation()
            elif choice == "3":
                scenario_3_test_direct_fog()
            elif choice == "4":
                scenario_4_load_test()
            elif choice == "5":
                scenario_5_mixed_test()
            elif choice == "6":
                print("\n🚀 Exécution de TOUS les scénarios...\n")
                scenario_1_test_load_balancer()
                time.sleep(2)
                scenario_2_test_cooperation()
                time.sleep(2)
                scenario_3_test_direct_fog()
                time.sleep(2)
                scenario_4_load_test()
                time.sleep(2)
                scenario_5_mixed_test()
                print("\n\n✅ TOUS LES TESTS TERMINÉS!")
            elif choice == "0":
                print("\n👋 Au revoir!\n")
                break
            else:
                print("\n❌ Choix invalide!")
            
            input("\n⏸️  Appuyez sur Entrée pour continuer...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interruption - Au revoir!\n")
            break


if __name__ == "__main__":
    main()