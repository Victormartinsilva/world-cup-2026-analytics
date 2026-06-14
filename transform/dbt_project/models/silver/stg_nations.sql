-- Aggregated participation and performance per nation across all editions
WITH matches AS (
    SELECT * FROM {{ ref('stg_matches') }}
),

all_teams AS (
    SELECT home_team AS team, edition_year, home_goals AS goals_for, away_goals AS goals_against, winner
    FROM matches
    UNION ALL
    SELECT away_team, edition_year, away_goals, home_goals, winner
    FROM matches
),

nation_stats AS (
    SELECT
        team                                              AS nation,
        COUNT(DISTINCT edition_year)                      AS editions_played,
        COUNT(*)                                          AS total_matches,
        SUM(CASE WHEN winner = team THEN 1 ELSE 0 END)   AS wins,
        SUM(CASE WHEN winner = 'Draw' THEN 1 ELSE 0 END) AS draws,
        SUM(CASE WHEN winner IS NOT NULL AND winner != team AND winner != 'Draw' THEN 1 ELSE 0 END) AS losses,
        SUM(goals_for)                                    AS total_goals_for,
        SUM(goals_against)                                AS total_goals_against,
        MIN(edition_year)                                 AS first_edition,
        MAX(edition_year)                                 AS last_edition
    FROM all_teams
    GROUP BY team
)

SELECT * FROM nation_stats
