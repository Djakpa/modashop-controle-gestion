-- ====================================================================
-- 05. DÉTECTION AUTOMATIQUE DES DÉRIVES (TOP ALERTES)
-- ====================================================================
-- Objectif : Identifier automatiquement les dérives significatives
--            (CA, marge, charges) sans avoir à scanner manuellement.
--
-- Métier   : C'est le rêve de tout contrôleur de gestion : être
--            alerté automatiquement plutôt que de découvrir un
--            problème 3 semaines après en lisant le reporting.
--
-- Méthode  : Calcul de la moyenne et de l'écart-type sur les 12
--            derniers mois (référence). Tout point au-delà de
--            ±2 écarts-types = anomalie statistique (méthode Z-score).
-- ====================================================================

-- 5.1 - DÉRIVES SUR LES CHARGES PAR CENTRE DE COÛT
WITH charges_mensuelles AS (
    SELECT
        strftime(date_charge, '%Y-%m')      AS annee_mois,
        cc_id,
        nature_charge,
        SUM(montant_ht)                     AS montant_mois
    FROM fact_charges
    GROUP BY annee_mois, cc_id, nature_charge
),
charges_stats AS (
    SELECT
        annee_mois,
        cc_id,
        nature_charge,
        montant_mois,
        -- Moyenne sur les 12 mois précédents (référence)
        AVG(montant_mois) OVER (
            PARTITION BY cc_id, nature_charge
            ORDER BY annee_mois
            ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING
        ) AS moyenne_12m,
        -- Écart-type sur les 12 mois précédents
        STDDEV(montant_mois) OVER (
            PARTITION BY cc_id, nature_charge
            ORDER BY annee_mois
            ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING
        ) AS ecart_type_12m
    FROM charges_mensuelles
)
SELECT
    annee_mois,
    cc.centre_cout,
    nature_charge,
    ROUND(montant_mois, 0)        AS montant,
    ROUND(moyenne_12m, 0)         AS moyenne_ref,
    ROUND(montant_mois - moyenne_12m, 0) AS ecart_valeur,
    ROUND((montant_mois - moyenne_12m) / NULLIF(moyenne_12m, 0) * 100, 1) AS ecart_pc,
    -- Z-score : nombre d'écarts-types vs la moyenne
    ROUND((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0), 2) AS z_score,
    CASE
        WHEN ABS((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0)) > 3
            THEN '🚨 ANOMALIE MAJEURE'
        WHEN ABS((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0)) > 2
            THEN '⚠️ Dérive significative'
        ELSE '✅ Normal'
    END AS statut
FROM charges_stats cs
LEFT JOIN dim_centre_cout cc USING (cc_id)
WHERE moyenne_12m IS NOT NULL
  AND ABS((montant_mois - moyenne_12m) / NULLIF(ecart_type_12m, 0)) > 2  -- on garde uniquement les alertes
ORDER BY annee_mois DESC, ABS(z_score) DESC
LIMIT 20;

-- ====================================================================
-- 💡 LECTURE ATTENDUE SUR MODASHOP :
--   - Avril/Mai/Juin 2025 : Marketing Marketplaces flaggé +40%
--     => l'anomalie #1 est détectée AUTOMATIQUEMENT par l'algorithme
-- ====================================================================
