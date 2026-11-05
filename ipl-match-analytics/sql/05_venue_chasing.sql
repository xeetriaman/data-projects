-- Grounds with at least 30 completed matches: who wins more, the chasing or defending side?
SELECT
    venue,
    COUNT(*)                                                  AS matches,
    ROUND(100.0 * SUM(winner = bat_second) / COUNT(*), 1)     AS chasing_win_pct,
    ROUND(AVG(first_innings_runs), 1)                         AS avg_first_innings
FROM matches
WHERE result != 'no result'
GROUP BY venue
HAVING COUNT(*) >= 30
ORDER BY chasing_win_pct DESC;
