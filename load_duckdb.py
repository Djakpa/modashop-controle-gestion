"""
====================================================================
CHARGEMENT DES DONNÉES MODASHOP DANS DUCKDB
====================================================================
Ce script :
  1. Crée une base DuckDB (fichier .duckdb)
  2. Charge tous les CSV du dossier ./modashop_data/ comme tables
  3. Ajoute les contraintes de typage et les index utiles
  4. Crée 3 vues de base très utiles pour les analyses suivantes
  5. Lance quelques requêtes de contrôle pour vérifier que tout est OK

Prérequis :
    pip install duckdb pandas

Lancement :
    python load_duckdb.py

Sortie : un fichier 'modashop.duckdb' réutilisable
====================================================================
"""

import duckdb
from pathlib import Path

# ====================================================================
# CONFIGURATION
# ====================================================================

DATA_DIR = Path("./modashop_data")     # Dossier contenant les CSV
DB_PATH  = "modashop.duckdb"           # Fichier base DuckDB en sortie

# Mapping nom_table -> fichier CSV
TABLES = {
    'dim_date':           'dim_date.csv',
    'dim_canal':          'dim_canal.csv',
    'dim_categorie':      'dim_categorie.csv',
    'dim_produit':        'dim_produit.csv',
    'dim_client':         'dim_client.csv',
    'dim_centre_cout':    'dim_centre_cout.csv',
    'fact_ventes':        'fact_ventes.csv',
    'fact_encaissements': 'fact_encaissements.csv',
    'fact_achats':        'fact_achats.csv',
    'fact_charges':       'fact_charges.csv',
    'fact_paie':          'fact_paie.csv',
    'fact_budget':        'fact_budget.csv',
}


# ====================================================================
# 1. CRÉATION DE LA BASE ET CHARGEMENT DES CSV
# ====================================================================

