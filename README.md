# 📈📊 Application Streamlit : Analyse de la consommation et de la production électrique 🔋

Cette application Streamlit permet d'analyser de manière interactive la consommation électrique 
et la production photovoltaïque issue d'une installation solaire. Elle fusionne et visualise 
les données pour explorer les dynamiques journalières et horaires.

## 📂 Arborescence du projet

```
conso_prod_app/
│
├── app.py                    # Point d'entrée Streamlit
├── README.md                 # Documentation de l'application
├── requirements.txt          # Dépendances Python
│
├── data/                     # Données brutes et nettoyées
│   ├── conso/                # Fichiers de consommation (EDF)
│   └── prod/                 # Fichiers de production (Hoymiles)
│
├── data_tools.py             # Transformations et manipulations de données
├── files_tools.py            # Traitement des fichiers bruts CSV
└── plot_tools.py             # Fonctions de visualisation interactive
└── requirements.txt          # Dépendances (Streamlit, pandas, etc.)
```

## 📄 Description de l'application

L'application permet de :
- Nettoyer et harmoniser les données de consommation et de production
- Ajuster les créneaux horaires (pas de 15 ou 30 minutes)
- Filtrer les périodes à visualiser (date et heure de début/fin)
- Visualiser les courbes de consommation, de production, et leur somme

L'application en ligne associée au dépôt github est accessible depuis le lien suivant : https://suivi-elec-app.streamlit.app/.

## 📥 Données sources

- **Consommation électrique** : export depuis l'espace personnel EDF
  - URL : [https://suiviconso.edf.fr/comprendre](https://suiviconso.edf.fr/comprendre)
  - Format : CSV avec un pas temporel de 30 min

- **Production photovoltaïque** : export du site Hoymiles
  - URL : [https://global.hoymiles.com](https://global.hoymiles.com/website/plant/detail/156600/report)
  - Format : CSV avec un pas temporel de 15 min

## ⚙️ Chronologie des traitements

1. **Chargement des données brutes** via `files_tools.py` :
   - Nettoyage du fichier CSV de consommation EDF horodatés par pas de 30 min (suppression des lignes inutiles, 
     standardisation de l'horodatage)
   - Fusion des fichiers CSV Hoymiles journaliers horodatés par pas de 15 min

2. **Harmonisation temporelle** des données brutes grâce à `data_tools.py` :
   - Ajout des créneaux manquants (NaN si absent)
   - Reformatage en pas de 15 min (dédoublement des données de consommation)

3. **Fusion des données** sur la colonne `datetime` :
   - Inner join entre consommation et production
   - Calcul d'une colonne "total" : consommation + production

4. **Affichage graphique interactif** via `plot_tools.py` et `Streamlit` :
   - Tracé des courbes interactives avec Plotly
   - Sélecteurs de période (date + heure de début/fin)

## 📊 Affichage graphique interactif

- Utilisation de **Plotly** pour l'affichage des courbes (consommation, production, total)
- Intégration des info-bulles en survol du graphique
- Filtrage par période via l'interface `Streamlit` (date et heure)

## 🛠️ Dépendances Python (requirements.txt)

Exemple de contenu du fichier `requirements.txt` :

```
pandas==2.2.3
plotly==6.0.1
streamlit==1.44.1
```

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone <url_du_repo>
cd conso_prod_app
```

### 2. Créer et activer un environnement virtuel

#### Créer l’environnement virtuel

```bash
python -m venv .venv
```

#### Activer l’environnement

- Sous Windows :

```bash
.venv\Scripts\activate
```

- Sous macOS / Linux :

```bash
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer l’application

```bash
streamlit run app.py
```


## 🚀 Lancer l'application

Depuis le dossier racine `conso_prod_app`, lancer la commande suivante :

```bash
streamlit run app.py
```

L'application se lance dans le navigateur par défaut, sur `localhost:8501` par défaut.

---