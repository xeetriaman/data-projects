-- How did the median Sydney house price move through 2018?
-- Quarters with fewer than 1,000 recorded sales are left out (the file only holds sales settled in 2018).
SELECT strftime('%Y', contract_date) || '-Q' || ((CAST(strftime('%m', contract_date) AS INTEGER) + 2) / 3) AS quarter,
       n AS sales,
       price AS median_price
FROM (
    SELECT contract_date, price,
           ROW_NUMBER() OVER (PARTITION BY strftime('%Y', contract_date) || ((CAST(strftime('%m', contract_date) AS INTEGER) + 2) / 3) ORDER BY price) AS rn,
           COUNT(*) OVER (PARTITION BY strftime('%Y', contract_date) || ((CAST(strftime('%m', contract_date) AS INTEGER) + 2) / 3)) AS n
    FROM sales
)
WHERE rn = (n + 1) / 2 AND n >= 1000
ORDER BY quarter;
