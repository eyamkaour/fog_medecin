"""
LOAD BALANCER CORRIGÉ - Répartition intelligente entre Fog Nodes
Port: 5000
Strategies: Round-Robin + Least Connections + Health Monitoring
"""

from flask import Flask, request, jsonify
import requests
from datetime import datetime
from collections import deque
import threading
import time

app = Flask(__name__)

# Configuration des Fog Nodes
FOG_NODES = [
    {"id": "FOG-001", "url": "http://localhost:5001", "specialty": "general"},
    {"id": "FOG-002", "url": "http://localhost:5002", "specialty": "critical_care"},
    {"id": "FOG-003", "url": "http://localhost:5003", "specialty": "pediatric"}
]

# Statistiques de charge par node
node_stats = {
    node['id']: {
        'url': node['url'],
        'requests': 0,
        'active_connections': 0,
        'last_health': None,
        'status': 'unknown',
        'response_times': deque(maxlen=10),
        'specialty': node['specialty']
    } for node in FOG_NODES
}

# Index pour Round-Robin
current_node_index = 0
stats_lock = threading.Lock()

def health_check_background():
    """Vérifie la santé des fog nodes en arrière-plan"""
    while True:
        for node_id, stats in node_stats.items():
            try:
                start = time.time()
                response = requests.get(f"{stats['url']}/health", timeout=2)
                response_time = time.time() - start
                
                with stats_lock:
                    if response.status_code == 200:
                        stats['status'] = 'healthy'
                        stats['last_health'] = datetime.now().isoformat()
                        stats['response_times'].append(response_time)
                    else:
                        stats['status'] = 'unhealthy'
            except Exception as e:
                with stats_lock:
                    stats['status'] = 'offline'
                    stats['last_health'] = datetime.now().isoformat()
        
        time.sleep(5)  # Check toutes les 5 secondes

def get_healthy_nodes():
    """Retourne les nodes sains"""
    with stats_lock:
        return [node_id for node_id, stats in node_stats.items() 
                if stats['status'] == 'healthy']

def select_node_round_robin():
    """Sélection Round-Robin avec nodes sains uniquement"""
    global current_node_index
    healthy_nodes = get_healthy_nodes()
    
    if not healthy_nodes:
        return None
    
    with stats_lock:
        # Trouver le prochain node sain
        attempts = 0
        while attempts < len(FOG_NODES):
            node_id = list(node_stats.keys())[current_node_index % len(FOG_NODES)]
            current_node_index += 1
            
            if node_id in healthy_nodes:
                return node_id
            attempts += 1
    
    return healthy_nodes[0] if healthy_nodes else None

def select_node_least_connections():
    """Sélection basée sur le moins de connexions actives"""
    healthy_nodes = get_healthy_nodes()
    
    if not healthy_nodes:
        return None
    
    with stats_lock:
        # Trouver le node avec le moins de connexions
        min_connections = float('inf')
        best_node = None
        
        for node_id in healthy_nodes:
            connections = node_stats[node_id]['active_connections']
            if connections < min_connections:
                min_connections = connections
                best_node = node_id
        
        return best_node

def select_node_by_specialty(patient_data):
    """Sélection basée sur la spécialité médicale"""
    status = patient_data.get('status', 'normal')
    heart_rate = patient_data.get('heart_rate', 72)
    
    # Logique de routing intelligente
    if status == 'critical' or heart_rate > 120:
        target_specialty = 'critical_care'
    elif status == 'warning':
        target_specialty = 'general'
    else:
        target_specialty = 'pediatric'
    
    # Trouver le fog node avec cette spécialité
    for node_id, stats in node_stats.items():
        if stats['specialty'] == target_specialty and stats['status'] == 'healthy':
            return node_id
    
    # Fallback sur least connections si spécialité non disponible
    return select_node_least_connections()

