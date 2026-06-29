"""
====================================================================
🦆 MODASHOP - DASHBOARD CONTRÔLE DE GESTION
====================================================================
Dashboard interactif de pilotage pour ModaShop SAS.
Données : 24 mois (2024-2025) - ETI e-commerce 85 M€

Lancement :
    streamlit run app.py
====================================================================
"""

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ====================================================================
# CONFIG
# ====================================================================

st.set_page_config(
    page_title="ModaShop - Dashboard CDG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).parent.parent / "modashop.duckdb"

# Génération automatique de la base au premier lancement (pour Streamlit Cloud)
if not DB_PATH.exists():
    import subprocess
    with st.spinner("🚀 Premier lancement - génération des données (~1 min)..."):
        root = Path(__file__).parent.parent
        subprocess.run(["python", str(root / "generate_modashop_data.py")], cwd=root, check=True)
        subprocess.run(["python", str(root / "load_duckdb.py")], cwd=root, check=True)
    st.rerun()


# ====================================================================
# CONNEXION CACHÉE (perf)
# ====================================================================

@st.cache_resource
def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(ttl=3600)
def run_query(sql: str) -> pd.DataFrame:
    return get_connection().execute(sql).df()


# ====================================================================
# SIDEBAR - FILTRES
# ====================================================================

st.sidebar.title("🎛️ Filtres")
annees = run_query("SELECT DISTINCT annee FROM v_ventes ORDER BY annee DESC")['annee'].tolist()
annee_choisie = st.sidebar.selectbox("Année", annees, index=0)

canaux_dispos = ['Tous'] + run_query("SELECT DISTINCT canal FROM v_ventes ORDER BY canal")['canal'].tolist()
canal_choisi = st.sidebar.selectbox("Canal", canaux_dispos)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "ℹ️ **À propos**\n\n"
    "Dashboard de pilotage du contrôle de gestion sur 24 mois "
    "(2024-2025). Données 100% synthétiques (~624k lignes) "
    "incluant 5 anomalies volontairement injectées pour rendre "
    "l'analyse réaliste."
)
st.sidebar.markdown("📂 [Code source GitHub](https://github.com/)")

# Filtre canal SQL
filtre_canal = "" if canal_choisi == "Tous" else f"AND canal = '{canal_choisi}'"

# ====================================================================
# HEADER
# ====================================================================

st.title("📊 ModaShop SAS - Pilotage Contrôle de Gestion")
st.markdown(
    f"**Période analysée :** Année {annee_choisie}  |  "
    f"**Canal :** {canal_choisi}  |  "
    f"**Source :** Données synthétiques ETI e-commerce"
)
st.markdown("---")


# ====================================================================
# KPIs PRINCIPAUX
# ====================================================================

kpis_query = f"""
    SELECT
        SUM(ca_ht)            AS ca,
        SUM(cout_achat_ht)    AS cout,
        SUM(marge_brute_ht)   AS marge,
        SUM(quantite)         AS qte
    FROM v_ventes
    WHERE annee = {annee_choisie} {filtre_canal}
"""
kpis = run_query(kpis_query).iloc[0]

# KPI N-1 pour comparaison
kpis_n_1_query = f"""
    SELECT SUM(ca_ht) AS ca, SUM(marge_brute_ht) AS marge
    FROM v_ventes
    WHERE annee = {annee_choisie - 1} {filtre_canal}
"""
kpis_n_1 = run_query(kpis_n_1_query).iloc[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    delta_ca = (kpis['ca'] - kpis_n_1['ca']) / kpis_n_1['ca'] * 100 if kpis_n_1['ca'] else 0
    st.metric(
        "💰 Chiffre d'affaires",
        f"{kpis['ca']/1e6:,.1f} M€",
        f"{delta_ca:+.1f}% vs N-1"
    )
with col2:
    delta_m = (kpis['marge'] - kpis_n_1['marge']) / kpis_n_1['marge'] * 100 if kpis_n_1['marge'] else 0
    st.metric(
        "📈 Marge brute",
        f"{kpis['marge']/1e6:,.1f} M€",
        f"{delta_m:+.1f}% vs N-1"
    )
with col3:
    taux_marge = kpis['marge'] / kpis['ca'] * 100 if kpis['ca'] else 0
    taux_marge_n_1 = kpis_n_1['marge'] / kpis_n_1['ca'] * 100 if kpis_n_1['ca'] else 0
    st.metric(
        "🎯 Taux de marge",
        f"{taux_marge:.1f}%",
        f"{taux_marge - taux_marge_n_1:+.1f} pts"
    )
with col4:
    st.metric(
        "📦 Articles vendus",
        f"{kpis['qte']:,.0f}".replace(",", " ")
    )

st.markdown("---")


# ====================================================================
# ONGLETS D'ANALYSE
# ====================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Évolution mensuelle",
    "🎯 Budget vs Réel",
    "🔍 Décomposition Prix/Volume/Mix",
    "💸 DSO & BFR",
    "🚨 Alertes auto"
])

