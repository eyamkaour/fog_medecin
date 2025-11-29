"""
SIMULATEUR IoT - Envoi de signaux ECG vers le Load Balancer
Génère des données patient réalistes avec différents patterns pathologiques
"""

import requests
import json
import time
import random
import numpy as np
from datetime import datetime
import threading
from collections import deque
import argparse

# Configuration
LOAD_BALANCER_URL = "http://localhost:5000/predict"
HEALTH_CHECK_URL = "http://localhost:5000/health"

class ECGSignalGenerator:
    """Générateur de signaux ECG réalistes avec différentes pathologies"""
    
    def __init__(self):
        # Patterns ECG pré-enregistrés pour différentes conditions
        self.patterns = {
            'normal': self._generate_normal_ecg(),
            'supraventricular': self._generate_supraventricular_ecg(),
            'ventricular': self._generate_ventricular_ecg()
        }
        
        # Patients simulés avec profils médicaux
        self.patients = [
            {"id": "PAT-001", "name": "Jean Dupont", "age": 45, "risk_factor": "low"},
            {"id": "PAT-002", "name": "Marie Martin", "age": 68, "risk_factor": "high"},
            {"id": "PAT-003", "name": "Pierre Leroy", "age": 32, "risk_factor": "medium"},
            {"id": "PAT-004", "name": "Sophie Bernard", "age": 55, "risk_factor": "high"},
            {"id": "PAT-005", "name": "Luc Moreau", "age": 29, "risk_factor": "low"}
        ]
        
        self.sent_signals = 0
        self.failed_signals = 0
        
    def _generate_normal_ecg(self):
        """Génère un signal ECG normal"""
        t = np.linspace(0, 1, 187)
        # Pattern ECG normal avec onde P, complexe QRS, onde T
        signal = (
            0.5 * np.sin(2 * np.pi * 5 * t) +  # Rythme de base
            1.0 * np.exp(-((t-0.2)/0.05)**2) +  # Onde P
            2.0 * np.exp(-((t-0.4)/0.03)**2) -  # Complexe QRS
            0.8 * np.exp(-((t-0.6)/0.07)**2)    # Onde T
        )
        return signal.tolist()
    
    def _generate_supraventricular_ecg(self):
        """Génère un signal avec arythmie supraventriculaire"""
        t = np.linspace(0, 1, 187)
        # Pattern avec extrasystoles supraventriculaires
        signal = (
            0.5 * np.sin(2 * np.pi * 7 * t) +  # Rythme plus rapide
            1.2 * np.exp(-((t-0.15)/0.04)**2) +  # Onde P altérée
            1.8 * np.exp(-((t-0.35)/0.04)**2) -  # QRS étroit
            0.6 * np.exp(-((t-0.55)/0.06)**2) +  # Onde T
            0.9 * np.exp(-((t-0.8)/0.02)**2)     # Extrasystole
        )
        return signal.tolist()
    
    def _generate_ventricular_ecg(self):
        """Génère un signal avec arythmie ventriculaire"""
        t = np.linspace(0, 1, 187)
        # Pattern ventriculaire dangereux
        signal = (
            0.3 * np.sin(2 * np.pi * 3 * t) +   # Rythme irrégulier
            2.5 * np.exp(-((t-0.3)/0.08)**2) -  # QRS très large
            0.4 * np.exp(-((t-0.7)/0.1)**2) +   # Onde T inversée
            1.2 * np.exp(-((t-0.5)/0.05)**2)    # Complexe ventriculaire
        )
        return signal.tolist()
    
    def generate_signal(self, condition='normal', noise_level=0.1):
        """Génère un signal ECG avec bruit réaliste"""
        base_signal = self.patterns[condition]
        
        # Ajouter du bruit réaliste
        noise = np.random.normal(0, noise_level, len(base_signal))
        signal_with_noise = [base + noise_i for base, noise_i in zip(base_signal, noise)]
        
        return signal_with_noise
    
    def get_random_patient(self):
        """Retourne un patient aléatoire"""
        return random.choice(self.patients)
    
    def get_vital_signs(self, condition):
        """Génère des signes vitaux cohérents avec la condition"""
        if condition == 'normal':
            heart_rate = random.randint(60, 100)
            temperature = round(random.uniform(36.0, 37.2), 1)
            spo2 = random.randint(95, 100)
            blood_pressure = random.randint(110, 130)
            
        elif condition == 'supraventricular':
            heart_rate = random.randint(100, 140)
            temperature = round(random.uniform(36.5, 37.8), 1)
            spo2 = random.randint(90, 98)
            blood_pressure = random.randint(100, 120)
            
        else:  # ventricular
            heart_rate = random.randint(140, 180)
            temperature = round(random.uniform(37.0, 38.5), 1)
            spo2 = random.randint(85, 95)
            blood_pressure = random.randint(90, 110)
        
        return {
            'heart_rate': heart_rate,
            'temperature': temperature,
            'spo2': spo2,
            'blood_pressure': blood_pressure
        }

