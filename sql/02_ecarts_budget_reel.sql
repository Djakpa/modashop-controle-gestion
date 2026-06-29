-- ====================================================================
-- 02. ANALYSE D'ÉCARTS BUDGET vs RÉEL (CA et Marge)
-- ====================================================================
-- Objectif : Comparer le réalisé au budget annuel par mois et par axe
--            analytique, en calculant les écarts en valeur et en %.
--
-- Métier   : C'est le coeur du métier de contrôleur de gestion.
--            On identifie rapidement les BU/canaux qui dérapent.
--
-- Lecture  : ecart_pc > 0 = on dépasse le budget (favorable sur CA)
--            ecart_pc < 0 = on est en retrait (défavorable sur CA)
-- ====================================================================

WITH realise AS (
    SELECT
        annee,
        mois,
        canal,
        categorie,
        SUM(ca_ht)          AS ca_reel,
        SUM(marge_brute_ht) AS marge_reel
    FROM v_ventes
    WHERE annee = 2025
    GROUP BY annee, mois, canal, categorie
),
budget AS (
    SELECT
        b.mois,
        c.canal,
        cat.categorie,
        b.montant_budget         AS ca_budget,
        b.montant_budget * b.marge_budget_pc AS marge_budget
    FROM fact_budget b
    LEFT JOIN dim_canal     c   ON b.canal_id     = c.canal_id
    LEFT JOIN dim_categorie cat ON b.categorie_id = cat.categorie_id
    WHERE b.type = 'CA' AND b.annee = 2025
)
SELECT
    r.mois,
    r.canal,
    r.categorie,
    -- CA
    ROUND(b.ca_budget, 0)                                          AS ca_budget,
    ROUND(r.ca_reel, 0)                                            AS ca_reel,
    ROUND(r.ca_reel - b.ca_budget, 0)                              AS ecart_ca,
    ROUND((r.ca_reel - b.ca_budget) / NULLIF(b.ca_budget, 0) * 100, 1) AS ecart_ca_pc,
    -- Marge
    ROUND(b.marge_budget, 0)                                       AS marge_budget,
    ROUND(r.marge_reel, 0)                                         AS marge_reel,
    ROUND(r.marge_reel - b.marge_budget, 0)                        AS ecart_marge,
    ROUND((r.marge_reel - b.marge_budget) / NULLIF(b.marge_budget, 0) * 100, 1) AS ecart_marge_pc,
    -- Flag visuel rapide
    CASE
        WHEN (r.ca_reel - b.ca_budget) / NULLIF(b.ca_budget, 0) < -0.10 THEN '🔴 Forte sous-performance'
        WHEN (r.ca_reel - b.ca_budget) / NULLIF(b.ca_budget, 0) < -0.05 THEN '🟠 Sous-performance'
        WHEN (r.ca_reel - b.ca_budget) / NULLIF(b.ca_budget, 0) >  0.05 THEN '🟢 Sur-performance'
        ELSE '⚪ Conforme'
    END AS statut
FROM realise r
LEFT JOIN budget b
    ON r.mois = b.mois
   AND r.canal = b.canal
   AND r.categorie = b.categorie
ORDER BY r.mois, ABS(r.ca_reel - b.ca_budget) DESC;
