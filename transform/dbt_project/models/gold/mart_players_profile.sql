-- Player profile mart for the 2026 squad visualization
WITH players AS (
    SELECT * FROM {{ ref('stg_players') }}
)

SELECT
    nation,
    player_name,
    position,
    age,
    matches_played,
    goals,
    assists,
    minutes_90s,
    market_value_eur_m,
    CASE
        WHEN position IN ('GK')             THEN 'Goalkeeper'
        WHEN position IN ('CB','RB','LB','WB','RWB','LWB') THEN 'Defender'
        WHEN position IN ('DM','CM','AM','MF') THEN 'Midfielder'
        WHEN position IN ('LW','RW','FW','CF','ST') THEN 'Forward'
        ELSE 'Unknown'
    END AS position_group
FROM players
WHERE player_name IS NOT NULL
ORDER BY nation, market_value_eur_m DESC NULLS LAST