class IoTDeviceSimulator:
    """Simulateur de dispositif IoT médical"""
    
    def __init__(self, device_id, send_interval=5):
        self.device_id = device_id
        self.send_interval = send_interval
        self.ecg_generator = ECGSignalGenerator()
        self.running = False
        self.stats = {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'last_status': 'stopped'
        }
        
    def send_signal(self, condition_probabilities=None):
        """Envoie un signal ECG vers le load balancer"""
        
        if condition_probabilities is None:
            condition_probabilities = {'normal': 0.7, 'supraventricular': 0.2, 'ventricular': 0.1}
        
        # Choisir une condition selon les probabilités
        condition = random.choices(
            list(condition_probabilities.keys()),
            weights=list(condition_probabilities.values())
        )[0]
        
        # Générer les données
        patient = self.ecg_generator.get_random_patient()
        signal = self.ecg_generator.generate_signal(condition)
        vital_signs = self.ecg_generator.get_vital_signs(condition)
        
        # Préparer le payload
        payload = {
            "device_id": self.device_id,
            "patient_id": patient['id'],
            "patient_name": patient['name'],
            "signal": signal,
            "timestamp": datetime.now().isoformat(),
            "condition": condition,
            **vital_signs
        }
        
        try:
            # Envoyer vers le load balancer
            response = requests.post(
                LOAD_BALANCER_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            self.stats['total_sent'] += 1
            
            if response.status_code == 200:
                self.stats['successful'] += 1
                result = response.json()
                
                # Afficher le résultat avec couleur selon la criticité
                status_color = {
                    'normal': '🟢',
                    'warning': '🟡', 
                    'critical': '🔴'
                }.get(result.get('status', 'normal'), '⚪')
                
                print(f"{status_color} Signal envoyé | Patient: {patient['name']} | "
                      f"Condition: {condition.upper()} | "
                      f"Résultat: {result.get('class_name', 'N/A')} | "
                      f"Fog: {result.get('load_balancer_info', {}).get('fog_node', 'N/A')} | "
                      f"Temps: {result.get('load_balancer_info', {}).get('processing_time', 0):.3f}s")
                
                return True
            else:
                self.stats['failed'] += 1
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.stats['failed'] += 1
            print(f"❌ Erreur connexion: {str(e)}")
            return False
    
    def start_continuous_sending(self, condition_probabilities=None):
        """Démarre l'envoi continu de signaux"""
        self.running = True
        self.stats['last_status'] = 'running'
        
        print(f"\n🚀 Démarrage simulateur IoT {self.device_id}")
        print(f"📊 Intervale: {self.send_interval}s")
        print(f"🎯 Probabilités: {condition_probabilities}")
        print("=" * 80)
        
        while self.running:
            self.send_signal(condition_probabilities)
            time.sleep(self.send_interval)
    
    def stop(self):
        """Arrête l'envoi de signaux"""
        self.running = False
        self.stats['last_status'] = 'stopped'
        print(f"\n🛑 Simulateur {self.device_id} arrêté")

def check_system_health():
    """Vérifie la santé du système"""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"\n✅ Système opérationnel")
            print(f"   Load Balancer: {health_data.get('status', 'N/A')}")
            print(f"   Fog Nodes sains: {health_data.get('healthy_nodes', 0)}/{health_data.get('total_nodes', 0)}")
            
            # Afficher le statut des nodes
            for node_id, node_info in health_data.get('nodes', {}).items():
                status_icon = '🟢' if node_info.get('status') == 'healthy' else '🔴'
                print(f"   {status_icon} {node_id}: {node_info.get('status', 'unknown')} "
                      f"(connexions: {node_info.get('active_connections', 0)})")
            
            return True
        else:
            print(f"❌ Load balancer non healthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de contacter le load balancer: {str(e)}")
        return False

