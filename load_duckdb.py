"""
====================================================================
CHARGEMENT DES DONNÉES MODASHOP DANS DUCKDB
====================================================================
"""

import duckdb
from pathlib import Path

# ====================================================================
# CONFIGURATION — ces variables sont écrasées par app.py
# ====================================================================

DATA_DIR = Path("./modashop_data")
DB_PATH  = "modashop.duckdb"

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

    db_path_str = str(DB_PATH)

    # ✅ On supprime le fichier existant pour éviter tout conflit
    import os
    if os.path.exists(db_path_str):
        os.remove(db_path_str)

    con = duckdb.connect(db_path_str)
    print(f"\n📂 Base ouverte : {db_path_str}")

    print("\n[1/4] Nettoyage des tables existantes...")
    for table in TABLES.keys():
        con.execute(f"DROP TABLE IF EXISTS {table};")
        con.execute(f"DROP VIEW IF EXISTS {table};")

    print("\n[2/4] Chargement des CSV...")
    for table, fichier in TABLES.items():
        chemin = Path(str(DATA_DIR)) / fichier
        if not chemin.exists():
            raise FileNotFoundError(f"❌ Fichier introuvable : {chemin}")

        con.execute(f"""
            CREATE TABLE {table} AS
            SELECT * FROM read_csv_auto('{chemin}', delim=';', header=true);
        """)
        n = con.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        print(f"  ✓ {table:25s} {n:>10,} lignes")

    return con


# ====================================================================
# 2. CRÉATION DES VUES
# ====================================================================

def creer_vues(con):
    print("\n[3/4] Création des vues d'analyse...")

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
    print("  ✓ v_ventes")

    con.execute("""
        CREATE OR REPLACE VIEW v_pnl_mensuel AS
        SELECT annee_mois, annee, mois, canal, categorie,
            SUM(quantite) AS qte_vendue, SUM(ca_ht) AS ca_ht,
            SUM(cout_achat_ht) AS cout_achat_ht, SUM(marge_brute_ht) AS marge_brute_ht,
            ROUND(SUM(marge_brute_ht)/NULLIF(SUM(ca_ht),0)*100,2) AS taux_marge_pc
        FROM v_ventes
        GROUP BY annee_mois, annee, mois, canal, categorie;
    """)
    print("  ✓ v_pnl_mensuel")

    con.execute("""
        CREATE OR REPLACE VIEW v_encaissements AS
        SELECT e.commande_id, e.date_cmd, e.date_encaissement, e.delai_jours,
               e.montant_ht, c.canal,
               CAST(strftime(e.date_cmd, '%Y-%m') AS VARCHAR) AS annee_mois
        FROM fact_encaissements e
        LEFT JOIN fact_ventes v ON e.commande_id = v.commande_id
        LEFT JOIN dim_canal   c ON v.canal_id = c.canal_id;
    """)
    print("  ✓ v_encaissements")


# ====================================================================
# 3. CONTRÔLES
# ====================================================================

def controles(con):
    print("\n[4/4] Contrôles de cohérence...\n")

    print("📊 CA par année :")
    res = con.execute("""
        SELECT annee,
               ROUND(SUM(ca_ht)/1e6, 2) AS ca_m_euros,
               ROUND(SUM(marge_brute_ht)/1e6, 2) AS marge_m_euros,
               ROUND(SUM(marge_brute_ht)/SUM(ca_ht)*100, 1) AS taux_marge_pc
        FROM v_ventes GROUP BY annee ORDER BY annee;
    """).fetchall()
    print(f"  {'Année':<8}{'CA (M€)':<12}{'Marge (M€)':<14}{'Taux marge':<10}")
    for r in res:
        print(f"  {r[0]:<8}{r[1]:<12}{r[2]:<14}{r[3]:<10}%")

    print("\n" + "=" * 60)
    print("✅ Base prête !")
    print("=" * 60)


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
