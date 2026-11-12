-- Does zoning change what buyers pay for land?
SELECT zoning, COUNT(*) AS sales,
       ROUND(AVG(area_sqm)) AS avg_area_sqm,
       ROUND(AVG(price)) AS avg_price,
       ROUND(AVG(price * 1.0 / area_sqm)) AS avg_price_per_sqm
FROM sales
GROUP BY zoning
HAVING COUNT(*) >= 100
ORDER BY avg_price_per_sqm DESC;
