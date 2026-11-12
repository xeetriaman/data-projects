-- Most and least expensive suburbs by average price per square metre of land (suburbs with 30+ sales).
WITH suburb AS (
    SELECT suburb, COUNT(*) AS sales,
           ROUND(AVG(price * 1.0 / area_sqm)) AS avg_price_per_sqm,
           ROUND(AVG(price)) AS avg_price
    FROM sales
    GROUP BY suburb
    HAVING COUNT(*) >= 30
)
SELECT * FROM (SELECT 'Top 10' AS band, * FROM suburb ORDER BY avg_price_per_sqm DESC LIMIT 10)
UNION ALL
SELECT * FROM (SELECT 'Bottom 10' AS band, * FROM suburb ORDER BY avg_price_per_sqm ASC LIMIT 10);
