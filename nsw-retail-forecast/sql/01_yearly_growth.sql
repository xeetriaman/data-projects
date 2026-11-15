-- Financial-year turnover by industry group, and growth on the year before.
WITH yearly AS (
  SELECT industry,
         CAST(strftime('%Y', month) AS INTEGER) + (CAST(strftime('%m', month) AS INTEGER) >= 7) AS fin_year,
         COUNT(*) AS months,
         SUM(turnover_m) AS turnover_m
  FROM retail
  GROUP BY industry, fin_year
)
SELECT industry,
       fin_year,
       ROUND(turnover_m / 1000, 2) AS turnover_bn,
       ROUND(100.0 * (turnover_m / LAG(turnover_m) OVER (PARTITION BY industry ORDER BY fin_year) - 1), 1) AS growth_pct
FROM yearly
WHERE months = 12 AND fin_year >= 2019
ORDER BY industry, fin_year;
