"""
TABLEAU DE BORD MÉDICAL - STREAMLIT
Installation : pip install streamlit requests plotly pandas
Lancement : streamlit run medical_dashboard.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# Configuration de la page
st.set_page_config(
    page_title="Surveillance Médicale - Fog Computing",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API
API_URL = "http://127.0.0.1:8070"

# CSS personnalisé
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #EFF6FF 0%, #E0E7FF 100%);
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #FEE2E2;
        border-left: 4px solid #DC2626;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .alert-warning {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .patient-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.3s;
    }
    .patient-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    .status-normal {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
    }
    .status-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
    }
    .status-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# ========================================
# FONCTIONS API FIREBASE
# ========================================
@st.cache_data(ttl=2)
def fetch_patients():
    try:
        response = requests.get(f"{API_URL}/api/patients", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=2)
def fetch_alerts():
    try:
        response = requests.get(f"{API_URL}/api/alerts", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=2)
def fetch_history(patient_id):
    try:
        response = requests.get(f"{API_URL}/api/history/{patient_id}", timeout=5)
        return response.json()['data'] if response.status_code == 200 else []
    except Exception as e:
        st.error(f"Erreur récupération historique: {e}")
        return []

@st.cache_data(ttl=2)
def fetch_status():
    try:
        response = requests.get(f"{API_URL}/api/stats", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def fetch_patient_detailed_history(patient_id):
    try:
        response = requests.get(f"{API_URL}/api/patient/{patient_id}/history", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def acknowledge_alert(alert_id):
    try:
        response = requests.post(f"{API_URL}/api/alerts/{alert_id}/acknowledge", timeout=5)
        return response.status_code == 200
    except:
        return False

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🏥 Surveillance Médicale en Temps Réel")
    st.markdown("**Système Fog Computing** - Architecture IoT → Fog → Cloud")
with col2:
    st.markdown(f"### ⏰ {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.rerun()

st.markdown("---")

# Récupération des données
patients = fetch_patients()
alerts = fetch_alerts()
system_status = fetch_status()

# Vérification de la connexion
if not patients:
    st.error("❌ **Erreur de connexion au serveur**")
    st.warning("Assurez-vous que le serveur cloud est lancé : `python cloud_server.py`")
    st.stop()

# Initialisation de la session
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = patients[0]['id'] if patients else None

# Sidebar - Liste des patients
with st.sidebar:
    st.header("👥 Patients Surveillés")
    st.markdown(f"**Total :** {len(patients)} patients")
    
    st.markdown("---")
    
    for patient in patients:
        # Gestion sécurisée du statut
        status = patient.get('status', 'normal')
        status_config = {
            'normal': {'class': 'status-normal', 'label': '✅ Normal'},
            'warning': {'class': 'status-warning', 'label': '⚠️ Alerte'},
            'critical': {'class': 'status-critical', 'label': '🚨 Critique'}
        }
        config = status_config.get(status, status_config['normal'])
        
        if st.button(
            f"{patient.get('name', 'Patient')} (ID: {patient['id']})",
            key=f"patient_{patient['id']}",
            use_container_width=True,
            type="primary" if st.session_state.selected_patient == patient['id'] else "secondary"
        ):
            st.session_state.selected_patient = patient['id']
            st.rerun()
        
        st.markdown(f"""
            <div style='text-align: center; margin: -10px 0 10px 0;'>
                <span class='{config['class']}'>{config['label']}</span>
            </div>
            <div style='display: flex; justify-content: space-around; font-size: 12px; margin-bottom: 15px;'>
                <div>❤️ {int(patient.get('heart_rate', 72))} bpm</div>
                <div>🌡️ {patient.get('temperature', 36.6):.1f}°C</div>
                <div>💧 {int(patient.get('spo2', 98))}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alertes dans la sidebar
    st.header("🔔 Alertes Récentes")
    st.markdown(f"**{len(alerts)}** alertes actives")

    for alert in alerts[:3]:
        severity = alert.get("severity", "warning")
        patient_id = alert.get("patient_id", None)
        
        # Trouver le nom du patient
        patient_name = "Patient inconnu"
        for patient in patients:
            if patient['id'] == patient_id:
                patient_name = patient.get('name', patient_id)
                break
        
        # Classe CSS selon sévérité
        alert_class = "alert-critical" if severity == 'critical' else "alert-warning"
        
        # Affichage
        st.markdown(f"""
            <div class='{alert_class}'>
                <strong>{severity.upper()}</strong><br>
                <small>{patient_name} - Classe: {alert.get('class_name', 'N/A')}</small><br>
                <small style='color: #666;'>{datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')}</small>
            </div>
        """, unsafe_allow_html=True)

