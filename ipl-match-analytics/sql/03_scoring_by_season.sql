-- First-innings scoring by season (full 20-over games only, no rain-shortened matches)
SELECT
    season,
    ROUND(AVG(first_innings_runs), 1)                                 AS avg_first_innings,
    ROUND(100.0 * SUM(first_innings_runs >= 200) / COUNT(*), 1)       AS pct_200_plus,
    MAX(first_innings_runs)                                           AS highest
FROM matches
WHERE result != 'no result' AND method = ''
GROUP BY season
ORDER BY season;
