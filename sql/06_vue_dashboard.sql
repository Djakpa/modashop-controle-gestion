-- ====================================================================
-- 06. VUE 360° POUR DASHBOARD (KPIs CONSOLIDÉS)
-- ====================================================================
-- Objectif : Produire une table consolidée prête à brancher sur
--            Streamlit / Power BI / Tableau avec tous les KPIs clés.
--
-- Métier   : C'est le format "self-service BI" : un fichier unique
--            qui contient tout, qu'on peut filtrer / pivoter à volonté.
--
-- Usage    : Cette vue alimente le dashboard Streamlit du projet.
-- ====================================================================

CREATE OR REPLACE VIEW v_dashboard_kpis AS
WITH
-- Bloc 1 : ventes mensuelles consolidées
ventes_mensuelles AS (
    SELECT
        annee_mois,
        annee,
        mois,
        canal,
        categorie,
        SUM(quantite)        AS qte,
        SUM(ca_ht)           AS ca_ht,
        SUM(cout_achat_ht)   AS cout_achat_ht,
        SUM(marge_brute_ht)  AS marge_brute_ht
    FROM v_ventes
    GROUP BY annee_mois, annee, mois, canal, categorie
),
-- Bloc 2 : budget mensuel
budget_mensuel AS (
    SELECT
        b.mois,
        c.canal,
        cat.categorie,
        b.montant_budget                       AS ca_budget,
        b.montant_budget * b.marge_budget_pc   AS marge_budget
    FROM fact_budget b
    LEFT JOIN dim_canal     c   ON b.canal_id = c.canal_id
    LEFT JOIN dim_categorie cat ON b.categorie_id = cat.categorie_id
    WHERE b.type = 'CA' AND b.annee = 2025
)
SELECT
    v.annee_mois,
    v.annee,
    v.mois,
    v.canal,
    v.categorie,
    v.qte,
    ROUND(v.ca_ht, 0)                        AS ca_ht,
    ROUND(v.cout_achat_ht, 0)                AS cout_achat_ht,
    ROUND(v.marge_brute_ht, 0)               AS marge_brute_ht,
    ROUND(v.marge_brute_ht / NULLIF(v.ca_ht, 0) * 100, 1) AS taux_marge_pc,
    -- Budget (seulement pour 2025, NULL pour 2024)
    CASE WHEN v.annee = 2025 THEN ROUND(b.ca_budget, 0) END     AS ca_budget,
    CASE WHEN v.annee = 2025 THEN ROUND(b.marge_budget, 0) END  AS marge_budget,
    CASE WHEN v.annee = 2025
         THEN ROUND(v.ca_ht - b.ca_budget, 0)
    END AS ecart_ca,
    CASE WHEN v.annee = 2025
         THEN ROUND((v.ca_ht - b.ca_budget) / NULLIF(b.ca_budget, 0) * 100, 1)
    END AS ecart_ca_pc
FROM ventes_mensuelles v
LEFT JOIN budget_mensuel b
    ON v.mois = b.mois
   AND v.canal = b.canal
   AND v.categorie = b.categorie
ORDER BY v.annee_mois, v.canal, v.categorie;

-- Test de la vue
SELECT * FROM v_dashboard_kpis LIMIT 10;