# Patient sélectionné
selected_patient = next((p for p in patients if p['id'] == st.session_state.selected_patient), patients[0] if patients else None)

if not selected_patient:
    st.error("Aucun patient sélectionné")
    st.stop()

# Section 1 : Signaux Vitaux
st.header(f"📊 Signaux Vitaux - {selected_patient.get('name', 'Patient')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    heart_rate = selected_patient.get('heart_rate', 72)
    delta_color = "inverse" if heart_rate > 100 else "normal"
    st.metric(
        label="❤️ Fréquence Cardiaque",
        value=f"{int(heart_rate)} bpm",
        delta="Élevé" if heart_rate > 100 else "Normal",
        delta_color=delta_color
    )

with col2:
    temperature = selected_patient.get('temperature', 36.6)
    delta_color = "inverse" if temperature > 38 else "normal"
    st.metric(
        label="🌡️ Température",
        value=f"{temperature:.1f} °C",
        delta="Fièvre" if temperature > 38 else "Normal",
        delta_color=delta_color
    )

with col3:
    spo2 = selected_patient.get('spo2', 98)
    delta_color = "inverse" if spo2 < 93 else "normal"
    st.metric(
        label="💧 Saturation O₂",
        value=f"{int(spo2)} %",
        delta="Faible" if spo2 < 93 else "Normal",
        delta_color=delta_color
    )

with col4:
    blood_pressure = selected_patient.get('blood_pressure', 120)
    delta_color = "inverse" if blood_pressure > 140 else "normal"
    st.metric(
        label="📈 Tension Artérielle",
        value=f"{int(blood_pressure)} mmHg",
        delta="Élevé" if blood_pressure > 140 else "Normal",
        delta_color=delta_color
    )

st.markdown("---")

# Section 2 : Dernière prédiction ECG
st.header("🫀 Dernière Analyse ECG")

if selected_patient.get('last_prediction'):
    last_pred = selected_patient['last_prediction']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Type de Battement",
            value=last_pred.get('class_name', 'N/A')
        )
    
    with col2:
        confidence = last_pred.get('confidence', 0) * 100
        st.metric(
            label="Confiance de Prédiction", 
            value=f"{confidence:.1f}%"
        )
    
    with col3:
        alert_status = "🚨 OUI" if last_pred.get('alert', False) else "✅ Non"
        st.metric(
            label="Alerte Générée",
            value=alert_status
        )
    
    with col4:
        history_count = selected_patient.get('history_count', 0)
        st.metric(
            label="Total Analyses",
            value=history_count
        )
        
    # Afficher le timestamp de la dernière analyse
    timestamp = last_pred.get('timestamp', '')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"🕒 Dernière analyse: {dt.strftime('%d/%m/%Y à %H:%M:%S')}")
        except:
            st.caption(f"🕒 Dernière analyse: {timestamp}")
    
else:
    st.info("Aucune donnée ECG disponible pour ce patient")

st.markdown("---")

# Section 3 : Historique Complet des Prédictions
st.header("📈 Historique des Analyses ECG")

