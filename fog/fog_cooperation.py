"""
SERVICE DE COOPÉRATION FOG - Corrigé
Gère la communication, synchronisation et alertes entre fog nodes
"""

import requests
from datetime import datetime
import threading
import time

class FogCooperation:
    def __init__(self, current_fog_id, fog_nodes_config):
        """
        Args:
            current_fog_id: ID du fog node actuel (ex: "FOG-001")
            fog_nodes_config: Liste des fog nodes [{id, url, specialty}, ...]
        """
        self.current_fog_id = current_fog_id
        self.fog_nodes = fog_nodes_config
        self.shared_alerts = []
        self.sync_lock = threading.Lock()
        
    def get_node_by_specialty(self, patient_data):
        """
        Route vers le fog node spécialisé selon les données du patient
        """
        status = patient_data.get('status', 'normal')
        heart_rate = patient_data.get('heart_rate', 72)
        
        # Logique de routing médicale
        if status == 'critical' or heart_rate > 120:
            target_specialty = 'critical_care'
        elif status == 'warning' or (heart_rate > 100 and heart_rate <= 120):
            target_specialty = 'general'
        else:
            target_specialty = 'pediatric'
        
        # Trouver le fog node avec cette spécialité
        for node in self.fog_nodes:
            if node['specialty'] == target_specialty:
                return node
        
        # Fallback sur fog général
        return self.fog_nodes[0]
    
    def share_alert(self, alert_data):
        """
        Partage une alerte critique avec tous les autres fog nodes
        Utilisé pour les cas d'urgence nécessitant coordination
        """
        alert_payload = {
            'alert_id': alert_data.get('alert_id'),
            'patient_id': alert_data.get('patient_id'),
            'severity': alert_data.get('severity', 'high'),
            'message': alert_data.get('message'),
            'timestamp': datetime.now().isoformat(),
            'source_fog': self.current_fog_id
        }
        
        shared_count = 0
        for node in self.fog_nodes:
            if node['id'] != self.current_fog_id:
                try:
                    response = requests.post(
                        f"{node['url']}/alerts/share", 
                        json=alert_payload, 
                        timeout=3
                    )
                    if response.status_code == 200:
                        shared_count += 1
                        print(f"📢 Alerte partagée: {self.current_fog_id} → {node['id']}")
                except Exception as e:
                    print(f"❌ Échec partage alerte vers {node['id']}: {str(e)}")
        
        return shared_count
    
    def sync_patient_data(self, patient_id, analysis_result):
        """
        Synchronise les résultats d'analyse avec les autres fog nodes
        Permet de partager l'historique patient entre fogs
        """
        sync_data = {
            'patient_id': patient_id,
            'last_analysis': analysis_result,
            'timestamp': datetime.now().isoformat(),
            'source_fog': self.current_fog_id
        }
        
        synced_nodes = []
        for node in self.fog_nodes:
            if node['id'] != self.current_fog_id:
                try:
                    response = requests.post(
                        f"{node['url']}/sync/patient", 
                        json=sync_data, 
                        timeout=3
                    )
                    if response.status_code == 200:
                        synced_nodes.append(node['id'])
                except Exception as e:
                    print(f"⚠️ Sync échouée vers {node['id']}: {str(e)}")
        
        return synced_nodes
    
    def request_analysis_from_peer(self, patient_data, target_specialty):
        """
        Demande une analyse à un fog peer spécialisé
        Utilisé quand le fog actuel n'a pas la capacité/spécialité
        """
        target_node = None
        for node in self.fog_nodes:
            if node['specialty'] == target_specialty and node['id'] != self.current_fog_id:
                target_node = node
                break
        
        if not target_node:
            return None
        
        try:
            response = requests.post(
                f"{target_node['url']}/predict",
                json=patient_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                result['analyzed_by'] = target_node['id']
                print(f"🤝 Analyse déléguée à {target_node['id']} ({target_specialty})")
                return result
        except Exception as e:
            print(f"❌ Échec délégation vers {target_node['id']}: {str(e)}")
        
        return None
    
    def get_system_health(self):
        """
        Récupère l'état de santé de tous les fog nodes du système
        """
        health_status = {}
        
        for node in self.fog_nodes:
            try:
                start = time.time()
                response = requests.get(f"{node['url']}/health", timeout=2)
                response_time = (time.time() - start) * 1000  # en ms
                
                if response.status_code == 200:
                    health_data = response.json()
                    health_status[node['id']] = {
                        'status': 'healthy',
                        'response_time_ms': round(response_time, 2),
                        'specialty': node['specialty'],
                        'details': health_data
                    }
                else:
                    health_status[node['id']] = {
                        'status': 'unhealthy',
                        'response_time_ms': round(response_time, 2),
                        'specialty': node['specialty']
                    }
            except Exception as e:
                health_status[node['id']] = {
                    'status': 'offline',
                    'response_time_ms': None,
                    'specialty': node['specialty'],
                    'error': str(e)
                }
        
        return health_status
    
    def receive_shared_alert(self, alert_data):
        """
        Reçoit une alerte partagée d'un autre fog node
        À appeler dans l'endpoint /alerts/share
        """
        with self.sync_lock:
            self.shared_alerts.append({
                'received_at': datetime.now().isoformat(),
                'alert': alert_data
            })
            
            # Garder seulement les 100 dernières alertes
            if len(self.shared_alerts) > 100:
                self.shared_alerts = self.shared_alerts[-100:]
        
        print(f"📨 Alerte reçue de {alert_data.get('source_fog')}: {alert_data.get('message')}")
        return True
    
    def get_shared_alerts(self, patient_id=None):
        """
        Récupère les alertes partagées, optionnellement filtrées par patient
        """
        with self.sync_lock:
            if patient_id:
                return [a for a in self.shared_alerts 
                       if a['alert'].get('patient_id') == patient_id]
            return self.shared_alerts.copy()
    
    def broadcast_critical_event(self, event_data):
        """
        Diffuse un événement critique à tous les fog nodes
        (ex: panne système, alerte sécurité)
        """
        event_payload = {
            'event_type': event_data.get('type'),
            'severity': 'critical',
            'message': event_data.get('message'),
            'timestamp': datetime.now().isoformat(),
            'source_fog': self.current_fog_id
        }
        
        broadcast_results = {'success': 0, 'failed': 0}
        
        for node in self.fog_nodes:
            if node['id'] != self.current_fog_id:
                try:
                    response = requests.post(
                        f"{node['url']}/events/critical",
                        json=event_payload,
                        timeout=3
                    )
                    if response.status_code == 200:
                        broadcast_results['success'] += 1
                    else:
                        broadcast_results['failed'] += 1
                except:
                    broadcast_results['failed'] += 1
        
        return broadcast_results


# Factory function pour créer l'instance de coopération
def create_fog_cooperation(fog_id, fog_nodes_config):
    """
    Crée une instance de FogCooperation
    
    Args:
        fog_id: "FOG-001", "FOG-002", etc.
        fog_nodes_config: Liste de tous les fog nodes
    
    Returns:
        FogCooperation instance
    """
    return FogCooperation(fog_id, fog_nodes_config)


# Configuration par défaut des fog nodes
DEFAULT_FOG_NODES = [
    {"id": "FOG-001", "url": "http://localhost:5001", "specialty": "general"},
    {"id": "FOG-002", "url": "http://localhost:5002", "specialty": "critical_care"},
    {"id": "FOG-003", "url": "http://localhost:5003", "specialty": "pediatric"}
]