# ────── TAB 1 : ÉVOLUTION MENSUELLE ──────────────────────────────────
with tab1:
    st.subheader("Évolution mensuelle du CA et de la marge")

    df_mens = run_query(f"""
        SELECT
            annee_mois,
            SUM(ca_ht)/1e6           AS ca_m_euros,
            SUM(marge_brute_ht)/1e6  AS marge_m_euros,
            ROUND(SUM(marge_brute_ht)/SUM(ca_ht)*100, 1) AS taux_marge_pc
        FROM v_ventes
        WHERE annee = {annee_choisie} {filtre_canal}
        GROUP BY annee_mois
        ORDER BY annee_mois
    """)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_mens['annee_mois'], y=df_mens['ca_m_euros'],
        name='CA (M€)', marker_color='#3B82F6'
    ))
    fig.add_trace(go.Scatter(
        x=df_mens['annee_mois'], y=df_mens['marge_m_euros'],
        name='Marge (M€)', mode='lines+markers',
        line=dict(color='#10B981', width=3), yaxis='y'
    ))
    fig.add_trace(go.Scatter(
        x=df_mens['annee_mois'], y=df_mens['taux_marge_pc'],
        name='Taux marge (%)', mode='lines+markers',
        line=dict(color='#F59E0B', width=2, dash='dot'), yaxis='y2'
    ))
    fig.update_layout(
        height=450,
        yaxis=dict(title="Montant (M€)"),
        yaxis2=dict(title="Taux marge (%)", overlaying='y', side='right'),
        hovermode='x unified',
        legend=dict(orientation='h', y=-0.2),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Voir le détail mensuel"):
        st.dataframe(df_mens, use_container_width=True, hide_index=True)

    st.subheader("Répartition du CA par catégorie")
    df_cat = run_query(f"""
        SELECT categorie, SUM(ca_ht)/1e6 AS ca_m_euros
        FROM v_ventes
        WHERE annee = {annee_choisie} {filtre_canal}
        GROUP BY categorie
        ORDER BY ca_m_euros DESC
    """)
    fig_cat = px.pie(
        df_cat, values='ca_m_euros', names='categorie',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_cat.update_traces(textposition='inside', textinfo='percent+label')
    fig_cat.update_layout(height=400)
    st.plotly_chart(fig_cat, use_container_width=True)


# ────── TAB 2 : BUDGET VS RÉEL ───────────────────────────────────────
with tab2:
    st.subheader(f"Analyse d'écarts Budget vs Réel - {annee_choisie}")
    if annee_choisie != 2025:
        st.info("ℹ️ Le budget n'est disponible que pour 2025.")
    else:
        df_ecart = run_query(f"""
            WITH realise AS (
                SELECT mois, canal, categorie,
                       SUM(ca_ht) AS ca_reel,
                       SUM(marge_brute_ht) AS marge_reel
                FROM v_ventes
                WHERE annee = 2025 {filtre_canal}
                GROUP BY mois, canal, categorie
            ),
            budget AS (
                SELECT b.mois, c.canal, cat.categorie,
                       b.montant_budget AS ca_budget,
                       b.montant_budget * b.marge_budget_pc AS marge_budget
                FROM fact_budget b
                LEFT JOIN dim_canal c ON b.canal_id = c.canal_id
                LEFT JOIN dim_categorie cat ON b.categorie_id = cat.categorie_id
                WHERE b.type = 'CA' AND b.annee = 2025
            )
            SELECT
                r.mois,
                SUM(b.ca_budget)/1e6 AS ca_budget_m,
                SUM(r.ca_reel)/1e6   AS ca_reel_m,
                SUM(r.ca_reel - b.ca_budget)/1e6 AS ecart_m,
                ROUND(SUM(r.ca_reel - b.ca_budget) / NULLIF(SUM(b.ca_budget), 0) * 100, 1) AS ecart_pc
            FROM realise r
            LEFT JOIN budget b ON r.mois=b.mois AND r.canal=b.canal AND r.categorie=b.categorie
            GROUP BY r.mois
            ORDER BY r.mois
        """)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_ecart['mois'], y=df_ecart['ca_budget_m'],
            name='Budget', marker_color='#94A3B8'
        ))
        fig.add_trace(go.Bar(
            x=df_ecart['mois'], y=df_ecart['ca_reel_m'],
            name='Réel',
            marker_color=['#10B981' if e >= 0 else '#EF4444' for e in df_ecart['ecart_m']]
        ))
        fig.update_layout(
            height=400, barmode='group',
            xaxis=dict(title="Mois", dtick=1),
            yaxis=dict(title="CA (M€)"),
            hovermode='x unified',
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📋 Détail des écarts par mois")
        st.dataframe(
            df_ecart.style.format({
                'ca_budget_m': '{:.2f} M€',
                'ca_reel_m':   '{:.2f} M€',
                'ecart_m':     '{:+.2f} M€',
                'ecart_pc':    '{:+.1f}%',
            }).background_gradient(subset=['ecart_pc'], cmap='RdYlGn', vmin=-15, vmax=15),
            use_container_width=True, hide_index=True
        )


# ────── TAB 3 : DÉCOMPOSITION PRIX/VOLUME/MIX ────────────────────────
with tab3:
    st.subheader("Décomposition de l'écart de CA (N vs N-1) par catégorie")
    st.markdown(
        "🧠 **Méthode** : décomposition classique du contrôle de gestion. "
        "L'écart total se décompose en 3 effets : **prix**, **volume** et **mix**."
    )

    df_pvm = run_query("""
        WITH ventes_par_annee AS (
            SELECT annee, categorie,
                   SUM(quantite) AS qte,
                   SUM(ca_ht) AS ca,
                   SUM(ca_ht) / NULLIF(SUM(quantite), 0) AS prix_moyen
            FROM v_ventes GROUP BY annee, categorie
        ),
        pivot_annees AS (
            SELECT n.categorie,
                   n.qte AS qte_n, n_1.qte AS qte_n_1,
                   n.prix_moyen AS prix_n, n_1.prix_moyen AS prix_n_1,
                   n.ca AS ca_n, n_1.ca AS ca_n_1
            FROM ventes_par_annee n
            JOIN ventes_par_annee n_1
              ON n.categorie = n_1.categorie
             AND n.annee = 2025 AND n_1.annee = 2024
        )
        SELECT categorie,
               ROUND(ca_n_1/1e6, 2) AS ca_n_1_m,
               ROUND(ca_n/1e6, 2) AS ca_n_m,
               ROUND((ca_n - ca_n_1)/1e6, 2) AS ecart_total_m,
               ROUND((qte_n - qte_n_1) * prix_n_1 / 1e6, 2) AS effet_volume_m,
               ROUND((prix_n - prix_n_1) * qte_n / 1e6, 2) AS effet_prix_m,
               ROUND(((ca_n - ca_n_1) - ((qte_n - qte_n_1) * prix_n_1) - ((prix_n - prix_n_1) * qte_n))/1e6, 2) AS effet_mix_m,
               ROUND((ca_n - ca_n_1) / NULLIF(ca_n_1, 0) * 100, 1) AS croissance_pc,
               ROUND((prix_n - prix_n_1) / NULLIF(prix_n_1, 0) * 100, 1) AS evol_prix_pc,
               ROUND((qte_n - qte_n_1) / NULLIF(qte_n_1, 0) * 100, 1) AS evol_volume_pc
        FROM pivot_annees ORDER BY ABS(ca_n - ca_n_1) DESC
    """)

    # Waterfall par catégorie
    fig = go.Figure()
    for _, row in df_pvm.iterrows():
        fig.add_trace(go.Bar(
            name=row['categorie'],
            x=['Effet Volume', 'Effet Prix', 'Effet Mix'],
            y=[row['effet_volume_m'], row['effet_prix_m'], row['effet_mix_m']],
        ))
    fig.update_layout(
        height=400, barmode='group',
        yaxis=dict(title="Impact sur le CA (M€)"),
        title="Contribution de chaque effet par catégorie"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df_pvm.style.format({
            'ca_n_1_m':       '{:.2f} M€',
            'ca_n_m':         '{:.2f} M€',
            'ecart_total_m':  '{:+.2f} M€',
            'effet_volume_m': '{:+.2f} M€',
            'effet_prix_m':   '{:+.2f} M€',
            'effet_mix_m':    '{:+.2f} M€',
            'croissance_pc':  '{:+.1f}%',
            'evol_prix_pc':   '{:+.1f}%',
            'evol_volume_pc': '{:+.1f}%',
        }),
        use_container_width=True, hide_index=True
    )

    st.success(
        "💡 **Insight détecté** : la catégorie **Accessoires** présente un effet prix très positif (~+30%) "
        "compensé par un effet volume négatif (~-11%) → signature classique d'une **montée en gamme mal calibrée**."
    )


# ────── TAB 4 : DSO ──────────────────────────────────────────────────
with tab4:
    st.subheader("Évolution du DSO (Days Sales Outstanding) par canal")
    st.markdown(
        "💡 Le DSO mesure le délai moyen d'encaissement client. "
        "Une dégradation impacte directement le BFR et la trésorerie."
    )

    df_dso = run_query("""
        SELECT annee_mois, canal, ROUND(AVG(delai_jours), 1) AS dso_jours
        FROM v_encaissements
        WHERE annee_mois IS NOT NULL
        GROUP BY annee_mois, canal
        ORDER BY annee_mois, canal
    """)

    fig = px.line(
        df_dso, x='annee_mois', y='dso_jours', color='canal',
        markers=True,
        labels={'annee_mois': 'Mois', 'dso_jours': 'DSO (jours)'},
        color_discrete_map={'Web': '#3B82F6', 'Marketplace': '#EF4444', 'Boutique': '#10B981'}
    )
    # Annotation visuelle de l'anomalie (méthode robuste : shape + annotation)
    fig.add_shape(
        type="line", xref="x", yref="paper",
        x0="2025-04", x1="2025-04", y0=0, y1=1,
        line=dict(color="red", width=2, dash="dash"),
    )
    fig.add_annotation(
        x="2025-04", y=1, yref="paper", xref="x",
        text="⚠️ Anomalie #3 détectée", showarrow=False,
        yshift=10, font=dict(color="red", size=12),
    )
    fig.update_layout(height=450, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    st.error(
        "🚨 **Anomalie détectée** : à partir d'avril 2025, le DSO marketplaces passe brutalement de **45 à 60 jours** "
        "(+15 jours). Impact estimé sur le BFR à isoler et à remonter à la direction."
    )


# ────── TAB 5 : ALERTES AUTO ─────────────────────────────────────────
with tab5:
    st.subheader("🚨 Détection automatique des dérives sur les charges")
    st.markdown(
        "📊 **Méthode** : pour chaque ligne de charge mensuelle, on calcule le **Z-score** (nombre d'écarts-types) "
        "vs la moyenne des 12 mois précédents. Tout point au-delà de ±2σ est flaggé."
    )

    df_alertes = run_query("""
        WITH charges_mensuelles AS (
            SELECT strftime(date_charge, '%Y-%m') AS annee_mois,
                   cc_id, nature_charge, SUM(montant_ht) AS montant_mois
            FROM fact_charges
            GROUP BY annee_mois, cc_id, nature_charge
        ),
        charges_stats AS (
            SELECT annee_mois, cc_id, nature_charge, montant_mois,
                   AVG(montant_mois) OVER (
                       PARTITION BY cc_id, nature_charge ORDER BY annee_mois
                       ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) AS moyenne_12m,
                   STDDEV(montant_mois) OVER (
                       PARTITION BY cc_id, nature_charge ORDER BY annee_mois
                       ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) AS ecart_type_12m
            FROM charges_mensuelles
        )
        SELECT annee_mois, cc.centre_cout, nature_charge,
               ROUND(montant_mois, 0) AS montant,
               ROUND(moyenne_12m, 0) AS moyenne_ref,
               ROUND((montant_mois - moyenne_12m) / NULLIF(moyenne_12m, 0) * 100, 1) AS ecart_pc,
               ROUND((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0), 2) AS z_score
        FROM charges_stats cs
        LEFT JOIN dim_centre_cout cc USING (cc_id)
        WHERE moyenne_12m IS NOT NULL
          AND ABS((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0)) > 2
        ORDER BY annee_mois DESC, ABS(z_score) DESC
        LIMIT 15
    """)

    st.dataframe(
        df_alertes.style.format({
            'montant':     '{:,.0f} €',
            'moyenne_ref': '{:,.0f} €',
            'ecart_pc':    '{:+.1f}%',
            'z_score':     '{:+.2f}σ',
        }).background_gradient(subset=['z_score'], cmap='RdYlGn_r', vmin=-3, vmax=3),
        use_container_width=True, hide_index=True
    )

    st.warning(
        "⚠️ **Insight** : la nature **Marketing Marketplaces** ressort plusieurs fois en alerte sur Q2 2025. "
        "Le surcoût budgétaire mérite une investigation : explosion du CAC ou changement de stratégie média ?"
    )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray; font-size:0.9em;'>"
    "Dashboard CDG ModaShop — Projet portfolio — Données 100% synthétiques"
    "</div>",
    unsafe_allow_html=True
)