def interactive_mode():
    """Mode interactif pour envoyer des signaux manuellement"""
    generator = ECGSignalGenerator()
    simulator = IoTDeviceSimulator("INTERACTIVE-DEVICE")
    
    print("\n" + "="*60)
    print("🎮 MODE INTERACTIF - Simulateur ECG")
    print("="*60)
    
    conditions = {
        '1': ('normal', 'Rythme normal'),
        '2': ('supraventricular', 'Arythmie supraventriculaire'), 
        '3': ('ventricular', 'Arythmie ventriculaire CRITIQUE'),
        '4': ('random', 'Aléatoire (réaliste)')
    }
    
    while True:
        print("\nOptions:")
        for key, (cond, desc) in conditions.items():
            print(f"  {key}. {desc}")
        print("  s. Statut du système")
        print("  q. Quitter")
        
        choice = input("\nVotre choix: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 's':
            check_system_health()
        elif choice in conditions:
            condition = conditions[choice][0]
            if condition == 'random':
                # Probabilités réalistes
                probas = {'normal': 0.75, 'supraventricular': 0.2, 'ventricular': 0.05}
                simulator.send_signal(probas)
            else:
                simulator.send_signal({condition: 1.0})
        else:
            print("❌ Choix invalide")

def main():
    parser = argparse.ArgumentParser(description='Simulateur IoT pour signaux ECG')
    parser.add_argument('--mode', choices=['auto', 'interactive', 'single'], 
                       default='auto', help='Mode de fonctionnement')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Intervalle entre les envois (secondes)')
    parser.add_argument('--device', default='IoT-DEVICE-001', 
                       help='ID du dispositif IoT')
    parser.add_argument('--condition', choices=['normal', 'supraventricular', 'ventricular', 'random'],
                       default='random', help='Type de condition ECG')
    
    args = parser.parse_args()
    
    # Vérifier la santé du système d'abord
    if not check_system_health():
        print("❌ Le système n'est pas prêt. Vérifiez que:")
        print("   - Le load balancer est lancé sur localhost:5000")
        print("   - Les fog nodes sont démarrés (ports 5001, 5002, 5003)")
        print("   - Le cloud server est lancé sur localhost:8070")
        return
    
    simulator = IoTDeviceSimulator(args.device, args.interval)
    
    if args.mode == 'interactive':
        interactive_mode()
    
    elif args.mode == 'single':
        condition_probas = {args.condition: 1.0} if args.condition != 'random' else {
            'normal': 0.7, 'supraventricular': 0.2, 'ventricular': 0.1
        }
        simulator.send_signal(condition_probas)
    
    else:  # mode auto
        # Probabilités réalistes pour un hôpital
        condition_probas = {
            'normal': 0.75,           # 75% de cas normaux
            'supraventricular': 0.20,  # 20% d'arythmies bénignes  
            'ventricular': 0.05       # 5% de cas critiques
        }
        
        try:
            simulator.start_continuous_sending(condition_probas)
        except KeyboardInterrupt:
            simulator.stop()
            print(f"\n📊 Statistiques finales:")
            print(f"   Signaux envoyés: {simulator.stats['total_sent']}")
            print(f"   Succès: {simulator.stats['successful']}")
            print(f"   Échecs: {simulator.stats['failed']}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏥 SIMULATEUR IoT - Signaux ECG Médicaux")
    print("="*70)
    print("Ce simulateur génère des signaux ECG réalistes et les envoie")
    print("vers le système Fog Computing pour analyse en temps réel.")
    print("="*70)
    
    main()