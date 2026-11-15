-- Change in turnover in August 2021 (Sydney's Delta lockdown) against August 2019, by industry.
SELECT a.industry,
       ROUND(b.turnover_m, 1) AS aug_2019_m,
       ROUND(a.turnover_m, 1) AS aug_2021_m,
       ROUND(100.0 * (a.turnover_m / b.turnover_m - 1), 1) AS change_pct
FROM retail AS a
JOIN retail AS b ON b.industry = a.industry AND b.month = '2019-08-01'
WHERE a.month = '2021-08-01'
ORDER BY change_pct;
