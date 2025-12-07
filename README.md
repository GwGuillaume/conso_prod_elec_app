# 📈📊 Application Streamlit : Analyse de la consommation et de la production électrique 🔋

Cette application **Streamlit** permet d'analyser de manière interactive la **consommation électrique**
et la **production photovoltaïque** issue d'une installation solaire.  
Elle fusionne et visualise les données pour explorer les dynamiques **journalières, hebdomadaires et mensuelles**.

---

## 📂 Arborescence du projet

```yaml
.
├── app/
│ ├── main.py # Lancement de l’application en mode module
│ ├── main.py # Point d’entrée Streamlit
│ ├── core/ # Cœur logique de l’application
│ │ ├── config.py # Configuration globale et chemins
│ │ ├── data_manager.py # Gestion et fusion des données
│ │ ├── statistics.py # Calculs statistiques et agrégations
│ │ └── visualization.py # Fonctions de visualisation (Plotly)
│ └── ui/ # Interface graphique Streamlit
│ ├── layout.py # Disposition générale
│ ├── theme.py # Palette de couleurs et styles
│ └── widgets.py # Composants interactifs
│
├── common/ # Fonctions utilitaires partagées
│ ├── data_tools.py
│ ├── file_utils.py
│ ├── plot_tools.py
│ ├── token_manager.py
│ └── utils.py
│
├── conso_api_tools/ # Données de consommation (Enedis / Linky)
│ ├── api_client.py
│ ├── daily_update.py
│ ├── fetch_history.py
│ ├── conso/
│ │ ├── consumption_data_1h.csv
│ │ ├── consumption_data_30min.csv
│ │ └── raw_conso_files.zip
│ ├── merged/global.csv
│ └── init.py
│
├── prod_api_tools/ # Données de production (Hoymiles)
│ ├── api_client.py
│ ├── daily_update.py
│ ├── fetch_history.py
│ ├── token_refresh.py
│ └── prod/
│ ├── production_data.csv
│ └── raw_prod_files.zip
│
├── package.json # Dépendance Node.js pour Linky
├── requirements.txt # Dépendances Python
├── README.md # Documentation du projet
└── app.py # Ancienne version (compatible pour debug)
```

---

## 📄 Description de l'application

L’application permet de :
- Charger, nettoyer et fusionner les données de **consommation Linky** et de **production Hoymiles**
- Ajuster les pas horaires et combler les créneaux manquants
- Filtrer dynamiquement les périodes (jour, semaine, mois)
- Visualiser les courbes de **consommation**, **production** et **total**
- Calculer des **statistiques énergétiques** (totaux, moyennes, ratios)

L’application est aussi disponible en ligne :  
👉 [https://suivi-elec-app.streamlit.app](https://suivi-elec-app.streamlit.app)

---

## 📥 Données sources

- **Consommation électrique (EDF / Enedis)** :
  - Export depuis l’espace personnel EDF : [https://suiviconso.edf.fr/comprendre](https://suiviconso.edf.fr/comprendre)
  - Format : CSV à pas de 30 minutes

- **Production photovoltaïque (Hoymiles)** :
  - Export depuis : [https://global.hoymiles.com](https://global.hoymiles.com/website/plant/detail/156600/report)
  - Format : CSV à pas de 15 minutes

---

## ⚙️ Chronologie des traitements

1️⃣ **Chargement des données brutes** :
   - Nettoyage et harmonisation des CSV  
   - Standardisation de l’horodatage  

2️⃣ **Harmonisation temporelle** :
   - Recalage en pas de 15 ou 30 minutes  
   - Ajout des créneaux manquants  

3️⃣ **Fusion des jeux de données** :
   - Jointure sur la colonne `datetime`  
   - Ajout d’une colonne `total = consommation + production`  

4️⃣ **Visualisation interactive (Plotly)** :
   - Sélecteurs dynamiques de période  
   - Info-bulles et légendes interactives  

---

## 📊 Affichage graphique

- **Plotly** pour des courbes interactives  
- **Streamlit** pour l’interface utilisateur  
- Thème clair et responsive (`.streamlit/config.toml`)

---

## 🛠️ Installation

### 1️⃣ Cloner le dépôt

```bash
    git clone <url_du_repo>
    cd conso_prod_app
```

### 2️⃣ Créer un environnement virtuel

```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS / Linux
    .venv\Scripts\activate     # Windows
```

3️⃣ Installer les dépendances

```bash
    pip install -r requirements.txt
    npm install linky
```

## 🚀 Lancer l'application

### Méthode 1 — via Streamlit

```bash
    streamlit run app/main.py
```

### Méthode 2 — via Python

```bash
  python -m app
```

L’application s’ouvre sur http://localhost:8501

## 🔄 Téléchargement automatique des données

La mise à jour automatique des données se fait désormais via les modules situés dans les dossiers `prod_api_tools` et `conso_api_tools`.

- **Production (Hoymiles)** : `prod_api_tools/daily_update.py`

    → Ce script télécharge quotidiennement la production, met à jour `prod/prod_raw_files.zip` (archive des CSV journaliers renommés) et `prod/production_data.csv` (fichier consolidé).

- **Consommation (Linky / Enedis via linky / Conso API)** : `conso_api_tools/daily_update.py`

  → Ce script récupère la courbe 30 min (ou agrégée 1h selon configuration), met à jour `conso/raw_conso_files.zip` et `conso/consumption_data_30min.csv` / `consumption_data_1h.csv`.

### Exemples d'utilisation (local)

```bash
    # Mise à jour production : télécharge la veille et intègre
    python -m prod_api_tools.daily_update --mode local --action last
```

```bash
    # Backfill production à partir d'une date
    python -m prod_api_tools.daily_update --mode local --action backfill --start-date 2025-03-25
```

```bash
    # Mise à jour consommation (Linky) : télécharge la veille
    python -m conso_api_tools.daily_update --mode local --action last
```

## 🧮 Calculs et statistiques

Le module app/core/statistics.py permet :
- le calcul de la production et consommation totale sur une période
- la moyenne journalière ou horaire
- les ratios d’autoconsommation et de surplus

---

## 👤 Auteur
Développé par Gwenaël GUILLAUME

---
