# 🚀 Guide de déploiement — Mettre le dashboard en ligne (gratuit)

Pour avoir un **lien live cliquable** sur ton CV, il faut déployer l'app Streamlit sur **Streamlit Community Cloud** (gratuit).

## Étape 1 — Pousser le code sur GitHub

1. Crée un nouveau repo sur GitHub (suggestion de nom : `modashop-controle-gestion`)
2. Public, sans README (on a déjà le nôtre)
3. Suis les instructions de GitHub pour pousser le code :

```bash
cd modashop_project
git init
git add .
git commit -m "Initial commit - Projet ModaShop"
git branch -M main
git remote add origin https://github.com/TON-USERNAME/modashop-controle-gestion.git
git push -u origin main
```

⚠️ **Important** : le fichier `modashop.duckdb` est dans `.gitignore` (trop volumineux). Streamlit Cloud va le **regénérer automatiquement** grâce aux scripts.

## Étape 2 — Créer un compte Streamlit Cloud

1. Va sur https://streamlit.io/cloud
2. Clique sur "Sign up" puis connecte-toi **avec ton compte GitHub**
3. C'est gratuit, ça prend 30 secondes

## Étape 3 — Déployer l'app

1. Une fois connectée, clique sur **"New app"** en haut à droite
2. Remplis :
   - **Repository** : `TON-USERNAME/modashop-controle-gestion`
   - **Branch** : `main`
   - **Main file path** : `streamlit_app/app.py`
3. Clique sur **"Advanced settings"** → Python version : **3.11**
4. Clique sur **"Deploy!"**

## Étape 4 — Configurer le script de génération au démarrage

⚠️ Comme le fichier `.duckdb` n'est pas dans Git, il faut le créer au lancement. Crée un fichier `streamlit_app/setup.sh` dans ton repo avec :

```bash
#!/bin/bash
python generate_modashop_data.py
python load_duckdb.py
```

OU plus simple : ajoute au tout début de `app.py` une vérification :

```python
import os
from pathlib import Path

# Setup automatique au premier lancement
db_path = Path(__file__).parent.parent / "modashop.duckdb"
if not db_path.exists():
    import subprocess
    with st.spinner("Premier lancement - génération des données (~1 min)..."):
        root = Path(__file__).parent.parent
        subprocess.run(["python", str(root / "generate_modashop_data.py")], cwd=root, check=True)
        subprocess.run(["python", str(root / "load_duckdb.py")], cwd=root, check=True)
```

## Étape 5 — Récupérer ton lien

Au bout de 2-3 minutes, tu auras une URL du type :
```
https://modashop-controle-gestion-TON-USERNAME.streamlit.app
```

🎉 **C'est ce lien que tu mettras sur ton CV.**

---

## 🆘 Si tu bloques

- **L'app ne se lance pas** : vérifie les logs dans Streamlit Cloud (bouton "Manage app" en bas à droite)
- **"Module not found"** : assure-toi que `requirements.txt` est à la racine de ton repo
- **"DuckDB file not found"** : le setup automatique du point 4 n'est pas en place

## 🎁 Bonus : domaine custom (optionnel)

Tu peux personnaliser l'URL via les settings du dashboard Streamlit Cloud :
- `https://modashop.streamlit.app` (si dispo)
- ou un sous-domaine plus court
