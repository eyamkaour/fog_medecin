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
API_URL = "http://127.0.0.1:6000"

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

# Fonction pour récupérer les données
@st.cache_data(ttl=2)
def fetch_patients():
    try:
        response = requests.get(f"{API_URL}/patients", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=2)
def fetch_alerts():
    try:
        response = requests.get(f"{API_URL}/alerts", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=2)
def fetch_history(patient_id):
    try:
        response = requests.get(f"{API_URL}/history/{patient_id}", timeout=5)
        return response.json()['data'] if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=2)
def fetch_status():
    try:
        response = requests.get(f"{API_URL}/status", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

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
    st.warning("Assurez-vous que le serveur mock est lancé : `python mock_cloud_server.py`")
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
        status_class = f"status-{patient['status']}"
        status_label = {
            'normal': '✅ Normal',
            'warning': '⚠️ Alerte',
            'critical': '🚨 Critique'
        }[patient['status']]
        
        if st.button(
            f"{patient['name']} (ID: {patient['id']})",
            key=f"patient_{patient['id']}",
            use_container_width=True,
            type="primary" if st.session_state.selected_patient == patient['id'] else "secondary"
        ):
            st.session_state.selected_patient = patient['id']
            st.rerun()
        
        st.markdown(f"""
            <div style='text-align: center; margin: -10px 0 10px 0;'>
                <span class='{status_class}'>{status_label}</span>
            </div>
            <div style='display: flex; justify-content: space-around; font-size: 12px; margin-bottom: 15px;'>
                <div>❤️ {int(patient['heart_rate'])} bpm</div>
                <div>🌡️ {patient['temperature']:.1f}°C</div>
                <div>💧 {int(patient['spo2'])}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alertes dans la sidebar
    st.header("🔔 Alertes Récentes")
    st.markdown(f"**{len(alerts)}** alertes actives")
    
    for alert in alerts[:3]:
        alert_class = "alert-critical" if alert['severity'] == 'critical' else "alert-warning"
        st.markdown(f"""
            <div class='{alert_class}'>
                <strong>{alert['type']}</strong><br>
                <small>{alert['patient_name']} - {alert['value']}</small><br>
                <small style='color: #666;'>{datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')}</small>
            </div>
        """, unsafe_allow_html=True)

# Patient sélectionné
selected_patient = next((p for p in patients if p['id'] == st.session_state.selected_patient), patients[0])

# Section 1 : Signaux Vitaux
st.header(f"📊 Signaux Vitaux - {selected_patient['name']}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_color = "inverse" if selected_patient['heart_rate'] > 100 else "normal"
    st.metric(
        label="❤️ Fréquence Cardiaque",
        value=f"{int(selected_patient['heart_rate'])} bpm",
        delta="Élevé" if selected_patient['heart_rate'] > 100 else "Normal",
        delta_color=delta_color
    )

with col2:
    delta_color = "inverse" if selected_patient['temperature'] > 38 else "normal"
    st.metric(
        label="🌡️ Température",
        value=f"{selected_patient['temperature']:.1f} °C",
        delta="Fièvre" if selected_patient['temperature'] > 38 else "Normal",
        delta_color=delta_color
    )

with col3:
    delta_color = "inverse" if selected_patient['spo2'] < 93 else "normal"
    st.metric(
        label="💧 Saturation O₂",
        value=f"{int(selected_patient['spo2'])} %",
        delta="Faible" if selected_patient['spo2'] < 93 else "Normal",
        delta_color=delta_color
    )

with col4:
    delta_color = "inverse" if selected_patient['blood_pressure'] > 140 else "normal"
    st.metric(
        label="📈 Tension Artérielle",
        value=f"{int(selected_patient['blood_pressure'])} mmHg",
        delta="Élevé" if selected_patient['blood_pressure'] > 140 else "Normal",
        delta_color=delta_color
    )

st.markdown("---")

# Section 2 : Graphiques d'évolution
st.header("📈 Évolution Temporelle")

history_data = fetch_history(selected_patient['id'])

if history_data:
    df = pd.DataFrame(history_data)
    
    # Graphique 1 : Fréquence Cardiaque
    fig_hr = go.Figure()
    fig_hr.add_trace(go.Scatter(
        x=df['time'],
        y=df['heart_rate'],
        mode='lines+markers',
        name='Fréquence Cardiaque',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=6)
    ))
    fig_hr.update_layout(
        title="Fréquence Cardiaque (bpm)",
        xaxis_title="Heure",
        yaxis_title="BPM",
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(range=[50, 150])
    )
    st.plotly_chart(fig_hr, use_container_width=True)
    
    # Graphique 2 : Température
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df['time'],
        y=df['temperature'],
        mode='lines+markers',
        name='Température',
        line=dict(color='#F97316', width=3),
        marker=dict(size=6)
    ))
    fig_temp.update_layout(
        title="Température Corporelle (°C)",
        xaxis_title="Heure",
        yaxis_title="°C",
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(range=[35, 40])
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # Graphique 3 : SpO2
    fig_spo2 = go.Figure()
    fig_spo2.add_trace(go.Scatter(
        x=df['time'],
        y=df['spo2'],
        mode='lines+markers',
        name='Saturation O₂',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=6)
    ))
    fig_spo2.update_layout(
        title="Saturation en Oxygène (%)",
        xaxis_title="Heure",
        yaxis_title="%",
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(range=[85, 100])
    )
    st.plotly_chart(fig_spo2, use_container_width=True)

st.markdown("---")

# Section 3 : État du Système
st.header("⚙️ État du Système")

if system_status:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background-color: #D1FAE5; padding: 20px; border-radius: 10px; text-align: center;'>
                <h3>📱 Couche IoT</h3>
                <h2 style='color: #065F46;'>Actif</h2>
                <p>{} capteurs connectés</p>
            </div>
        """.format(system_status['iot']['devices_connected']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background-color: #DBEAFE; padding: 20px; border-radius: 10px; text-align: center;'>
                <h3>🖥️ Nœud Fog</h3>
                <h2 style='color: #1E40AF;'>En ligne</h2>
                <p>Latence: {} ms</p>
            </div>
        """.format(system_status['fog']['latency_ms']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background-color: #E9D5FF; padding: 20px; border-radius: 10px; text-align: center;'>
                <h3>☁️ Cloud</h3>
                <h2 style='color: #6B21A8;'>Synchronisé</h2>
                <p>DB: {} MB</p>
            </div>
        """.format(system_status['cloud']['database_size_mb']), unsafe_allow_html=True)

st.markdown("---")

# Section 4 : Tableau détaillé des alertes
st.header("🚨 Historique des Alertes")

if alerts:
    alerts_df = pd.DataFrame(alerts)
    alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
    alerts_df = alerts_df.sort_values('timestamp', ascending=False)
    
    st.dataframe(
        alerts_df[['patient_name', 'type', 'value', 'severity', 'timestamp']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "patient_name": "Patient",
            "type": "Type d'alerte",
            "value": "Valeur",
            "severity": "Sévérité",
            "timestamp": st.column_config.DatetimeColumn("Horodatage", format="DD/MM/YYYY HH:mm:ss")
        }
    )
else:
    st.info("Aucune alerte active pour le moment.")

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