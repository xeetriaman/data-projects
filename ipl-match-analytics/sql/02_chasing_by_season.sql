-- How often captains choose to field first, and how often chasing actually wins
SELECT
    season,
    COUNT(*)                                                          AS matches,
    ROUND(100.0 * SUM(toss_decision = 'field') / COUNT(*), 1)         AS chose_to_field_pct,
    ROUND(100.0 * SUM(winner = bat_second) / COUNT(*), 1)             AS chasing_win_pct
FROM matches
WHERE result != 'no result'
GROUP BY season
ORDER BY season;
