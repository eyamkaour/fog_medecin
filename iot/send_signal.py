import requests
import numpy as np
import time
from datetime import datetime

# URL du Fog Node
FOG_URL = "http://localhost:5000/predict"

def generate_simulated_ecg(signal_type="normal"):
    """
    Génère un signal ECG simulé de 187 points.
    """
    if signal_type == "normal":
        t = np.linspace(0, 4*np.pi, 187)
        signal = np.sin(t) + 0.1 * np.random.randn(187)

    elif signal_type == "dangerous":
        # ⚠️ Signal extrêmement anormal pour déclencher une alerte
        t = np.linspace(0, 4*np.pi, 187)
        signal = 5 * np.sin(t) + 2 * np.random.randn(187)
        # Pics dangereux (simule fibrillation / tachycardie sévère)
        signal[50] = 10
        signal[120] = -12
        signal[160] = 15

    else:
        signal = np.random.randn(187)

    return signal.tolist()

def send_signal(patient_id, signal_type):
    """
    Envoie un signal ECG au Fog Node.
    """
    signal = generate_simulated_ecg(signal_type)

    payload = {
        "patient_id": patient_id,
        "timestamp": datetime.now().isoformat(),
        "signal": signal
    }

    try:
        print(f"\n📤 Envoi du signal de {patient_id} (type: {signal_type})...")
        response = requests.post(FOG_URL, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Réponse Fog Node :")
            print(f"  Patient ID:    {result.get('patient_id')}")
            print(f"  Classe:        {result.get('class_name')} (ID: {result.get('class_id')})")
            print(f"  Confiance:     {result.get('confidence', 0):.2%}")
            print(f"  Alerte:        {'🚨 OUI' if result.get('alert') else 'Non'}")
            print(f"  Cloud Status:  {result.get('cloud_status')}")
            return result
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        return None

def test_multiple_patients():
    """
    Test avec multiples signaux pour les mêmes patients
    """
    print("\n" + "="*60)
    print("📡 TEST HISTORIQUE - Signaux Multiples")
    print("="*60)

    # Patient P003 - 5 signaux normaux
    print("\n--- 🩺 Patient P003 (5 Signaux Normaux) ---")
    for i in range(2):
        print(f"Envoi {i+1}/2...")
        result = send_signal("P003", "normal")
        time.sleep(2)
    send_signal("P003", "dangerous")
    send_signal("P003", "warning")
    # Patient P002 - 3 signaux dangereux  
    print("\n--- ⚠️ Patient P004 (3 Signaux Dangereux) ---")
    for i in range(3):
        print(f"Envoi {i+1}/3...")
        result = send_signal("P004", "dangerous")
        time.sleep(2)

def send_P001_normal():
    """
    Patient P003 envoie un signal normal.
    """
    return send_signal("P003", "normal")

def send_P002_dangerous():
    """
    Patient P002 envoie un signal très dangereux.
    """
    return send_signal("P004", "dangerous")

if __name__ == "__main__":
    # Test avec multiples signaux pour l'historique
    test_multiple_patients()