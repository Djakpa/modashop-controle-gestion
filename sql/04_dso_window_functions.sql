-- ====================================================================
-- 04. CALCUL DU DSO (Days Sales Outstanding) PAR CANAL ET PAR MOIS
-- ====================================================================
-- Objectif : Suivre le délai moyen d'encaissement client par canal,
--            avec une moyenne mobile sur 3 mois pour lisser le bruit.
--
-- Métier   : Le DSO est un indicateur clé du BFR. Sa dégradation a
--            un impact direct sur la trésorerie.
--
-- Technique : Utilisation des WINDOW FUNCTIONS (AVG OVER) pour
--             calculer une moyenne glissante - compétence valorisée
--             sur un poste de Data Analyst.
-- ====================================================================

WITH dso_mensuel AS (
    SELECT
        annee_mois,
        canal,
        COUNT(*)                            AS nb_factures,
        ROUND(AVG(delai_jours), 1)          AS dso_jours,
        ROUND(SUM(montant_ht) / 1000, 0)    AS ca_encaisse_keur
    FROM v_encaissements
    WHERE annee_mois IS NOT NULL
    GROUP BY annee_mois, canal
)
SELECT
    annee_mois,
    canal,
    nb_factures,
    dso_jours,
    ca_encaisse_keur,
    -- Moyenne mobile 3 mois (sur le canal courant uniquement)
    ROUND(
        AVG(dso_jours) OVER (
            PARTITION BY canal
            ORDER BY annee_mois
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        1
    )                                       AS dso_moy_3m,
    -- Évolution vs mois précédent
    dso_jours - LAG(dso_jours) OVER (
        PARTITION BY canal
        ORDER BY annee_mois
    )                                       AS evol_vs_m_1,
    -- Évolution vs même mois année précédente (utile pour la saisonnalité)
    ROUND(
        dso_jours - LAG(dso_jours, 12) OVER (
            PARTITION BY canal
            ORDER BY annee_mois
        ),
        1
    )                                       AS evol_vs_n_1,
    -- Alerte automatique
    CASE
        WHEN canal = 'Marketplace' AND dso_jours > 55 THEN '⚠️ DSO marketplace dégradé'
        WHEN canal = 'Web' AND dso_jours > 3 THEN '⚠️ Anomalie paiement web'
        ELSE NULL
    END AS alerte
FROM dso_mensuel
ORDER BY canal, annee_mois;

-- ====================================================================
-- 💡 LECTURE ATTENDUE SUR MODASHOP :
--   - Web        : DSO ~1 jour (paiement immédiat CB)
--   - Boutique   : DSO ~0.5 jour
--   - Marketplace: DSO ~45 jours jusqu'en mars 2025
--                  puis ~60 jours à partir d'avril 2025
--                  => l'anomalie #3 ressort très clairement
-- ====================================================================
