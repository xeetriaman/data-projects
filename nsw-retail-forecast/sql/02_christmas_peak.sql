-- How much bigger December is than an average month, by industry (2024 calendar year).
SELECT industry,
       ROUND(MAX(CASE WHEN strftime('%m', month) = '12' THEN turnover_m END), 1) AS december_m,
       ROUND(AVG(turnover_m), 1) AS average_month_m,
       ROUND(100.0 * (MAX(CASE WHEN strftime('%m', month) = '12' THEN turnover_m END) / AVG(turnover_m) - 1), 1) AS december_lift_pct
FROM retail
WHERE strftime('%Y', month) = '2024'
GROUP BY industry
ORDER BY december_lift_pct DESC;
