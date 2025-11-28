import requests
import numpy as np
import time
from datetime import datetime

# URL du Fog Node
FOG_URL = "http://localhost:5000/predict"

def generate_simulated_ecg(signal_type="normal"):
    """
    Génère un signal ECG simulé de 187 points
    
    Args:
        signal_type: "normal", "abnormal", ou "random"
    
    Returns:
        Liste de 187 valeurs
    """
    if signal_type == "normal":
        # Signal ECG normal simulé (sinusoïde + bruit)
        t = np.linspace(0, 4*np.pi, 187)
        signal = np.sin(t) + 0.1 * np.random.randn(187)
    elif signal_type == "abnormal":
        # Signal anormal (amplitudes élevées)
        t = np.linspace(0, 4*np.pi, 187)
        signal = 2 * np.sin(t) + 0.5 * np.random.randn(187)
    else:
        # Signal aléatoire
        signal = np.random.randn(187)
    
    return signal.tolist()

def send_single_signal(patient_id, signal_type="random"):
    """
    Envoie un signal ECG au Fog Node
    """
    signal = generate_simulated_ecg(signal_type)
    
    payload = {
        "patient_id": patient_id,
        "timestamp": datetime.now().isoformat(),
        "signal": signal
    }
    
    try:
        print(f"\n📤 Envoi du signal pour {patient_id} (type: {signal_type})...")
        response = requests.post(FOG_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Réponse reçue:")
            print(f"  Patient ID:    {result.get('patient_id')}")
            print(f"  Classe:        {result.get('class_name')} (ID: {result.get('class_id')})")
            print(f"  Confiance:     {result.get('confidence', 0):.2%}")
            print(f"  Alerte:        {'🚨 OUI' if result.get('alert') else 'Non'}")
            print(f"  Cloud Status:  {result.get('cloud_status')}")
            return result
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            print(f"   Message: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: Impossible de se connecter au Fog Node")
        print("   Vérifiez que fog_node.py est en cours d'exécution")
        return None
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def send_multiple_signals(count=5, delay=2):
    """
    Envoie plusieurs signaux avec un délai entre chacun
    """
    print("\n" + "="*60)
    print(f"📡 Envoi de {count} signaux ECG simulés")
    print("="*60)
    
    signal_types = ["normal", "abnormal", "random"]
    results = []
    
    for i in range(count):
        patient_id = f"P{str(i+1).zfill(3)}"
        signal_type = signal_types[i % len(signal_types)]
        
        result = send_single_signal(patient_id, signal_type)
        if result:
            results.append(result)
        
        if i < count - 1:
            print(f"\n⏳ Attente de {delay} secondes...")
            time.sleep(delay)
    
    print("\n" + "="*60)
    print(f"✓ Envoi terminé: {len(results)}/{count} réussis")
    print("="*60)
    
    return results

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("📡 CLIENT IoT - Simulateur de signaux ECG")
    print("="*60)
    
    # Mode d'utilisation
    if len(sys.argv) > 1:
        if sys.argv[1] == "single":
            # Envoyer un seul signal
            patient_id = sys.argv[2] if len(sys.argv) > 2 else "P001"
            signal_type = sys.argv[3] if len(sys.argv) > 3 else "random"
            send_single_signal(patient_id, signal_type)
        elif sys.argv[1] == "multi":
            # Envoyer plusieurs signaux
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            delay = int(sys.argv[3]) if len(sys.argv) > 3 else 2
            send_multiple_signals(count, delay)
        else:
            print("Usage:")
            print("  python send_signal.py single [patient_id] [signal_type]")
            print("  python send_signal.py multi [count] [delay]")
            print("\nSignal types: normal, abnormal, random")
    else:
        # Par défaut: envoyer un signal aléatoire
        send_single_signal("P001", "random")