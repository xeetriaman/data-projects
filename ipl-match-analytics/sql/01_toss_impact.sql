-- Does winning the toss help you win the match?
SELECT
    toss_decision                                             AS toss_choice,
    COUNT(*)                                                  AS matches,
    ROUND(100.0 * SUM(toss_winner = winner) / COUNT(*), 1)    AS toss_winner_win_pct
FROM matches
WHERE result != 'no result'
GROUP BY toss_decision
UNION ALL
SELECT 'all', COUNT(*), ROUND(100.0 * SUM(toss_winner = winner) / COUNT(*), 1)
FROM matches
WHERE result != 'no result';
