-- ====================================================================
-- 03. DÉCOMPOSITION DE L'ÉCART DE CA EN EFFET PRIX / VOLUME / MIX
-- ====================================================================
-- Objectif : Décomposer l'écart de CA entre 2025 (N) et 2024 (N-1)
--            en 3 effets : prix, volume, mix.
--
-- Métier   : C'est LA requête signature du contrôle de gestion.
--            Un DAF veut savoir "pourquoi" le CA varie, pas juste
--            "de combien".
--
-- Formules (méthode classique du contrôle de gestion) :
--   - Effet Volume = (Qté N - Qté N-1) × Prix moyen N-1
--   - Effet Prix   = (Prix moyen N - Prix moyen N-1) × Qté N
--   - Effet Mix    = Écart total - Effet Volume - Effet Prix
--
-- Vérification : CA_N - CA_N-1 = Effet Volume + Effet Prix + Effet Mix
-- ====================================================================

WITH ventes_par_annee AS (
    SELECT
        annee,
        categorie,
        SUM(quantite)                          AS qte,
        SUM(ca_ht)                             AS ca,
        SUM(ca_ht) / NULLIF(SUM(quantite), 0)  AS prix_moyen
    FROM v_ventes
    GROUP BY annee, categorie
),
pivot_annees AS (
    SELECT
        n.categorie,
        n.qte         AS qte_n,
        n_1.qte       AS qte_n_1,
        n.prix_moyen  AS prix_n,
        n_1.prix_moyen AS prix_n_1,
        n.ca          AS ca_n,
        n_1.ca        AS ca_n_1
    FROM ventes_par_annee n
    JOIN ventes_par_annee n_1
        ON n.categorie = n_1.categorie
       AND n.annee = 2025
       AND n_1.annee = 2024
)
SELECT
    categorie,
    ROUND(ca_n_1, 0)                                  AS ca_n_1,
    ROUND(ca_n, 0)                                    AS ca_n,
    ROUND(ca_n - ca_n_1, 0)                           AS ecart_total,
    -- Effet volume : ce que l'écart de quantité aurait rapporté au prix N-1
    ROUND((qte_n - qte_n_1) * prix_n_1, 0)            AS effet_volume,
    -- Effet prix : ce que la variation de prix rapporte sur les qtés N
    ROUND((prix_n - prix_n_1) * qte_n, 0)             AS effet_prix,
    -- Effet mix : résiduel (variations internes au sein de la catégorie)
    ROUND((ca_n - ca_n_1)
        - ((qte_n - qte_n_1) * prix_n_1)
        - ((prix_n - prix_n_1) * qte_n), 0)           AS effet_mix,
    -- Ratios pour storytelling
    ROUND((ca_n - ca_n_1) / NULLIF(ca_n_1, 0) * 100, 1) AS croissance_pc,
    ROUND((prix_n - prix_n_1) / NULLIF(prix_n_1, 0) * 100, 1) AS evol_prix_pc,
    ROUND((qte_n - qte_n_1) / NULLIF(qte_n_1, 0) * 100, 1) AS evol_volume_pc
FROM pivot_annees
ORDER BY ABS(ca_n - ca_n_1) DESC;

-- ====================================================================
-- 💡 LECTURE ATTENDUE SUR MODASHOP :
--   - Accessoires : effet PRIX très positif (+30% lié à la montée en gamme)
--                   mais effet VOLUME négatif (-20% : produits trop chers)
--                   => l'anomalie #4 ressort visuellement
--   - PAP Femme   : effet PRIX légèrement négatif (démarques sept)
-- ====================================================================
