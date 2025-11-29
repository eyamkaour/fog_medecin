# 🏥 Système de Surveillance Médicale ECG - Fog Computing

![Architecture](https://img.shields.io/badge/Architecture-Fog%20Computing-blue)
![Python](https://img.shields.io/badge/Python-3.10-green)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.13-orange)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-yellow)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

## 📋 Table des Matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture du Système](#-architecture-du-système)
- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Structure du Projet](#-structure-du-projet)
- [Lancement du Système](#-lancement-du-système)
- [Utilisation](#-utilisation)
- [API Documentation](#-api-documentation)
- [Monitoring & Dashboard](#-monitoring--dashboard)
- [Dépannage](#-dépannage)
- [Scripts de Démarrage](#-scripts-de-démarrage-rapide)

---

## 🎯 Vue d'ensemble

Système intelligent de surveillance médicale en temps réel basé sur une architecture **Fog Computing**. Le système analyse les signaux ECG des patients pour détecter automatiquement les anomalies cardiaques et génère des alertes médicales.

### 🌟 Points Clés

- **Architecture 4 Couches** : IoT → Load Balancer → Fog Nodes → Cloud
- **IA embarquée** : Modèle CNN TensorFlow pour classification ECG
- **Coopération Fog** : Communication inter-nodes avec routing intelligent
- **Temps Réel** : Dashboard Streamlit avec mises à jour automatiques
- **Haute Disponibilité** : Load balancing et health monitoring

---

## 🏗️ Architecture du Système

```
┌─────────────────────────────────────────────────────────────────┐
│                         COUCHE IoT                               │
│           Dossier: /iot/                                         │
│  Simulateurs de dispositifs médicaux (ECG, capteurs vitaux)     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LOAD BALANCER (Port 5000)                    │
│           Dossier: /fog/                                         │
│  • Round-Robin Strategy                                          │
│  • Least Connections                                             │
│  • Specialty-Based Routing                                       │
│  • Health Monitoring                                             │
└──────────┬───────────────────┬────────────────────┬─────────────┘
           │                   │                    │
           ▼                   ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   FOG NODE 1     │ │   FOG NODE 2     │ │   FOG NODE 3     │
│   Port: 5001     │ │   Port: 5002     │ │   Port: 5003     │
│ Dossier: /fog/   │ │ Dossier: /fog/   │ │ Dossier: /fog/   │
│ Specialty:       │ │ Specialty:       │ │ Specialty:       │
│ General          │ │ Critical Care    │ │ Pediatric        │
│                  │ │                  │ │                  │
│ • CNN Model      │ │ • CNN Model      │ │ • CNN Model      │
│ • Cooperation    │ │ • Cooperation    │ │ • Cooperation    │
│ • Alert Sharing  │ │ • Alert Sharing  │ │ • Alert Sharing  │
└──────────┬───────┘ └─────────┬────────┘ └────────┬─────────┘
           │                   │                    │
           └───────────────────┼────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD SERVER (Port 8070)                      │
│           Dossier: /cloud/                                       │
│  • Firebase Firestore                                            │
│  • Data Persistence                                              │
│  • Patient History                                               │
│  • Alert Management                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              DASHBOARD STREAMLIT (Port 8501)                     │
│           Dossier: /dashboard/                                   │
│  • Real-time Visualization                                       │
│  • Patient Monitoring                                            │
│  • Alert Management                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

### 🔬 Analyse ECG Intelligente
- **Classification automatique** : 5 types de battements cardiaques
  - Normal Beat (Classe 0)
  - Supraventricular (Classe 1) 
  - Ventricular (Classe 2) - CRITIQUE
  - Fusion (Classe 3)
  - Unknown (Classe 4)
- **Confiance de prédiction** : Score de fiabilité pour chaque analyse
- **Détection d'anomalies** : Alertes automatiques si anomalie détectée

### 🤝 Coopération Inter-Fog
- **Routing Intelligent** : Redirection automatique selon la spécialité
- **Partage d'Alertes** : Diffusion des cas critiques à tous les nodes
- **Synchronisation de Données** : Historique patient partagé
- **Délégation de Tâches** : Transfert de patients entre spécialités

### ⚖️ Load Balancing Avancé
- **Multi-stratégie** :
  1. Specialty-Based (par spécialité médicale)
  2. Least Connections (charge minimale)
  3. Round-Robin (répartition équitable)
- **Health Monitoring** : Surveillance continue des fog nodes
- **Failover automatique** : Basculement si node défaillant

### 📊 Monitoring Temps Réel
- **Dashboard interactif** : Visualisation des patients en temps réel
- **Historique complet** : Toutes les analyses ECG par patient
- **Gestion d'alertes** : Acquittement et suivi des cas critiques
- **Statistiques système** : Performance et charge des nodes

---

## 📦 Prérequis

### Logiciels Requis
- **Python 3.10** ou supérieur
- **pip** (gestionnaire de paquets Python)
- **Compte Firebase** avec projet Firestore

### Connaissances Recommandées
- Bases en Python
- Notions de réseaux (HTTP, REST API)
- Compréhension basique du Machine Learning (optionnel)

---

## 🚀 Installation

### 1. Cloner le Projet

```bash
git clone <votre-repo>
cd fog-computing-medical-system
```

### 2. Créer un Environnement Virtuel

**Windows :**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r pip-requirements
```

### 4. Vérifier l'Installation

```bash
python -c "import tensorflow; print(tensorflow.__version__)"
python -c "import firebase_admin; print('Firebase OK')"
python -c "import streamlit; print('Streamlit OK')"
```

---

## ⚙️ Configuration

### 1. Configuration Firebase

#### a) Créer un Projet Firebase
1. Aller sur [Firebase Console](https://console.firebase.google.com/)
2. Créer un nouveau projet
3. Activer **Cloud Firestore** (mode production)

#### b) Obtenir les Credentials
1. Projet Firebase → **Paramètres** ⚙️ → **Comptes de service**
2. Cliquer sur **Générer une nouvelle clé privée**
3. Télécharger le fichier JSON

#### c) Placer le Fichier
```bash
# Renommer et placer dans le DOSSIER RACINE du projet
mv ~/Downloads/votre-fichier-firebase.json firebase-credentials.json
```

**Structure attendue :**
```
fog-computing-medical-system/
├── firebase-credentials.json  ← ICI (racine du projet)
├── fog/
├── cloud/
├── iot/
└── dashboard/
```

### 2. Entraîner le Modèle ECG

```bash
# Depuis la racine du projet
python train_model.py
```

**Sortie attendue :**
```
Epoch 10/10
856/856 [==============================] - 12s 14ms/step - loss: 0.0234 - accuracy: 0.9912
Accuracy: 0.9876
✅ Modèle sauvegardé : models/ecg_cnn.h5
```

Le modèle sera créé dans `models/ecg_cnn.h5` à la **racine du projet**.

---

## 📁 Structure du Projet

```
fog-computing-medical-system/
│
├── 📂 fog/                           # DOSSIER FOG COMPUTING
│   ├── fog_node_1.py                # Fog Node 1 (General) - Port 5001
│   ├── fog_node_2.py                # Fog Node 2 (Critical Care) - Port 5002
│   ├── fog_node_3.py                # Fog Node 3 (Pediatric) - Port 5003
│   ├── fog_cooperation.py           # Service de coopération inter-fog
│   └── load_balancer.py             # Load Balancer intelligent - Port 5000
│
├── 📂 cloud/                         # DOSSIER CLOUD
│   └── cloud_server.py              # Serveur Cloud Firebase - Port 8070
│
├── 📂 iot/                           # DOSSIER IoT
│   └── iot_simulator.py             # Simulateur de dispositifs médicaux
│
├── 📂 dashboard/                     # DOSSIER DASHBOARD
│   └── medical_dashboard.py         # Dashboard Streamlit - Port 8501
│
├── 📂 models/                        # MODÈLES IA (racine)
│   └── ecg_cnn.h5                   # Modèle CNN entraîné
│
├── 📂 Data/                          # DATASETS (racine)
│   └── archive/
│       ├── mitbih_train.csv         # Dataset MIT-BIH train
│       └── mitbih_test.csv          # Dataset MIT-BIH test
│
├── 🔥 firebase-credentials.json      # Clés Firebase (RACINE)
├── 🧠 train_model.py                 # Script d'entraînement (racine)
├── 📋 pip-requirements               # Dépendances Python (racine)
└── 📖 README.md                      # Ce fichier (racine)
```

### ⚠️ Points Importants sur la Structure

1. **Modèle CNN** : `models/ecg_cnn.h5` est dans **le dossier racine**, pas dans `/fog/`
2. **Firebase Credentials** : `firebase-credentials.json` est dans **le dossier racine**
3. **Chemins dans les fichiers** :
   - Les **fog nodes** utilisent : `MODEL_PATH = "../models/ecg_cnn.h5"` (chemin relatif)
   - Le **cloud server** utilise : `cred = credentials.Certificate("../firebase-credentials.json")`

---

## 🎬 Lancement du Système

Le système nécessite **6 terminaux** pour fonctionner complètement.

### ⚠️ Ordre de Démarrage Important

Respectez cet ordre pour éviter les erreurs de connexion :

1. Cloud Server
2. Fog Nodes (3)
3. Load Balancer
4. Dashboard
5. IoT Simulator

---

### Terminal 1 : Cloud Server 🌥️

```bash
# Aller dans le dossier cloud
cd cloud

# Lancer le serveur
python cloud_server.py
```

**Vérification :**
```
☁️  CLOUD SERVER - Firebase Firestore (QUOTA FIXED)
🔥 Initialisation Firebase...
✅ Firebase initialisé avec succès!
✅ Optimisé pour éviter 'Quota exceeded'
 * Running on http://0.0.0.0:8070
```

**Si erreur "firebase-credentials.json not found" :**
```bash
# Le fichier doit être dans la RACINE, donc le cloud_server doit le chercher avec:
# credentials.Certificate("../firebase-credentials.json")
```

---

### Terminal 2 : Fog Node 1 (General) 🌫️

```bash
# Aller dans le dossier fog
cd fog

# Lancer Fog Node 1
python fog_node_1.py
```

**Vérification :**
```
🌫️  [FOG-001] FOG NODE avec Coopération - Démarrage
[FOG-001] Initialisation de la coopération...
[FOG-001] Chargement du modèle...
Port: 5001
Spécialité: general
Modèle: ../models/ecg_cnn.h5
Coopération: Activée avec 2 autres fogs
 * Running on http://0.0.0.0:5001
```

**Si erreur "models/ecg_cnn.h5 not found" :**
```bash
# Vérifier que MODEL_PATH dans fog_node_1.py est:
MODEL_PATH = "../models/ecg_cnn.h5"

# Vérifier que le modèle existe:
cd ..
ls models/ecg_cnn.h5
```

---

### Terminal 3 : Fog Node 2 (Critical Care) 🚨

```bash
# Aller dans le dossier fog
cd fog

# Lancer Fog Node 2
python fog_node_2.py
```

**Vérification :**
```
🌫️  [FOG-002] 🚨 FOG NODE SOINS INTENSIFS - Démarrage
[FOG-002] Initialisation de la coopération...
[FOG-002] Chargement du modèle...
Port: 5002
Spécialité: CRITICAL_CARE (Cas critiques)
Modèle: ../models/ecg_cnn.h5
Coopération: Activée avec 2 autres fogs
 * Running on http://0.0.0.0:5002
```

---

### Terminal 4 : Fog Node 3 (Pediatric) 👶

```bash
# Aller dans le dossier fog
cd fog

# Lancer Fog Node 3
python fog_node_3.py
```

**Vérification :**
```
🌫️  [FOG-003] 👶 FOG NODE PÉDIATRIQUE - Démarrage
[FOG-003] Initialisation de la coopération...
[FOG-003] Chargement du modèle...
Port: 5003
Spécialité: PEDIATRIC (Suivi routine)
Modèle: ../models/ecg_cnn.h5
Coopération: Activée avec 2 autres fogs
 * Running on http://0.0.0.0:5003
```

---

### Terminal 5 : Load Balancer ⚖️

```bash
# Aller dans le dossier fog
cd fog

# Lancer le Load Balancer
python load_balancer.py
```

**Vérification :**
```
⚖️  LOAD BALANCER INTELLIGENT - Démarrage
Stratégies: Specialty-Based → Least-Connections → Round-Robin
Fog Nodes surveillés:
  • FOG-001: http://localhost:5001 (general)
  • FOG-002: http://localhost:5002 (critical_care)
  • FOG-003: http://localhost:5003 (pediatric)
Port: 5000
 * Running on http://0.0.0.0:5000
```

---

### Terminal 6 : Dashboard Streamlit 📊

```bash
# Aller dans le dossier dashboard
cd dashboard

# Lancer le dashboard
streamlit run medical_dashboard.py
```

**Vérification :**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

Le navigateur s'ouvrira automatiquement sur `http://localhost:8501`

---

## 💻 Utilisation

### 1. Vérifier que Tout Fonctionne

**Test de santé du système :**
```bash
# Dans un nouveau terminal (depuis la racine)

# Test Load Balancer
curl http://localhost:5000/health

# Test Cloud Server
curl http://localhost:8070/health

# Test Fog Node 1
curl http://localhost:5001/health

# Test Fog Node 2
curl http://localhost:5002/health

# Test Fog Node 3
curl http://localhost:5003/health
```

**Réponse attendue (Load Balancer) :**
```json
{
  "status": "ok",
  "load_balancer": "online",
  "healthy_nodes": 3,
  "total_nodes": 3,
  "nodes": {
    "FOG-001": {
      "status": "healthy",
      "active_connections": 0,
      "specialty": "general"
    },
    "FOG-002": {
      "status": "healthy",
      "active_connections": 0,
      "specialty": "critical_care"
    },
    "FOG-003": {
      "status": "healthy",
      "active_connections": 0,
      "specialty": "pediatric"
    }
  }
}
```

---

### 2. Lancer le Simulateur IoT

**Terminal 7 :**
```bash
# Aller dans le dossier iot
cd iot

# Lancer le simulateur
python iot_simulator.py
```

**Menu interactif :**
```
═══════════════════════════════════════════════════════════
🏥 SIMULATEUR IoT MÉDICAL - ECG SIGNAL SENDER
═══════════════════════════════════════════════════════════

🔍 Vérification des services...
   ✅ Load Balancer: En ligne
   ✅ FOG-001: En ligne
   ✅ FOG-002: En ligne
   ✅ FOG-003: En ligne

Choisissez un scénario de test:

  1️⃣  Test Load Balancer (Routing Intelligent)
  2️⃣  Test Coopération (Alertes & Synchronisation)
  3️⃣  Test Direct (Chaque Fog Individuellement)
  4️⃣  Test de Charge (20 requêtes rapides)
  5️⃣  Simulation Réaliste (30 secondes continu)
  6️⃣  TOUT TESTER (Tous les scénarios)
  0️⃣  Quitter

👉 Votre choix:
```

#### Scénarios Disponibles

**1️⃣ Test Load Balancer**
- Teste le routing intelligent
- Vérifie que chaque fog reçoit les bons patients
- Exemple : cas critiques → FOG-002, cas normaux → FOG-003

**2️⃣ Test Coopération**
- Envoie des cas critiques
- Vérifie le partage d'alertes entre fogs
- Vérifie la synchronisation des données

**3️⃣ Test Direct**
- Envoie directement à chaque fog individuellement
- Teste toutes les méthodes de chaque fog

**4️⃣ Test de Charge**
- Envoie 20 requêtes rapidement
- Vérifie la performance du système
- Affiche les statistiques de répartition

**5️⃣ Simulation Réaliste**
- Flux continu pendant 30 secondes
- Distribution réaliste : 70% normal, 20% warning, 10% critical
- Simule un environnement hospitalier réel

**6️⃣ Tout Tester**
- Exécute tous les scénarios séquentiellement
- Test complet du système

---

### 3. Accéder au Dashboard

Ouvrir dans votre navigateur : **http://localhost:8501**

**Fonctionnalités du Dashboard :**

#### 📊 Vue d'ensemble
- Liste de tous les patients surveillés
- Statut en temps réel : Normal / Warning / Critical
- Signaux vitaux actuels

#### ❤️ Signaux Vitaux (par patient)
- **Fréquence cardiaque** : bpm avec indicateur d'alerte
- **Température** : °C avec détection de fièvre
- **Saturation O₂** : % SpO2
- **Tension artérielle** : mmHg

#### 🫀 Analyse ECG
- **Type de battement** : Classification IA
- **Confiance** : Pourcentage de certitude
- **Alerte générée** : Oui/Non
- **Total analyses** : Compteur d'historique

#### 📈 Historique Complet
- Bouton "Voir l'historique complet"
- Tableau avec toutes les analyses passées
- Graphique de confiance dans le temps
- Répartition des types de battements (pie chart)

#### 🚨 Alertes Actives
- Liste des alertes non acquittées
- Filtrage par patient
- Bouton d'acquittement
- Niveau de sévérité

#### ⚙️ État du Système
- Total prédictions effectuées
- Alertes actives
- Patients suivis
- Statut Cloud/Fog

---

## 🔧 Dépannage

### Problème : Cloud Server ne trouve pas firebase-credentials.json

**Erreur :**
```
❌ Erreur Firebase: Could not load credentials from ../firebase-credentials.json
```

**Solution :**
```bash
# Vérifier l'emplacement du fichier
ls firebase-credentials.json

# Le fichier DOIT être à la racine:
fog-computing-medical-system/
├── firebase-credentials.json  ← ICI
├── cloud/
│   └── cloud_server.py (utilise "../firebase-credentials.json")

# Si le fichier est ailleurs, le déplacer:
mv cloud/firebase-credentials.json ./firebase-credentials.json
```

---

### Problème : Fog Nodes ne trouvent pas le modèle

**Erreur :**
```
❌ [FOG-001] Erreur: ../models/ecg_cnn.h5 not found
```

**Solution :**
```bash
# 1. Vérifier que le modèle existe à la racine
ls models/ecg_cnn.h5

# 2. Si absent, entraîner le modèle:
python train_model.py

# 3. Vérifier que MODEL_PATH dans les fog nodes est correct:
# fog_node_1.py, fog_node_2.py, fog_node_3.py doivent avoir:
MODEL_PATH = "../models/ecg_cnn.h5"

# 4. Les fog nodes DOIVENT être lancés depuis /fog/:
cd fog
python fog_node_1.py  ✅
# PAS:
python fog/fog_node_1.py  ❌
```

---

### Problème : Dashboard ne se connecte pas au Cloud

**Erreur Streamlit :**
```
❌ Erreur de connexion au serveur
Assurez-vous que le serveur cloud est lancé
```

**Solution :**
```bash
# 1. Vérifier que le Cloud Server tourne
curl http://localhost:8070/health

# 2. Vérifier l'URL dans dashboard/medical_dashboard.py:
API_URL = "http://127.0.0.1:8070"

# 3. Relancer le Cloud Server si nécessaire:
cd cloud
python cloud_server.py
```

---

### Problème : Import Error - fog_cooperation

**Erreur :**
```
ModuleNotFoundError: No module named 'fog_cooperation'
```

**Solution :**
```bash
# Les fog nodes DOIVENT être lancés depuis le dossier /fog/
cd fog
python fog_node_1.py  ✅

# PAS depuis la racine:
python fog/fog_node_1.py  ❌
```

---

### Problème : Port déjà utilisé

**Erreur :**
```
OSError: [Errno 48] Address already in use
```

**Solution :**
```bash
# Trouver le processus utilisant le port (exemple: 5001)

# Windows:
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :5001
kill -9 <PID>
```

---

## 🚀 Scripts de Démarrage Rapide

### Script Bash (Linux/Mac)

Créer un fichier `start_system.sh` à la **racine** :

```bash
#!/bin/bash

echo "🏥 Démarrage du Système de Surveillance Médicale"
echo "================================================"

# Vérifier les fichiers nécessaires
if [ ! -f "firebase-credentials.json" ]; then
    echo "❌ Erreur: firebase-credentials.json non trouvé à la racine"
    exit 1
fi

if [ ! -f "models/ecg_cnn.h5" ]; then
    echo "❌ Erreur: models/ecg_cnn.h5 non trouvé"
    echo "💡 Lancez: python train_model.py"
    exit 1
fi

# Fonction pour lancer dans un nouveau terminal (Mac)
launch_terminal_mac() {
    osascript -e "tell app \"Terminal\" to do script \"cd '$(pwd)' && $1\""
}

# Fonction pour lancer dans un nouveau terminal (Linux avec gnome-terminal)
launch_terminal_linux() {
    gnome-terminal -- bash -c "cd '$(pwd)' && $1; exec bash"
}

# Détecter l'OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    LAUNCH_CMD="launch_terminal_mac"
else
    LAUNCH_CMD="launch_terminal_linux"
fi

# Activer l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo ""
echo "☁️  Lancement Cloud Server..."
$LAUNCH_CMD "cd cloud && python cloud_server.py"
sleep 3

echo "🌫️  Lancement Fog Node 1..."
$LAUNCH_CMD "cd fog && python fog_node_1.py"
sleep 2

echo "🌫️  Lancement Fog Node 2..."
$LAUNCH_CMD "cd fog && python fog_node_2.py"
sleep 2

echo "🌫️  Lancement Fog Node 3..."
$LAUNCH_CMD "cd fog && python fog_node_3.py"
sleep 2

echo "⚖️  Lancement Load Balancer..."
$LAUNCH_CMD "cd fog && python load_balancer.py"
sleep 2

echo "📊 Lancement Dashboard..."
$LAUNCH_CMD "cd dashboard && streamlit run medical_dashboard.py"

echo ""
echo "✅ Système démarré!"
echo "📊 Dashboard: http://localhost:8501"
echo ""
echo "Pour lancer le simulateur IoT:"
echo "  cd iot && python iot_simulator.py"
```

Utilisation :
```bash
chmod +x start_system.sh
./start_system.sh
```

---

### Script Batch (Windows)

Créer un fichier `start_system.bat` à la **racine** :

```batch
@echo off
echo 🏥 Démarrage du Système de Surveillance Médicale
echo ================================================

REM Vérifier les fichiers nécessaires
if not exist "firebase-credentials.json" (
    echo ❌ Erreur: firebase-credentials.json non trouvé à la racine
    pause
    exit /b 1
)

if not exist "models\ecg_cnn.h5" (
    echo ❌ Erreur: models\ecg_cnn.h5 non trouvé
    echo 💡 Lancez: python train_model.py
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
)

echo.
echo ☁️  Lancement Cloud Server...
start "Cloud Server" cmd /k "cd cloud && python cloud_server.py"
timeout /t 3

echo 🌫️  Lancement Fog Node 1...
start "Fog Node 1" cmd /k "cd fog && python fog_node_1.py"
timeout /t 2

echo 🌫️  Lancement Fog Node 2...
start "Fog Node 2" cmd /k "cd fog && python fog_node_2.py"
timeout /t 2

echo 🌫️  Lancement Fog Node 3...
start "Fog Node 3" cmd /k "cd fog && python fog_node_3.py"
timeout /t 2

echo ⚖️  Lancement Load Balancer...
start "Load Balancer" cmd /k "cd fog && python load_balancer.py"
timeout /t 2

echo 📊 Lancement Dashboard...
start "Dashboard" cmd /k "cd dashboard && streamlit run medical_dashboard.py"

echo.
echo ✅ Système démarré!
echo 📊 Dashboard: http://localhost:8501
echo.
echo Pour lancer le simulateur IoT:
echo   cd iot
echo   python iot_simulator.py
pause
```

Utilisation :
```batch
start_system.bat
```

---

## 📚 Résumé des Chemins Importants

### Fichiers à la Racine
- `firebase-credentials.json` ← Credentials Firebase
- `models/ecg_cnn.h5` ← Modèle CNN
- `train_model.py` ← Script d'entraînement
- `pip-requirements` ← Dépendances

### Chemins Relatifs dans le Code

**cloud_server.py** (dans `/cloud/`) :
```python
cred = credentials.Certificate("../firebase-credentials.json")
```

**fog_node_1.py, fog_node_2.py, fog_node_3.py** (dans /fog/) :
pythonMODEL_PATH = "../models/ecg_cnn.h5"

medical_dashboard.py (dans /dashboard/) :
pythonAPI_URL = "http://127.0.0.1:8070"  # Pointe vers cloud_server

iot_simulator.py (dans /iot/) :
pythonLOAD_BALANCER_URL = "http://localhost:5000/predict"