# Bouton pour voir l'historique détaillé
if st.button("📋 Voir l'historique complet", type="secondary"):
    try:
        history_data = fetch_patient_detailed_history(selected_patient['id'])
        
        if history_data and history_data.get('history'):
            st.subheader(f"Historique complet de {selected_patient.get('name', 'Patient')}")
            
            # Créer un DataFrame pour l'affichage
            history_df = pd.DataFrame(history_data['history'])
            
            # Formater les dates
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            history_df['time'] = history_df['timestamp'].dt.strftime('%H:%M:%S')
            history_df['date'] = history_df['timestamp'].dt.strftime('%Y-%m-%d')
            history_df['confidence_pct'] = history_df['confidence'] * 100
            
            # Afficher le tableau
            st.dataframe(
                history_df[['date', 'time', 'class_name', 'confidence_pct', 'alert']],
                use_container_width=True,
                column_config={
                    "date": "Date",
                    "time": "Heure", 
                    "class_name": "Type de Battement",
                    "confidence_pct": st.column_config.NumberColumn(
                        "Confiance",
                        format="%.1f%%",
                    ),
                    "alert": "Alerte"
                }
            )
            
            # Graphique de l'évolution de la confiance
            st.subheader("📊 Évolution de la Confiance")
            fig = px.line(history_df, x='timestamp', y='confidence_pct', 
                          title='Confiance des Prédictions dans le Temps',
                          labels={'confidence_pct': 'Confiance (%)', 'timestamp': 'Temps'})
            fig.update_traces(line=dict(color='#3B82F6', width=3))
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques des types de battements
            st.subheader("📈 Répartition des Types de Battements")
            beat_counts = history_df['class_name'].value_counts()
            fig_pie = px.pie(values=beat_counts.values, names=beat_counts.index,
                           title='Distribution des Types de Battements')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        else:
            st.info("Aucun historique disponible pour ce patient")
    except Exception as e:
        st.error(f"Erreur lors de la récupération de l'historique: {e}")

# Afficher le résumé de l'historique
if selected_patient.get('history_count', 0) > 0:
    st.success(f"📊 {selected_patient['history_count']} analyses ECG enregistrées dans l'historique")
else:
    st.info("Aucune analyse ECG enregistrée pour ce patient")

st.markdown("---")

# Section 4 : Alertes Actives
st.header("🚨 Alertes Actives")

if alerts:
    # Filtrer les alertes pour le patient sélectionné
    patient_alerts = [alert for alert in alerts if alert.get('patient_id') == selected_patient['id']]
    
    if patient_alerts:
        for alert in patient_alerts:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                severity = alert.get('severity', 'warning')
                severity_icon = "🔴" if severity == 'critical' else "🟡"
                st.write(f"{severity_icon} **{alert.get('class_name', 'Alerte ECG')}**")
                st.write(f"Patient: {selected_patient.get('name', 'N/A')}")
            
            with col2:
                confidence = alert.get('confidence', 0) * 100
                st.write(f"Confiance: {confidence:.1f}%")
            
            with col3:
                timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                st.write(f"À: {timestamp.strftime('%H:%M:%S')}")
            
            with col4:
                if st.button("✓ Acquitter", key=f"ack_{alert['id']}"):
                    if acknowledge_alert(alert['id']):
                        st.success("Alerte acquittée!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'acquittement")
            
            st.markdown("---")
    else:
        st.success("✅ Aucune alerte active pour ce patient")
else:
    st.info("Aucune alerte dans le système")

st.markdown("---")

# Section 5 : État du Système
st.header("⚙️ État du Système")

if system_status:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Prédictions",
            value=system_status.get('predictions_total', 0)
        )
    
    with col2:
        st.metric(
            label="Alertes Actives",
            value=system_status.get('alerts_active', 0)
        )
    
    with col3:
        st.metric(
            label="Patients Suivis",
            value=system_status.get('patients_total', 0)
        )
    
    with col4:
        st.metric(
            label="Statut Cloud",
            value="✅ En ligne"
        )
else:
    st.warning("Impossible de récupérer l'état du système")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Projet Fog Computing Médical</strong> | Développé par l'équipe E4</p>
        <p>Mise à jour automatique toutes les 2 secondes</p>
    </div>
""", unsafe_allow_html=True)

# Auto-refresh toutes les 2 secondes
time.sleep(2)
st.rerun()