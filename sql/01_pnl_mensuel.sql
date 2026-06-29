-- ====================================================================
-- 01. P&L MENSUEL DÉTAILLÉ (Canal × Catégorie)
-- ====================================================================
-- Objectif : Construire le compte de résultat de gestion mensuel
--            avec ventilation par axe analytique (canal × catégorie)
--
-- Métier   : Cette requête est la base de tout reporting de clôture.
--            Elle remplace 3 jours de manipulation Excel par un calcul
--            instantané.
--
-- Sortie   : 1 ligne par mois × canal × catégorie avec CA, coût, marge,
--            taux de marge et part de mix.
-- ====================================================================

WITH pnl_base AS (
    SELECT
        annee_mois,
        annee,
        mois,
        canal,
        categorie,
        SUM(quantite)        AS qte_vendue,
        SUM(ca_ht)           AS ca_ht,
        SUM(cout_achat_ht)   AS cout_achat_ht,
        SUM(marge_brute_ht)  AS marge_brute_ht
    FROM v_ventes
    GROUP BY annee_mois, annee, mois, canal, categorie
),
totaux_mensuels AS (
    -- Calcul du CA total mensuel pour le mix
    SELECT annee_mois, SUM(ca_ht) AS ca_total_mois
    FROM pnl_base
    GROUP BY annee_mois
)
SELECT
    p.annee_mois,
    p.canal,
    p.categorie,
    p.qte_vendue,
    ROUND(p.ca_ht, 0)                                        AS ca_ht,
    ROUND(p.cout_achat_ht, 0)                                AS cout_achat_ht,
    ROUND(p.marge_brute_ht, 0)                               AS marge_brute_ht,
    ROUND(p.marge_brute_ht / NULLIF(p.ca_ht, 0) * 100, 1)    AS taux_marge_pc,
    ROUND(p.ca_ht / NULLIF(t.ca_total_mois, 0) * 100, 1)     AS part_mix_pc
FROM pnl_base p
LEFT JOIN totaux_mensuels t USING (annee_mois)
ORDER BY p.annee_mois, p.canal, p.categorie;
