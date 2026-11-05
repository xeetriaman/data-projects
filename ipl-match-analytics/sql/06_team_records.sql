-- Franchise win rates (teams with 50+ completed matches)
WITH appearances AS (
    SELECT team1 AS team, winner FROM matches WHERE result != 'no result'
    UNION ALL
    SELECT team2 AS team, winner FROM matches WHERE result != 'no result'
)
SELECT
    team,
    COUNT(*)                                          AS matches,
    SUM(winner = team)                                AS wins,
    ROUND(100.0 * SUM(winner = team) / COUNT(*), 1)   AS win_pct
FROM appearances
GROUP BY team
HAVING COUNT(*) >= 50
ORDER BY win_pct DESC;