@app.route("/predict", methods=["POST"])
def predict():
    """Route principale - Répartition de charge"""
    selected_node_id = None
    
    try:
        patient_data = request.json
        
        # STRATÉGIE 1: Par spécialité (si données patient disponibles)
        if patient_data and 'status' in patient_data:
            selected_node_id = select_node_by_specialty(patient_data)
            strategy = "specialty-based"
        
        # STRATÉGIE 2: Least Connections (fallback)
        if not selected_node_id:
            selected_node_id = select_node_least_connections()
            strategy = "least-connections"
        
        # STRATÉGIE 3: Round-Robin (dernier fallback)
        if not selected_node_id:
            selected_node_id = select_node_round_robin()
            strategy = "round-robin"
        
        if not selected_node_id:
            return jsonify({"error": "Aucun fog node disponible"}), 503
        
        # Incrémenter les connexions actives
        with stats_lock:
            node_stats[selected_node_id]['active_connections'] += 1
            node_stats[selected_node_id]['requests'] += 1
        
        # Forward la requête au fog node sélectionné
        node_url = node_stats[selected_node_id]['url']
        start_time = time.time()
        
        response = requests.post(
            f"{node_url}/predict", 
            json=patient_data, 
            timeout=15
        )
        
        processing_time = time.time() - start_time
        
        # Décrémenter les connexions actives
        with stats_lock:
            node_stats[selected_node_id]['active_connections'] -= 1
            node_stats[selected_node_id]['response_times'].append(processing_time)
        
        # Ajouter des infos de routing dans la réponse
        result = response.json()
        result['load_balancer_info'] = {
            'fog_node': selected_node_id,
            'strategy': strategy,
            'processing_time': round(processing_time, 3)
        }
        
        print(f"✅ Requête routée vers {selected_node_id} ({strategy}) - {processing_time:.2f}s")
        
        return jsonify(result), response.status_code
        
    except requests.exceptions.Timeout:
        # Marquer le node comme lent
        if selected_node_id:
            with stats_lock:
                node_stats[selected_node_id]['active_connections'] -= 1
                node_stats[selected_node_id]['status'] = 'slow'
        return jsonify({"error": "Fog node timeout"}), 504
        
    except Exception as e:
        if selected_node_id:
            with stats_lock:
                node_stats[selected_node_id]['active_connections'] -= 1
        print(f"❌ Erreur: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check du load balancer"""
    healthy_nodes = get_healthy_nodes()
    
    with stats_lock:
        nodes_status = {
            node_id: {
                'status': stats['status'],
                'active_connections': stats['active_connections'],
                'total_requests': stats['requests'],
                'avg_response_time': round(sum(stats['response_times']) / len(stats['response_times']), 3) 
                                     if stats['response_times'] else 0,
                'specialty': stats['specialty']
            } for node_id, stats in node_stats.items()
        }
    
    return jsonify({
        "status": "ok",
        "load_balancer": "online",
        "healthy_nodes": len(healthy_nodes),
        "total_nodes": len(FOG_NODES),
        "nodes": nodes_status
    }), 200

@app.route("/stats", methods=["GET"])
def stats():
    """Statistiques détaillées de répartition"""
    with stats_lock:
        total_requests = sum(s['requests'] for s in node_stats.values())
        
        stats_data = {
            'total_requests': total_requests,
            'nodes': {}
        }
        
        for node_id, node_data in node_stats.items():
            stats_data['nodes'][node_id] = {
                'requests': node_data['requests'],
                'percentage': round((node_data['requests'] / total_requests * 100), 2) if total_requests > 0 else 0,
                'active_connections': node_data['active_connections'],
                'status': node_data['status'],
                'avg_response_time': round(sum(node_data['response_times']) / len(node_data['response_times']), 3) 
                                     if node_data['response_times'] else 0,
                'specialty': node_data['specialty']
            }
    
    return jsonify(stats_data), 200

@app.route("/reset-stats", methods=["POST"])
def reset_stats():
    """Réinitialiser les statistiques"""
    with stats_lock:
        for node_id in node_stats:
            node_stats[node_id]['requests'] = 0
            node_stats[node_id]['response_times'].clear()
    
    return jsonify({"message": "Statistiques réinitialisées"}), 200

if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚖️  LOAD BALANCER INTELLIGENT - Démarrage")
    print("="*70)
    print("Stratégies: Specialty-Based → Least-Connections → Round-Robin")
    print(f"Fog Nodes surveillés:")
    for node in FOG_NODES:
        print(f"  • {node['id']}: {node['url']} ({node['specialty']})")
    print(f"Port: 5000")
    print("="*70 + "\n")
    
    # Démarrer le monitoring de santé en arrière-plan
    health_thread = threading.Thread(target=health_check_background, daemon=True)
    health_thread.start()
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)