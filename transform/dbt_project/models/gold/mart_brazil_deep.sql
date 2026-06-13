-- Brazil performance per edition: goals, stage reached, wins/losses
WITH matches AS (
    SELECT * FROM {{ ref('stg_matches') }}
),

brazil_matches AS (
    SELECT
        edition_year,
        stage,
        CASE WHEN home_team = 'Brazil' THEN away_team ELSE home_team END AS opponent,
        CASE WHEN home_team = 'Brazil' THEN home_goals ELSE away_goals END AS brazil_goals,
        CASE WHEN home_team = 'Brazil' THEN away_goals ELSE home_goals END AS opponent_goals,
        winner
    FROM matches
    WHERE home_team = 'Brazil' OR away_team = 'Brazil'
),

per_edition AS (
    SELECT
        edition_year,
        COUNT(*)                                                   AS matches_played,
        SUM(CASE WHEN winner = 'Brazil' THEN 1 ELSE 0 END)        AS wins,
        SUM(CASE WHEN winner = 'Draw' THEN 1 ELSE 0 END)          AS draws,
        SUM(CASE WHEN winner NOT IN ('Brazil','Draw') THEN 1 ELSE 0 END) AS losses,
        SUM(brazil_goals)                                          AS goals_scored,
        SUM(opponent_goals)                                        AS goals_conceded,
        MAX(stage)                                                 AS furthest_stage
    FROM brazil_matches
    GROUP BY edition_year
)

SELECT * FROM per_edition ORDER BY edition_year
