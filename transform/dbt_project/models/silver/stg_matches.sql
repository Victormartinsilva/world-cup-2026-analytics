-- Staged match results 1930-2022, one row per match
WITH source AS (
    SELECT * FROM {{ source('bronze', 'bronze_matches') }}
),

trimmed AS (
    SELECT
        CAST(year AS INTEGER)              AS edition_year,
        TRIM(stage)                        AS stage,
        TRIM(stadium)                      AS stadium,
        TRIM(city)                         AS city,
        TRIM(home_team_name)               AS home_team,
        CAST(home_team_goals AS INTEGER)   AS home_goals,
        CAST(away_team_goals AS INTEGER)   AS away_goals,
        TRIM(away_team_name)               AS away_team,
        CAST(attendance AS INTEGER)        AS attendance,
        TRIM(referee)                      AS referee
    FROM source
    WHERE home_team_name IS NOT NULL
),

cleaned AS (
    SELECT
        *,
        CASE
            WHEN home_goals > away_goals THEN home_team
            WHEN away_goals > home_goals THEN away_team
            ELSE 'Draw'
        END AS winner
    FROM trimmed
)

SELECT * FROM cleaned
