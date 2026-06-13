-- Final mart: all-time performance per nation, enriched with 2026 qualification flag
WITH nations AS (
    SELECT * FROM {{ ref('stg_nations') }}
),

cups AS (
    SELECT
        winner                          AS nation,
        COUNT(*)                        AS titles
    FROM {{ source('bronze', 'bronze_cups') }}
    GROUP BY winner
),

geo AS (
    SELECT country_name, iso_a3, qualified_2026
    FROM {{ source('bronze', 'bronze_countries') }}
)

SELECT
    n.*,
    COALESCE(c.titles, 0)             AS world_cup_titles,
    g.iso_a3,
    COALESCE(g.qualified_2026, FALSE) AS qualified_2026,
    ROUND(n.wins::FLOAT / NULLIF(n.total_matches, 0) * 100, 1) AS win_pct
FROM nations n
LEFT JOIN cups c ON LOWER(n.nation) = LOWER(c.nation)
LEFT JOIN geo g ON LOWER(n.nation) = LOWER(g.country_name)
ORDER BY world_cup_titles DESC, wins DESC