def charger_donnees():
    print("=" * 60)
    print("CHARGEMENT MODASHOP DANS DUCKDB")
    print("=" * 60)

    # On ouvre la connexion (crée le fichier si inexistant)
    con = duckdb.connect(DB_PATH)
    print(f"\n📂 Base ouverte : {DB_PATH}")

    # On vide les anciennes tables au cas où on relance le script
    print("\n[1/4] Nettoyage des tables existantes...")
    for table in TABLES.keys():
        con.execute(f"DROP TABLE IF EXISTS {table};")
        con.execute(f"DROP VIEW IF EXISTS {table};")

    # Chargement de chaque CSV en table
    print("\n[2/4] Chargement des CSV...")
    for table, fichier in TABLES.items():
        chemin = DATA_DIR / fichier
        if not chemin.exists():
            raise FileNotFoundError(f"❌ Fichier introuvable : {chemin}")

        # read_csv_auto détecte les types automatiquement
        # delim=';' car nos CSV sont au format français
        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT * FROM read_csv_auto('{chemin}', delim=';', header=true);
        """)
        n = con.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        print(f"  ✓ {table:25s} {n:>10,} lignes")

    return con


# ====================================================================
# 2. CRÉATION DES VUES UTILES POUR L'ANALYSE
# ====================================================================

def creer_vues(con):
    """
    Crée 3 vues qui seront réutilisées dans toutes les analyses.
    Ça t'évitera de réécrire les jointures à chaque requête.
    """
    print("\n[3/4] Création des vues d'analyse...")

    # ─── Vue 1 : ventes enrichies ─────────────────────────────────
    # Ajoute aux ventes les dimensions canal et catégorie produit
    # + colonnes pratiques (mois, marge, etc.)
    con.execute("""
        CREATE OR REPLACE VIEW v_ventes AS
        SELECT
            v.commande_id,
            v.date_cmd,
            CAST(strftime(v.date_cmd, '%Y-%m') AS VARCHAR)  AS annee_mois,
            EXTRACT(YEAR  FROM v.date_cmd)                  AS annee,
            EXTRACT(MONTH FROM v.date_cmd)                  AS mois,
            EXTRACT(QUARTER FROM v.date_cmd)                AS trimestre,
            v.client_id,
            v.sku,
            p.categorie,
            p.collection,
            c.canal,
            v.quantite,
            v.prix_unit_ht,
            v.ca_ht,
            v.cout_achat_ht,
            v.ca_ht - v.cout_achat_ht                       AS marge_brute_ht,
            ROUND((v.ca_ht - v.cout_achat_ht) / NULLIF(v.ca_ht, 0) * 100, 2) AS taux_marge_pc
        FROM fact_ventes v
        LEFT JOIN dim_produit p ON v.sku = p.sku
        LEFT JOIN dim_canal   c ON v.canal_id = c.canal_id;
    """)
    print("  ✓ v_ventes (jointure ventes + produit + canal)")

    # ─── Vue 2 : P&L mensuel agrégé ───────────────────────────────
    con.execute("""
        CREATE OR REPLACE VIEW v_pnl_mensuel AS
        SELECT
            annee_mois,
            annee,
            mois,
            canal,
            categorie,
            SUM(quantite)        AS qte_vendue,
            SUM(ca_ht)           AS ca_ht,
            SUM(cout_achat_ht)   AS cout_achat_ht,
            SUM(marge_brute_ht)  AS marge_brute_ht,
            ROUND(SUM(marge_brute_ht) / NULLIF(SUM(ca_ht), 0) * 100, 2) AS taux_marge_pc
        FROM v_ventes
        GROUP BY annee_mois, annee, mois, canal, categorie;
    """)
    print("  ✓ v_pnl_mensuel (P&L agrégé canal × catégorie × mois)")

    # ─── Vue 3 : encaissements enrichis ───────────────────────────
    con.execute("""
        CREATE OR REPLACE VIEW v_encaissements AS
        SELECT
            e.commande_id,
            e.date_cmd,
            e.date_encaissement,
            e.delai_jours,
            e.montant_ht,
            c.canal,
            CAST(strftime(e.date_cmd, '%Y-%m') AS VARCHAR) AS annee_mois
        FROM fact_encaissements e
        LEFT JOIN fact_ventes  v ON e.commande_id = v.commande_id
        LEFT JOIN dim_canal    c ON v.canal_id = c.canal_id;
    """)
    print("  ✓ v_encaissements (avec canal joint pour calcul DSO)")


# ====================================================================
# 3. CONTRÔLES DE COHÉRENCE
# ====================================================================

def controles(con):
    """
    Lance quelques requêtes pour vérifier que tout est bien chargé.
    """
    print("\n[4/4] Contrôles de cohérence...\n")

    # CA par année
    print("📊 CA par année :")
    res = con.execute("""
        SELECT annee,
               ROUND(SUM(ca_ht)/1e6, 2)        AS ca_m_euros,
               ROUND(SUM(marge_brute_ht)/1e6, 2) AS marge_m_euros,
               ROUND(SUM(marge_brute_ht)/SUM(ca_ht)*100, 1) AS taux_marge_pc
        FROM v_ventes
        GROUP BY annee
        ORDER BY annee;
    """).fetchall()
    print(f"  {'Année':<8}{'CA (M€)':<12}{'Marge (M€)':<14}{'Taux marge':<10}")
    for r in res:
        print(f"  {r[0]:<8}{r[1]:<12}{r[2]:<14}{r[3]:<10}%")

    # Mix canal en N
    print("\n📊 Mix canal en 2025 :")
    res = con.execute("""
        SELECT canal,
               ROUND(SUM(ca_ht)/1e6, 2)               AS ca_m_euros,
               ROUND(SUM(ca_ht)/(SELECT SUM(ca_ht) FROM v_ventes WHERE annee=2025)*100, 1) AS part_pc
        FROM v_ventes
        WHERE annee = 2025
        GROUP BY canal
        ORDER BY ca_m_euros DESC;
    """).fetchall()
    for r in res:
        print(f"  {r[0]:<15} {r[1]:>6} M€  ({r[2]}%)")

    # Mix catégorie en N
    print("\n📊 Mix catégorie en 2025 :")
    res = con.execute("""
        SELECT categorie,
               ROUND(SUM(ca_ht)/1e6, 2)               AS ca_m_euros,
               ROUND(SUM(ca_ht)/(SELECT SUM(ca_ht) FROM v_ventes WHERE annee=2025)*100, 1) AS part_pc
        FROM v_ventes
        WHERE annee = 2025
        GROUP BY categorie
        ORDER BY ca_m_euros DESC;
    """).fetchall()
    for r in res:
        print(f"  {r[0]:<15} {r[1]:>6} M€  ({r[2]}%)")

    # Vérif anomalie #3 : DSO marketplaces
    print("\n📊 DSO moyen marketplaces par trimestre (anomalie #3 attendue : +15j en Q2 2025) :")
    res = con.execute("""
        SELECT annee_mois,
               ROUND(AVG(delai_jours), 1) AS dso_jours
        FROM v_encaissements
        WHERE canal = 'Marketplace'
          AND annee_mois >= '2025-01'
        GROUP BY annee_mois
        ORDER BY annee_mois;
    """).fetchall()
    for r in res:
        marker = " ⚠️" if r[1] > 55 else ""
        print(f"  {r[0]}  →  {r[1]:>5} j{marker}")

    print("\n" + "=" * 60)
    print("✅ Base prête ! Tu peux maintenant écrire tes requêtes.")
    print("=" * 60)
    print(f"\n💡 Pour explorer interactivement :")
    print(f"   - Avec Python  : duckdb.connect('{DB_PATH}')")
    print(f"   - En ligne de commande : duckdb {DB_PATH}")
    print(f"   - Avec DBeaver / TablePlus : ouvrir le fichier {DB_PATH}")


# ====================================================================
# MAIN
# ====================================================================

def main():
    con = charger_donnees()
    creer_vues(con)
    controles(con)
    con.close()


if __name__ == '__main__':
    main()
