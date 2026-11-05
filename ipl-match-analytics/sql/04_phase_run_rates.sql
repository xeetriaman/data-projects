-- Run rate per over in each phase, before and after the 2023 Impact Player rule
SELECT
    CASE WHEN season >= 2023 THEN '2023 onwards' ELSE '2008-2022' END  AS era,
    phase,
    ROUND(6.0 * SUM(runs) / SUM(balls), 2)                             AS run_rate,
    ROUND(6.0 * SUM(wickets) / SUM(balls), 2)                          AS wickets_per_over
FROM phases
GROUP BY era, phase
ORDER BY era, CASE phase WHEN 'powerplay' THEN 1 WHEN 'middle' THEN 2 ELSE 3 END;
