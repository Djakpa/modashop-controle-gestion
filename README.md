# 📊 ModaShop — Automatisation du Reporting de Contrôle de Gestion

> **Projet portfolio Data Analyst / Contrôle de Gestion**
> Pipeline complet de production d'un reporting de clôture mensuelle automatisé, avec détection d'anomalies et dashboard interactif.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![SQL](https://img.shields.io/badge/SQL-DuckDB-yellow.svg)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Le pitch

> *"J'ai automatisé un processus de clôture mensuelle qui prenait 3 jours sous Excel et qui sort désormais en 15 minutes, avec un dashboard de pilotage P&L automatisé et une détection d'anomalies par Z-score."*

Ce projet simule de bout en bout le rôle d'un **Data Analyst en contrôle de gestion** au sein d'une ETI e-commerce fictive (**ModaShop SAS**, CA ~85 M€). Il couvre la chaîne complète : modélisation du business, génération de données, ETL, requêtes SQL d'analyse, dashboard interactif.

🔗 **[Voir le dashboard live →](https://your-app.streamlit.app)** _(à mettre à jour après déploiement)_

---

## 🏢 Contexte métier

**ModaShop SAS** est une ETI pure player e-commerce de mode (~310 personnes, 85 M€ de CA cible) :
- **3 canaux de vente** : Site web propre, marketplaces (Amazon/Zalando), 3 boutiques flagship
- **4 catégories** : PAP Femme, PAP Homme, Accessoires, Chaussures
- **Données simulées** : 24 mois (2024-2025), ~624 000 lignes de ventes

### 🎯 Les 5 problématiques à détecter

Pour rendre l'analyse réaliste, **5 anomalies ont été volontairement injectées** dans les données :

| # | Anomalie | Période | Détectée par |
|---|----------|---------|--------------|
| 1 | Explosion CAC marketing marketplaces (+40%) | Q2 2025 | Z-score sur charges |
| 2 | Surstock PAP Femme → démarques | Septembre 2025 | Analyse marge mensuelle |
| 3 | Dégradation DSO marketplaces (45j → 60j) | Avril 2025 | Window function sur encaissements |
| 4 | Effet mix accessoires (montée en gamme ratée) | Année 2025 | Décomposition prix/volume/mix |
| 5 | Inflation logistique (+15% sur transport) | Juin 2025 | Analyse coûts d'achat |

L'algorithme **détecte automatiquement** ces dérives — c'est précisément l'intérêt d'un système de reporting automatisé.

---

## 🛠️ Stack technique

| Couche | Outil | Pourquoi ce choix |
|--------|-------|-------------------|
| **Données** | Python + Pandas + NumPy | Génération de données synthétiques cohérentes |
| **Stockage** | DuckDB | Base SQL embarquée, ultra rapide, zéro infra |
| **Transformation** | SQL pur (CTE, window functions) | Standard métier, transférable PostgreSQL/Snowflake |
| **Visualisation** | Streamlit + Plotly | Dashboard web interactif, déployable gratuitement |
| **Versioning** | Git / GitHub | Bonnes pratiques de delivery |

---

## 📊 Aperçu du dashboard

Le dashboard contient **5 onglets** d'analyse :

1. 📅 **Évolution mensuelle** — CA, marge, mix catégorie
2. 🎯 **Budget vs Réel** — Analyse d'écarts mois par mois avec heatmap
3. 🔍 **Décomposition Prix/Volume/Mix** — _la requête signature du contrôle de gestion_
4. 💸 **DSO & BFR** — Suivi du délai d'encaissement avec détection d'anomalies
5. 🚨 **Alertes auto** — Détection statistique des dérives sur les charges

### Screenshots

> _Ajoute ici 2-3 captures d'écran de ton dashboard une fois lancé en local_
> _Suggestion : `docs/screenshot_dashboard_1.png`, `docs/screenshot_dashboard_2.png`_

---

## 🚀 Lancer le projet en local

### Prérequis

- Python 3.10+
- Git

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/<ton-username>/modashop-controle-gestion.git
cd modashop-controle-gestion

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Générer les données synthétiques (~1 min)
python generate_modashop_data.py

# 4. Charger les données dans DuckDB (~5 sec)
python load_duckdb.py

# 5. Lancer le dashboard
streamlit run streamlit_app/app.py
```

Le dashboard s'ouvre automatiquement dans ton navigateur à l'adresse `http://localhost:8501`.

---

## 📁 Structure du projet

```
modashop-controle-gestion/
├── 📄 README.md                       ← Ce fichier
├── 📄 requirements.txt                ← Dépendances Python
├── 🐍 generate_modashop_data.py       ← Génération des données synthétiques
├── 🐍 load_duckdb.py                  ← ETL : CSV → DuckDB
├── 📂 sql/                            ← Requêtes SQL d'analyse (6 fichiers commentés)
│   ├── 01_pnl_mensuel.sql
│   ├── 02_ecarts_budget_reel.sql
│   ├── 03_decomposition_prix_volume_mix.sql
│   ├── 04_dso_window_functions.sql
│   ├── 05_detection_anomalies.sql
│   └── 06_vue_dashboard.sql
├── 📂 streamlit_app/                  ← Application dashboard
│   └── app.py
├── 📂 modashop_data/                  ← Données CSV générées
└── 📂 docs/                           ← Captures d'écran, schémas
```

---

## 🔍 Focus sur les requêtes SQL clés

### Modèle en étoile (schéma)

```
                    ┌──────────────┐
                    │  dim_date    │
                    └──────┬───────┘
        ┌──────────┐       │       ┌──────────────┐
        │ dim_canal├───┐   │   ┌───┤  dim_produit │
        └──────────┘   ▼   ▼   ▼   └──────────────┘
                  ┌─────────────────┐
                  │   fact_ventes   │
                  └─────────────────┘
                       ▲   ▲   ▲
        ┌──────────┐   │   │   │   ┌──────────────┐
        │dim_client├───┘   │   └───┤dim_categorie │
        └──────────┘       │       └──────────────┘
                           ▼
              (+ fact_achats, fact_encaissements,
                 fact_charges, fact_paie, fact_budget)
```

### Exemple : décomposition Prix / Volume / Mix

C'est **la requête signature** du contrôle de gestion. Elle décompose l'écart de CA entre 2 années en 3 effets explicatifs :

```sql
SELECT categorie,
       -- Effet Volume = (Qté N - Qté N-1) × Prix moyen N-1
       (qte_n - qte_n_1) * prix_n_1            AS effet_volume,
       -- Effet Prix = (Prix N - Prix N-1) × Qté N
       (prix_n - prix_n_1) * qte_n             AS effet_prix,
       -- Effet Mix = résiduel
       (ca_n - ca_n_1)
         - ((qte_n - qte_n_1) * prix_n_1)
         - ((prix_n - prix_n_1) * qte_n)       AS effet_mix
FROM ventes_pivot;
```

**Résultat sur ModaShop** : la catégorie *Accessoires* affiche un effet prix très positif (+30%) compensé par un effet volume très négatif (-11%) → signature classique d'une montée en gamme mal calibrée. **Insight actionnable détecté en 1 requête.**

---

## 💡 Compétences mises en oeuvre

### SQL avancé
- **CTE** (Common Table Expressions) pour structurer les analyses complexes
- **Window functions** (`AVG OVER`, `LAG`, `STDDEV OVER`) pour les moyennes mobiles, comparaisons N-1, détection d'anomalies
- **Vues** matérialisées pour la performance et la maintenabilité
- Modélisation **étoile** (schéma data warehouse)

### Contrôle de gestion
- Construction d'un **P&L analytique** (canal × catégorie × CC)
- **Analyse d'écarts** budget vs réel
- **Décomposition Prix / Volume / Mix**
- Calcul du **DSO** et impact BFR
- **Détection statistique d'anomalies** (Z-score)

### Data & dataviz
- Génération de **données synthétiques** cohérentes (NumPy, vectorisation)
- ETL avec **pandas** et **DuckDB**
- Dashboard interactif **Streamlit** avec graphiques **Plotly**

---

## 📈 Pistes d'amélioration

- [ ] Orchestration avec **Airflow** ou **Prefect**
- [ ] Tests automatisés avec **pytest** (cohérence des chiffres)
- [ ] CI/CD via GitHub Actions
- [ ] Versionning des modèles avec **dbt**
- [ ] Export PowerPoint automatisé du reporting mensuel

---

## 👤 À propos

**[Ton Prénom Nom]**
📊 [Profil LinkedIn](https://www.linkedin.com/in/ton-profil)
✉️ ton.email@example.com

> _Projet réalisé dans le cadre de mon parcours vers un poste de Data Analyst spécialisé en contrôle de gestion. Données 100% synthétiques générées à des fins de démonstration technique — aucune information réelle d'entreprise._

---

## 📜 Licence

MIT License — libre de réutilisation à des fins d'apprentissage.
