-- Staged player-level data joining squad stats with market values
WITH squads AS (
    SELECT * FROM {{ source('bronze', 'bronze_squads') }}
),

market AS (
    SELECT * FROM {{ source('bronze', 'bronze_market_value') }}
)

SELECT
    s.nation,
    s.player                                                              AS player_name,
    s.pos                                                                 AS position,
    TRY_CAST(SPLIT_PART(CAST(s.age AS VARCHAR), '-', 1) AS INTEGER)      AS age,
    TRY_CAST(s.mp AS INTEGER)                                             AS matches_played,
    TRY_CAST(s.gls AS FLOAT)                                              AS goals,
    TRY_CAST(s.ast AS FLOAT)                                              AS assists,
    TRY_CAST(s."90s" AS FLOAT)                                            AS minutes_90s,
    m.market_value_eur_m
FROM squads s
LEFT JOIN market m
    ON s.nation = m.nation
    AND LOWER(TRIM(s.player)) = LOWER(TRIM(m.player_name))
