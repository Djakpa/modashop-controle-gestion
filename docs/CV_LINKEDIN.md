# 💼 Mise en avant sur CV et LinkedIn

## 📄 Comment intégrer ce projet sur ton CV

### Format suggéré (section "Projets" du CV)

```
🛠️ ModaShop — Automatisation reporting contrôle de gestion (2026)
Conception et développement d'un pipeline complet d'automatisation
du reporting de clôture mensuelle d'une ETI e-commerce fictive (85 M€).

• Modélisation d'un data warehouse (modèle en étoile, 12 tables)
• Génération de 624 000 lignes de données synthétiques cohérentes (Python)
• 6 requêtes SQL d'analyse : P&L analytique, écarts budget/réel,
  décomposition prix/volume/mix, DSO, détection d'anomalies (Z-score)
• Dashboard interactif Streamlit en ligne

🔗 Démo : [https://ton-app.streamlit.app]
🔗 Code : [https://github.com/ton-username/modashop-controle-gestion]

Stack : SQL (DuckDB) | Python | Pandas | Streamlit | Plotly | Git
```

### Variante plus condensée (1 ligne)

```
📊 ModaShop — Reporting CDG automatisé (SQL + Python + Streamlit)
   ETI fictive 85 M€ | P&L analytique, écarts, DSO, détection d'anomalies
   🔗 Démo live : https://ton-app.streamlit.app
```

---

## 🚀 Post LinkedIn de lancement

Voici une proposition de **post LinkedIn** pour annoncer ton projet. Il est construit pour générer de l'engagement (hook, structure, CTA).

### Version 1 — Storytelling

```
🚀 J'ai automatisé un reporting de contrôle de gestion qui prenait 3 jours
sous Excel pour le faire tourner en 15 minutes. Voici comment.

Le constat : la clôture mensuelle est souvent un cauchemar.
→ Extraction manuelle depuis l'ERP
→ Retraitements Excel à n'en plus finir
→ Erreurs de copier-coller
→ Et au final, des analyses qui arrivent trop tard pour agir.

Alors j'ai conçu un projet de bout en bout pour automatiser tout ça.

🏢 Le terrain de jeu : ModaShop SAS, une ETI e-commerce fictive (85 M€ CA,
24 mois de données simulées sur 3 canaux et 4 catégories produits).

🛠️ Le pipeline :
1️⃣ Génération de 624 000 lignes de données synthétiques cohérentes (Python)
2️⃣ Modélisation d'un data warehouse (modèle en étoile, 12 tables)
3️⃣ 6 requêtes SQL d'analyse, dont :
   • Décomposition Prix / Volume / Mix de l'écart de CA
   • Calcul du DSO avec window functions
   • Détection automatique d'anomalies par Z-score
4️⃣ Dashboard Streamlit interactif déployé en ligne

🎯 Le clou du spectacle : j'ai volontairement injecté 5 anomalies dans les
données (explosion CAC marketing, surstockage, dégradation du DSO,
montée en gamme ratée, inflation logistique).
👉 L'algo les détecte automatiquement.

C'est exactement ce qu'on attend d'un Data Analyst en contrôle de gestion :
ne plus passer son temps à chercher les problèmes, mais à les RÉSOUDRE
une fois qu'ils sont remontés automatiquement.

🔗 Démo live : [lien Streamlit]
🔗 Code source : [lien GitHub]

#ControleDeGestion #DataAnalyst #SQL #Python #DataViz #Finance
```

### Version 2 — Plus technique

```
🦆 Mon nouveau projet portfolio : un pipeline complet de reporting
contrôle de gestion automatisé.

Stack : Python → DuckDB → SQL → Streamlit (déployé en ligne)

Au programme :
✅ Modélisation d'un data warehouse (étoile, 12 tables)
✅ 624 000 lignes de données synthétiques (NumPy vectorisé)
✅ Window functions SQL (moyenne mobile, Z-score, LAG)
✅ Décomposition Prix / Volume / Mix
✅ Dashboard interactif avec 5 onglets d'analyse

Et surtout : 5 anomalies injectées volontairement pour valider que le
système d'alertes les remonte bien automatiquement. Spoiler : ✅

🎯 Cas d'usage : remplacer un processus Excel de 3 jours par 15 minutes
de SQL + Python.

Démo live : [lien]
Code : [lien]

Toujours ouvert·e aux retours et discussions !

#DataAnalyst #ControleDeGestion #SQL #Python
```

---

## 💬 Réponses préparées aux questions probables

**"Pourquoi des données synthétiques et pas réelles ?"**
> Confidentialité absolue, contrôle total sur les anomalies à analyser, et la modélisation du business model est en soi une compétence valorisée. Le code de génération est dans le repo.

**"Pourquoi DuckDB plutôt que PostgreSQL ?"**
> DuckDB me permet d'avoir un dépôt 100% reproductible sans dépendre d'un serveur. Le SQL est très proche de PostgreSQL, tout est transférable.

**"Tu sais ce qu'est un effet mix ?"**
> Oui, c'est le 3e effet de la décomposition d'écart, qui capture les variations internes à un agrégat (ex : montée en gamme, changement de répartition entre sous-catégories). C'est typiquement ce qu'on voit sur les Accessoires de ModaShop : +30% sur les prix mais -11% sur les volumes.

---

## 🎯 Conseils additionnels

1. **Ajoute 2-3 captures d'écran** du dashboard dans le README → ça donne envie de cliquer
2. **Active GitHub Pages** ou **Vercel** pour avoir une URL custom propre
3. **Épingle le repo** sur ton profil GitHub
4. **Fais 4-5 posts** plutôt qu'un seul (à 1-2 semaines d'intervalle) pour maximiser la visibilité :
   - Post 1 : Présentation générale (proposé ci-dessus)
   - Post 2 : Focus sur la décomposition Prix/Volume/Mix (avec capture)
   - Post 3 : Focus sur la détection automatique d'anomalies
   - Post 4 : Behind the scenes (comment tu as généré les données)
   - Post 5 : Retours, leçons apprises
