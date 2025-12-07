# ⚙️ Workflows GitHub Actions — Mise à jour des données

Ce dossier contient l’ensemble des workflows automatisés permettant la mise à jour des données **de consommation (Enedis)** et **de production (Hoymiles)**.

---

## 📊 Vue d’ensemble

| Type d’exécution | Source | Fichier | Description |
|------------------|---------|----------|--------------|
| 🕗 **Quotidien** | Enedis | `consumption_daily_update.yml` | Télécharge les données de consommation de la **veille** (intervalle 1h et 30min). |
| 🗓️ **Hebdomadaire** | Enedis | `consumption_weekly_update.yml` | Vérifie et complète **tout l’historique manquant** de consommation depuis `START_DATE`. |
| 🕗 **Quotidien** | Hoymiles | `production_daily_update.yml` | Télécharge les données de production solaire de la **veille**. |
| 🗓️ **Hebdomadaire** | Hoymiles | `production_weekly_update.yml` | Met à jour **l’ensemble de l’historique** de production. |
| ⏳ **Manuel**     | Enedis   | `consumption_full_download.yml` | Télécharge **toutes les données manquantes** de consommation depuis `START_DATE`.       |
| ⏳ **Manuel**     | Hoymiles | `production_full_download.yml`  | Télécharge **toutes les données manquantes** de production depuis `DEFAULT_START_DATE`. |

---

## 🧠 Fonctionnement général

Chaque workflow :
1. Clone le dépôt (`checkout`)
2. Installe Python et les dépendances
3. Exécute le script correspondant
4. Met à jour les fichiers CSV et ZIP (`data/conso/` ou `data/prod/`)
5. Fait un commit automatique uniquement si des changements sont détectés

---

## 🔐 Variables d’environnement

Les tokens et identifiants sensibles sont stockés dans **GitHub Secrets** :

| Variable | Utilisé par | Description |
|-----------|--------------|--------------|
| `ENEDIS_TOKEN` | Workflows *consommation* | Jeton d’accès à l’API Enedis via conso.boris.sh |
| `PRM` | Workflows *consommation* | Numéro PRM du compteur électrique |
| *(aucune variable nécessaire)* | Workflows *production* | L’authentification Hoymiles se fait via les fichiers locaux du projet |

---

## 🕒 Horaires planifiés

| Workflow | Heure UTC | Heure France (hiver) | Heure France (été) |
|-----------|------------|----------------------|--------------------|
| `production_daily_update.yml` | 06h15 | 07h15 | 08h15 |
| `consumption_daily_update.yml` | 08h34 | 09h34 | 10h34 |
| `production_weekly_update.yml` | 06h00 (lundi) | 07h00 | 08h00 |
| `consumption_weekly_update.yml` | 07h30 (lundi) | 08h30 | 09h30 |

> ⚠️ Les horaires ont été choisis pour éviter la surcharge API côté Enedis (fenêtre recommandée 6h–10h).

---

## 🧩 Scripts appelés

| Fichier Python | Dossier | Rôle principal |
|----------------|----------|----------------|
| `daily_update.py` | `conso_api_tools/` | Télécharge les données de la veille |
| `fetch_history.py` | `conso_api_tools/` | Télécharge tout l’historique manquant |
| `daily_update.py` | `prod_api_tools/` | Télécharge la production de la veille |
| `manage_production_data.py` | racine | Met à jour l’historique de production complet |

---

## 🚀 Déclenchement manuel

Tous les workflows peuvent être exécutés manuellement via :
**GitHub → Actions → Sélectionner le workflow → "Run workflow"**

Les workflows Full Download permettent de récupérer toutes les données manquantes et ne sont déclenchables que manuellement via GitHub Actions → "Run workflow".

---

## 🧹 Bonnes pratiques

- Ne pas modifier directement les CSV dans `data/` : laissez les scripts les régénérer.
- Si vous changez la structure du projet, mettez à jour les chemins dans les fichiers YAML.
- Pour déboguer localement, exécutez simplement :

```bash
  python conso_api_tools/daily_update.py
```
ou
```bash
  python prod_api_tools/daily_update.py
```
