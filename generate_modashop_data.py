"""
====================================================================
GÉNÉRATEUR DE DONNÉES SYNTHÉTIQUES - ModaShop SAS
====================================================================
Projet : Automatisation du reporting de clôture mensuelle
Entreprise fictive : ModaShop SAS (pure player e-commerce mode B2C)
Période : 24 mois (Janvier N-1 à Décembre N)
CA cible : ~85 M€ en année N

Ce script génère un dataset complet et cohérent simulant l'activité
d'une ETI e-commerce, avec des anomalies volontairement injectées
pour rendre l'analyse de contrôle de gestion réaliste.

Sortie : fichiers CSV dans le dossier ./data/
Format : simule des extracts ERP (Sage / Cegid / SAP)

Auteur : [Ton nom] - Projet portfolio LinkedIn
====================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random

# Reproductibilité
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ====================================================================
# PARAMÈTRES GLOBAUX DU BUSINESS MODEL
# ====================================================================

ANNEE_N = 2025  # Année courante (ajuste si besoin)
DATE_DEBUT = datetime(ANNEE_N - 1, 1, 1)
DATE_FIN = datetime(ANNEE_N, 12, 31)

CA_CIBLE_N = 85_000_000  # 85 M€
CROISSANCE_N = 0.12      # +12% vs N-1
CA_CIBLE_N_1 = CA_CIBLE_N / (1 + CROISSANCE_N)

OUTPUT_DIR = Path("./modashop_data")
OUTPUT_DIR.mkdir(exist_ok=True)


# ====================================================================
# 1. DIMENSIONS
# ====================================================================

def generer_dim_date():
    """Calendrier avec attributs utiles pour le contrôle de gestion."""
    dates = pd.date_range(DATE_DEBUT, DATE_FIN, freq='D')
    df = pd.DataFrame({'date': dates})
    df['date_id']    = df['date'].dt.strftime('%Y%m%d').astype(int)
    df['jour']       = df['date'].dt.day
    df['mois']       = df['date'].dt.month
    df['annee']      = df['date'].dt.year
    df['trimestre']  = df['date'].dt.quarter
    df['semaine']    = df['date'].dt.isocalendar().week
    df['jour_semaine'] = df['date'].dt.day_name()
    df['est_weekend']  = df['date'].dt.weekday.isin([5, 6])
    df['annee_mois']   = df['date'].dt.strftime('%Y-%m')

    # Périodes commerciales clés
    df['est_soldes']     = df['mois'].isin([1, 7])
    df['est_black_fri']  = (df['mois'] == 11) & (df['jour'] >= 20)
    df['est_noel']       = (df['mois'] == 12) & (df['jour'].between(1, 24))
    return df


def generer_dim_canal():
    return pd.DataFrame([
        {'canal_id': 1, 'canal': 'Web',        'part_ca_cible': 0.60, 'marge_cible': 0.52},
        {'canal_id': 2, 'canal': 'Marketplace','part_ca_cible': 0.25, 'marge_cible': 0.38},
        {'canal_id': 3, 'canal': 'Boutique',   'part_ca_cible': 0.15, 'marge_cible': 0.48},
    ])


def generer_dim_categorie():
    return pd.DataFrame([
        {'categorie_id': 1, 'categorie': 'PAP Femme',    'part_ca_cible': 0.45, 'marge_cible': 0.50},
        {'categorie_id': 2, 'categorie': 'PAP Homme',    'part_ca_cible': 0.25, 'marge_cible': 0.48},
        {'categorie_id': 3, 'categorie': 'Accessoires',  'part_ca_cible': 0.20, 'marge_cible': 0.60},
        {'categorie_id': 4, 'categorie': 'Chaussures',   'part_ca_cible': 0.10, 'marge_cible': 0.45},
    ])


def generer_dim_produit(dim_categorie, n_produits_par_cat=40):
    """Génère un catalogue de SKU avec prix achat / vente cohérents."""
    produits = []
    sku_counter = 1000
    libelles_par_cat = {
        'PAP Femme':   ['Robe', 'Chemisier', 'Pantalon', 'Jupe', 'Veste', 'Pull', 'Top', 'Manteau'],
        'PAP Homme':   ['Chemise', 'Pantalon', 'Pull', 'Veste', 'Polo', 'Costume', 'Tshirt', 'Short'],
        'Accessoires': ['Sac', 'Ceinture', 'Echarpe', 'Portefeuille', 'Lunettes', 'Chapeau', 'Bijou', 'Gants'],
        'Chaussures':  ['Baskets', 'Bottes', 'Mocassins', 'Sandales', 'Escarpins', 'Derbies'],
    }
    collections = ['PE', 'AH']  # Printemps-Été / Automne-Hiver

    for _, cat in dim_categorie.iterrows():
        marge_cat = cat['marge_cible']
        libs = libelles_par_cat[cat['categorie']]
        # fourchette de prix de vente par catégorie
        if cat['categorie'] == 'Accessoires':
            prix_min, prix_max = 25, 250
        elif cat['categorie'] == 'Chaussures':
            prix_min, prix_max = 60, 280
        else:
            prix_min, prix_max = 35, 320

        for i in range(n_produits_par_cat):
            prix_vente = round(np.random.uniform(prix_min, prix_max), 2)
            # marge réelle bruitée autour de la cible
            marge = np.clip(np.random.normal(marge_cat, 0.05), 0.20, 0.75)
            prix_achat = round(prix_vente * (1 - marge), 2)
            produits.append({
                'sku': f'SKU{sku_counter}',
                'libelle': f"{random.choice(libs)} {random.choice(collections)}{random.randint(22, 25)}",
                'categorie_id': cat['categorie_id'],
                'categorie': cat['categorie'],
                'prix_vente_ht': prix_vente,
                'prix_achat_ht': prix_achat,
                'collection': random.choice(collections),
            })
            sku_counter += 1
    return pd.DataFrame(produits)


def generer_dim_client(n=15000):
    segments = ['Nouveau', 'Récurrent', 'VIP']
    poids    = [0.55, 0.35, 0.10]
    clients = []
    for i in range(n):
        clients.append({
            'client_id': f'C{i+1:06d}',
            'segment':   np.random.choice(segments, p=poids),
            'date_creation': DATE_DEBUT + timedelta(days=np.random.randint(-730, 700)),
        })
    return pd.DataFrame(clients)


def generer_dim_centre_cout():
    return pd.DataFrame([
        {'cc_id': 'CC01', 'centre_cout': 'Marketing',       'masse_salariale_mens': 180_000},
        {'cc_id': 'CC02', 'centre_cout': 'Logistique',      'masse_salariale_mens': 220_000},
        {'cc_id': 'CC03', 'centre_cout': 'IT',              'masse_salariale_mens': 150_000},
        {'cc_id': 'CC04', 'centre_cout': 'RH',              'masse_salariale_mens':  80_000},
        {'cc_id': 'CC05', 'centre_cout': 'Direction',       'masse_salariale_mens': 120_000},
        {'cc_id': 'CC06', 'centre_cout': 'Service Client',  'masse_salariale_mens': 110_000},
        {'cc_id': 'CC07', 'centre_cout': 'Achats',          'masse_salariale_mens':  90_000},
    ])


# ====================================================================
# 2. COURBES DE SAISONNALITÉ
# ====================================================================

def coef_saisonnalite(mois):
    """
    Coefficient multiplicateur du CA par mois (moyenne = 1.0).
    Pics : nov (Black Friday), déc (Noël), janv/juil (soldes).
    Creux : févr, août.
    """
    coefs = {
        1: 1.15, 2: 0.70, 3: 0.90, 4: 0.95, 5: 1.00, 6: 0.95,
        7: 1.20, 8: 0.60, 9: 1.00, 10: 1.05, 11: 1.55, 12: 1.65
    }
    return coefs[mois]


# ====================================================================
# 3. FAITS - VENTES
# ====================================================================

def generer_fact_ventes(dim_produit, dim_client, dim_canal, dim_date):
    """
    Génère les lignes de commande détaillées sur 24 mois (vectorisé par mois).
    Anomalies injectées :
      - #2 Surstock PAP Femme été N : démarques sept N (-15% prix)
      - #4 Effet mix accessoires raté en N : volume -20%, prix +30%
    """
    print("  → génération des ventes (vectorisé)...")

    # CA cible par mois en utilisant la saisonnalité
    mois_periode = pd.date_range(DATE_DEBUT, DATE_FIN, freq='MS')
    ca_mensuel = {}
    for annee, ca_total in [(ANNEE_N - 1, CA_CIBLE_N_1), (ANNEE_N, CA_CIBLE_N)]:
        mois_annee = [d for d in mois_periode if d.year == annee]
        coefs_annee = np.array([coef_saisonnalite(d.month) for d in mois_annee])
        ca_mois = ca_total * coefs_annee / coefs_annee.sum()
        for d, c in zip(mois_annee, ca_mois):
            ca_mensuel[(d.year, d.month)] = c

    clients_ids = dim_client['client_id'].values
    canal_ids   = dim_canal['canal_id'].values
    canal_poids = dim_canal['part_ca_cible'].values

    cats_ordre = ['PAP Femme', 'PAP Homme', 'Accessoires', 'Chaussures']
    poids_categories = [0.45, 0.25, 0.20, 0.10]

    # Pré-indexation des produits par catégorie pour tirage rapide
    prod_par_cat = {cat: dim_produit[dim_produit['categorie'] == cat].reset_index(drop=True)
                    for cat in cats_ordre}

    toutes_ventes = []
    ordre_counter = 1

    for (annee, mois), ca_cible_mois in ca_mensuel.items():
        # Estimation du nb de lignes nécessaires (panier moyen ~80€ x 1.5 articles)
        panier_moyen = 110
        n_estime = int(ca_cible_mois / panier_moyen * 1.15)  # marge pour itération

        # Tirages vectorisés
        quantites = np.random.choice([1, 1, 1, 2, 2, 3], size=n_estime)
        canaux    = np.random.choice(canal_ids, size=n_estime, p=canal_poids)
        cats      = np.random.choice(cats_ordre, size=n_estime, p=poids_categories)
        clients   = np.random.choice(clients_ids, size=n_estime)
        jours     = np.random.randint(1, 29, size=n_estime)

        # Sélection produits : tirage vectoriel par catégorie
        sku_arr   = np.empty(n_estime, dtype=object)
        pv_arr    = np.empty(n_estime, dtype=float)
        pa_arr    = np.empty(n_estime, dtype=float)
        coll_arr  = np.empty(n_estime, dtype=object)
        for cat in cats_ordre:
            mask = (cats == cat)
            nb = int(mask.sum())
            if nb == 0:
                continue
            pool = prod_par_cat[cat]
            idx_pool = np.random.randint(0, len(pool), size=nb)
            sku_arr[mask]  = pool['sku'].values[idx_pool]
            pv_arr[mask]   = pool['prix_vente_ht'].values[idx_pool]
            pa_arr[mask]   = pool['prix_achat_ht'].values[idx_pool]
            coll_arr[mask] = pool['collection'].values[idx_pool]

        # --- ANOMALIE #4 : montée en gamme Accessoires (en N) ---
        if annee == ANNEE_N:
            mask_acc = (cats == 'Accessoires')
            pv_arr[mask_acc] *= 1.30
            # 20% des ventes Accessoires sont "perdues" → on les filtre
            drop_acc = mask_acc & (np.random.random(n_estime) < 0.20)
            keep = ~drop_acc
        else:
            keep = np.ones(n_estime, dtype=bool)

        # --- ANOMALIE #2 : démarques sept N PAP Femme PE ---
        if annee == ANNEE_N and mois == 9:
            mask_demarque = (cats == 'PAP Femme') & (coll_arr == 'PE')
            pv_arr[mask_demarque] *= 0.85

        # Soldes janvier/juillet : -30% sur 40% des ventes
        if mois in (1, 7):
            mask_soldes = np.random.random(n_estime) < 0.4
            pv_arr[mask_soldes] *= 0.70

        # Coûts d'achat avec léger bruit
        cout_unit = pa_arr * np.random.uniform(0.97, 1.03, n_estime)

        ca_ligne   = np.round(pv_arr * quantites, 2)
        cout_ligne = np.round(cout_unit * quantites, 2)

        # On applique le filtre keep + ajustement pour respecter le CA cible
        ca_ligne   = ca_ligne[keep]
        cout_ligne = cout_ligne[keep]
        quantites  = quantites[keep]
        canaux     = canaux[keep]
        clients    = clients[keep]
        jours      = jours[keep]
        sku_arr    = sku_arr[keep]
        pv_arr     = pv_arr[keep]

        # Ajustement : on garde un nombre de lignes pour atteindre ~ca cible (+/- 3%)
        ca_cum = np.cumsum(ca_ligne)
        n_garder = int(np.searchsorted(ca_cum, ca_cible_mois)) + 1
        n_garder = min(n_garder, len(ca_ligne))

        df_mois = pd.DataFrame({
            'commande_id':   [f'CMD{i:08d}' for i in range(ordre_counter, ordre_counter + n_garder)],
            'date_cmd':      [datetime(annee, mois, int(j)) for j in jours[:n_garder]],
            'client_id':     clients[:n_garder],
            'sku':           sku_arr[:n_garder],
            'canal_id':      canaux[:n_garder],
            'quantite':      quantites[:n_garder],
            'prix_unit_ht':  np.round(pv_arr[:n_garder], 2),
            'ca_ht':         ca_ligne[:n_garder],
            'cout_achat_ht': cout_ligne[:n_garder],
        })
        ordre_counter += n_garder
        toutes_ventes.append(df_mois)

    df = pd.concat(toutes_ventes, ignore_index=True)
    print(f"  ✓ {len(df):,} lignes de ventes générées | CA total = {df['ca_ht'].sum()/1e6:.1f} M€")
    return df


# ====================================================================
# 4. FAITS - ENCAISSEMENTS (pour calcul DSO)
# ====================================================================

def generer_fact_encaissements(fact_ventes, dim_canal):
    """
    Génère les encaissements avec délais réalistes par canal (vectorisé).
    Anomalie #3 : DSO marketplaces passe de 45j à 60j à partir d'avril N.
    """
    print("  → génération des encaissements (vectorisé)...")
    n = len(fact_ventes)
    canal = fact_ventes['canal_id'].values
    dates = pd.to_datetime(fact_ventes['date_cmd']).values

    delais = np.zeros(n, dtype=int)

    # Web (canal 1) : 0-2 jours
    mask_web = (canal == 1)
    delais[mask_web] = np.random.choice([0, 0, 0, 1, 2], size=mask_web.sum())

    # Boutique (canal 3) : 0-1 jour
    mask_bout = (canal == 3)
    delais[mask_bout] = np.random.choice([0, 1], size=mask_bout.sum())

    # Marketplaces (canal 2) : 45j avant avril N, 60j ensuite
    mask_mp = (canal == 2)
    seuil = np.datetime64(datetime(ANNEE_N, 4, 1))
    mask_mp_avant = mask_mp & (dates < seuil)
    mask_mp_apres = mask_mp & (dates >= seuil)
    delais[mask_mp_avant] = np.clip(np.random.normal(45, 4, mask_mp_avant.sum()).astype(int), 0, None)
    delais[mask_mp_apres] = np.clip(np.random.normal(60, 5, mask_mp_apres.sum()).astype(int), 0, None)

    df = pd.DataFrame({
        'commande_id': fact_ventes['commande_id'].values,
        'date_cmd': fact_ventes['date_cmd'].values,
        'date_encaissement': dates + delais.astype('timedelta64[D]'),
        'montant_ht': fact_ventes['ca_ht'].values,
        'delai_jours': delais,
    })
    print(f"  ✓ {len(df):,} encaissements générés")
    return df


# ====================================================================
# 5. FAITS - ACHATS / STOCKS
# ====================================================================

def generer_fact_achats(fact_ventes, dim_produit):
    """
    Génère les achats fournisseurs mensuels par SKU.
    Anomalie #2 (surstock été N) : surcommandes sur PAP Femme PE en mars-avril N.
    Anomalie #5 (inflation logistique) : coûts transport +15% à partir de juin N.
    """
    print("  → génération des achats...")
    # On agrège ventes mensuelles par SKU pour dimensionner les achats
    fact_ventes['annee_mois'] = pd.to_datetime(fact_ventes['date_cmd']).dt.strftime('%Y-%m')
    ventes_mensuelles = fact_ventes.groupby(['annee_mois', 'sku']).agg(
        qte_vendue=('quantite', 'sum'),
        cout_total=('cout_achat_ht', 'sum')
    ).reset_index()

    achats = []
    facture_id = 1
    for _, row in ventes_mensuelles.iterrows():
        produit = dim_produit[dim_produit['sku'] == row['sku']].iloc[0]
        annee, mois = map(int, row['annee_mois'].split('-'))
        # On commande en moyenne ce qu'on vend +/- 20%
        qte_achat = int(row['qte_vendue'] * np.random.uniform(0.85, 1.20))

        # ANOMALIE #2 : surstock été N sur PAP Femme PE
        if annee == ANNEE_N and mois in (3, 4) and produit['categorie'] == 'PAP Femme' and produit['collection'] == 'PE':
            qte_achat = int(qte_achat * 1.6)  # +60%

        cout_unit = produit['prix_achat_ht']

        # Frais de transport ~3% du coût d'achat
        # ANOMALIE #5 : inflation logistique +15% à partir de juin N
        taux_transport = 0.03
        if annee == ANNEE_N and mois >= 6:
            taux_transport = 0.0345  # +15%

        montant_marchandises = round(qte_achat * cout_unit, 2)
        montant_transport = round(montant_marchandises * taux_transport, 2)

        achats.append({
            'facture_id': f'FA{facture_id:07d}',
            'date_facture': datetime(annee, mois, np.random.randint(5, 26)),
            'sku': row['sku'],
            'quantite': qte_achat,
            'montant_marchandises_ht': montant_marchandises,
            'montant_transport_ht': montant_transport,
            'montant_total_ht': montant_marchandises + montant_transport,
            'delai_paiement_fourn': np.random.choice([30, 30, 45, 60], p=[0.5, 0.2, 0.2, 0.1]),
        })
        facture_id += 1
    df = pd.DataFrame(achats)
    print(f"  ✓ {len(df):,} factures d'achat générées")
    return df


# ====================================================================
# 6. FAITS - CHARGES EXTERNES (incl. anomalie marketing)
# ====================================================================

def generer_fact_charges_externes():
    """
    Charges mensuelles par centre de coût.
    Anomalie #1 : explosion du CAC marketing sur marketplaces en Q2 N.
    """
    print("  → génération des charges externes...")
    charges = []
    mois_periode = pd.date_range(DATE_DEBUT, DATE_FIN, freq='MS')

    charges_base = {
        # cc_id: {nature_charge: montant_mensuel_base}
        'CC01': {'Marketing digital Web': 280_000,
                 'Marketing Marketplaces': 90_000,
                 'Marketing offline': 40_000},
        'CC02': {'Loyer entrepôt': 65_000,
                 'Prestation logistique 3PL': 180_000,
                 'Fournitures emballage': 35_000},
        'CC03': {'SaaS et licences': 45_000,
                 'Hébergement cloud': 28_000,
                 'Prestations IT': 30_000},
        'CC04': {'Recrutement et formation': 12_000},
        'CC05': {'Loyer siège Paris': 55_000,
                 'Honoraires (avocats, comptables)': 18_000,
                 'Frais de déplacement': 22_000},
        'CC06': {'Plateforme service client': 8_000},
        'CC07': {'Frais douaniers et import': 25_000},
    }

    for d in mois_periode:
        # variation aléatoire +/- 5%
        for cc_id, dict_charges in charges_base.items():
            for nature, montant_base in dict_charges.items():
                montant = montant_base * np.random.uniform(0.95, 1.05)

                # ANOMALIE #1 : explosion marketing marketplaces Q2 N
                if (cc_id == 'CC01' and nature == 'Marketing Marketplaces'
                    and d.year == ANNEE_N and d.month in (4, 5, 6)):
                    montant *= 1.40  # +40%

                # Saisonnalité marketing : on dépense plus en oct/nov
                if cc_id == 'CC01' and d.month in (10, 11):
                    montant *= 1.5

                charges.append({
                    'date_charge': d,
                    'cc_id': cc_id,
                    'nature_charge': nature,
                    'montant_ht': round(montant, 2),
                })
    df = pd.DataFrame(charges)
    print(f"  ✓ {len(df):,} lignes de charges générées")
    return df


# ====================================================================
# 7. FAITS - PAIE
# ====================================================================

def generer_fact_paie(dim_centre_cout):
    """Masse salariale mensuelle par centre de coût, avec NAO +2.5% en janvier N."""
    print("  → génération de la paie...")
    paie = []
    mois_periode = pd.date_range(DATE_DEBUT, DATE_FIN, freq='MS')
    for d in mois_periode:
        for _, cc in dim_centre_cout.iterrows():
            ms = cc['masse_salariale_mens']
            # NAO janvier N : +2.5%
            if d.year == ANNEE_N:
                ms *= 1.025
            # Prime de fin d'année en décembre : 1.8 mois
            if d.month == 12:
                ms *= 1.8
            paie.append({
                'date_paie': d,
                'cc_id': cc['cc_id'],
                'masse_salariale_ht': round(ms * np.random.uniform(0.98, 1.02), 2),
            })
    df = pd.DataFrame(paie)
    print(f"  ✓ {len(df):,} lignes de paie générées")
    return df


# ====================================================================
# 8. BUDGET
# ====================================================================

def generer_fact_budget(dim_canal, dim_categorie, dim_centre_cout):
    """
    Budget de l'année N, construit en N-1 sur la base d'objectifs.
    Sera comparé au réel pour calculer les écarts.
    """
    print("  → génération du budget...")
    budget = []
    # Budget CA par canal × catégorie × mois
    for mois in range(1, 13):
        coef = coef_saisonnalite(mois)
        for _, canal in dim_canal.iterrows():
            for _, cat in dim_categorie.iterrows():
                ca_budget = (CA_CIBLE_N
                             * canal['part_ca_cible']
                             * cat['part_ca_cible']
                             * coef / 12)
                marge_pc = (canal['marge_cible'] + cat['marge_cible']) / 2
                budget.append({
                    'annee': ANNEE_N,
                    'mois': mois,
                    'type': 'CA',
                    'canal_id': canal['canal_id'],
                    'categorie_id': cat['categorie_id'],
                    'cc_id': None,
                    'montant_budget': round(ca_budget, 2),
                    'marge_budget_pc': round(marge_pc, 4),
                })
    # Budget charges par centre de coût et mois (basé sur N-1 + inflation 3%)
    base_charges_cc = {
        'CC01': 420_000, 'CC02': 290_000, 'CC03': 110_000,
        'CC04':  18_000, 'CC05':  98_000, 'CC06':  12_000, 'CC07':  28_000,
    }
    for mois in range(1, 13):
        coef_mkt = 1.5 if mois in (10, 11) else 1.0
        for cc_id, base in base_charges_cc.items():
            mt = base * 1.03  # inflation budgétée
            if cc_id == 'CC01':
                mt *= coef_mkt
            budget.append({
                'annee': ANNEE_N,
                'mois': mois,
                'type': 'Charges',
                'canal_id': None,
                'categorie_id': None,
                'cc_id': cc_id,
                'montant_budget': round(mt, 2),
                'marge_budget_pc': None,
            })
    df = pd.DataFrame(budget)
    print(f"  ✓ {len(df):,} lignes de budget générées")
    return df


# ====================================================================
# MAIN
# ====================================================================

def main():
    print("=" * 60)
    print("GÉNÉRATION DES DONNÉES MODASHOP SAS")
    print("=" * 60)

    print("\n[1/3] Génération des dimensions...")
    dim_date         = generer_dim_date()
    dim_canal        = generer_dim_canal()
    dim_categorie    = generer_dim_categorie()
    dim_produit      = generer_dim_produit(dim_categorie)
    dim_client       = generer_dim_client()
    dim_centre_cout  = generer_dim_centre_cout()

    print("\n[2/3] Génération des faits...")
    fact_ventes         = generer_fact_ventes(dim_produit, dim_client, dim_canal, dim_date)
    fact_encaissements  = generer_fact_encaissements(fact_ventes, dim_canal)
    fact_achats         = generer_fact_achats(fact_ventes, dim_produit)
    fact_charges        = generer_fact_charges_externes()
    fact_paie           = generer_fact_paie(dim_centre_cout)
    fact_budget         = generer_fact_budget(dim_canal, dim_categorie, dim_centre_cout)

    # On retire la colonne annee_mois ajoutée temporairement
    fact_ventes = fact_ventes.drop(columns=['annee_mois'], errors='ignore')

    print("\n[3/3] Export CSV dans ./data/ ...")
    tables = {
        'dim_date':           dim_date,
        'dim_canal':          dim_canal,
        'dim_categorie':      dim_categorie,
        'dim_produit':        dim_produit,
        'dim_client':         dim_client,
        'dim_centre_cout':    dim_centre_cout,
        'fact_ventes':        fact_ventes,
        'fact_encaissements': fact_encaissements,
        'fact_achats':        fact_achats,
        'fact_charges':       fact_charges,
        'fact_paie':          fact_paie,
        'fact_budget':        fact_budget,
    }
    for nom, df in tables.items():
        path = OUTPUT_DIR / f"{nom}.csv"
        df.to_csv(path, index=False, sep=';', encoding='utf-8')
        print(f"  ✓ {nom}.csv ({len(df):,} lignes)")

    print("\n" + "=" * 60)
    print("RÉCAPITULATIF")
    print("=" * 60)
    ca_n_1 = fact_ventes[pd.to_datetime(fact_ventes['date_cmd']).dt.year == ANNEE_N - 1]['ca_ht'].sum()
    ca_n   = fact_ventes[pd.to_datetime(fact_ventes['date_cmd']).dt.year == ANNEE_N]['ca_ht'].sum()
    print(f"CA {ANNEE_N - 1} : {ca_n_1/1e6:.2f} M€")
    print(f"CA {ANNEE_N}   : {ca_n/1e6:.2f} M€  (croissance : {(ca_n/ca_n_1 - 1)*100:+.1f}%)")
    print("\nAnomalies injectées (à détecter dans ton analyse) :")
    print("  #1 Explosion marketing marketplaces Q2 N (+40%)")
    print("  #2 Surstock PAP Femme PE → démarques sept N (-15%)")
    print("  #3 DSO marketplaces : 45j → 60j à partir d'avril N")
    print("  #4 Montée en gamme accessoires ratée en N (-20% volume, +30% prix)")
    print("  #5 Inflation logistique +15% à partir de juin N")
    print("\n✓ Tout est prêt dans ./data/")


if __name__ == '__main__':
    main()
