USE food_delivery_db;

-- 1. Top-spending customers
SELECT
    Customer_ID,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    SUM(Final_Amount) AS Total_Spending
FROM food_delivery
GROUP BY Customer_ID
ORDER BY Total_Spending DESC
LIMIT 10;

-- 2. Age group vs average order value
SELECT
    Age_Group,
    COUNT(*) AS Total_Orders,
    ROUND(AVG(Order_Value), 2) AS Average_Order_Value
FROM food_delivery
GROUP BY Age_Group
ORDER BY Average_Order_Value DESC;

-- 3. Weekend vs weekday order patterns
SELECT
    CASE
        WHEN LOWER(Order_Day) IN ('saturday', 'sunday')
            THEN 'Weekend'
        WHEN LOWER(Order_Day) IN
            ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')
            THEN 'Weekday'
        ELSE 'Unknown'
    END AS Day_Type,
    COUNT(DISTINCT Order_ID) AS Total_Orders
FROM food_delivery
GROUP BY Day_Type;

-- 4. Monthly revenue trends
SELECT
    DATE_FORMAT(Order_Date, '%Y-%m') AS Month,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    SUM(Final_Amount) AS Recorded_Revenue
FROM food_delivery
WHERE Order_Date IS NOT NULL
GROUP BY DATE_FORMAT(Order_Date, '%Y-%m')
ORDER BY Month;

-- 5. Discount impact on profit
SELECT
    Discount_Applied,
    COUNT(*) AS Total_Orders,
    ROUND(AVG(Profit_Margin), 4) AS Average_Profit_Margin
FROM food_delivery
GROUP BY Discount_Applied
ORDER BY Discount_Applied;

-- 6A. Highest-revenue cities
SELECT
    City,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    SUM(Final_Amount) AS Recorded_Revenue
FROM food_delivery
GROUP BY City
ORDER BY Recorded_Revenue DESC
LIMIT 10;

-- 6B. Highest-revenue cuisines
SELECT
    Cuisine_Type,
    COUNT(DISTINCT Order_ID) AS Total_Orders,
    SUM(Final_Amount) AS Recorded_Revenue
FROM food_delivery
WHERE Cuisine_Type IS NOT NULL
  AND LOWER(Cuisine_Type) <> 'unknown'
GROUP BY Cuisine_Type
ORDER BY Recorded_Revenue DESC
LIMIT 10;

-- 7. Average delivery time by city
SELECT
    City,
    COUNT(*) AS Total_Orders,
    ROUND(AVG(Delivery_Time_Min), 2) AS Average_Delivery_Minutes
FROM food_delivery
GROUP BY City
ORDER BY Average_Delivery_Minutes DESC;

-- 8. Distance vs delivery time
SELECT
    Distance_km,
    COUNT(*) AS Total_Orders,
    ROUND(AVG(Delivery_Time_Min), 2) AS Average_Delivery_Minutes
FROM food_delivery
WHERE Distance_km IS NOT NULL
  AND Delivery_Time_Min IS NOT NULL
GROUP BY Distance_km
ORDER BY Distance_km;

-- 9. Delivery rating vs delivery time
SELECT
    Delivery_Rating,
    COUNT(*) AS Total_Orders,
    ROUND(AVG(Delivery_Time_Min), 2) AS Average_Delivery_Minutes
FROM food_delivery
WHERE Delivery_Rating IS NOT NULL
GROUP BY Delivery_Rating
ORDER BY Delivery_Rating;

-- 10. Top-rated restaurants (minimum 20 ratings)
SELECT
    Restaurant_Name,
    COUNT(Restaurant_Rating) AS Rating_Count,
    ROUND(AVG(Restaurant_Rating), 2) AS Average_Rating
FROM food_delivery
WHERE Restaurant_Rating IS NOT NULL
GROUP BY Restaurant_Name
HAVING COUNT(Restaurant_Rating) >= 20
ORDER BY Average_Rating DESC, Rating_Count DESC
LIMIT 10;

-- 11. Cancellation rate by restaurant
SELECT
    Restaurant_Name,
    COUNT(*) AS Total_Orders,
    SUM(
        CASE WHEN LOWER(Order_Status) = 'cancelled'
             THEN 1 ELSE 0 END
    ) AS Cancelled_Orders,
    ROUND(
        100.0 * SUM(
            CASE WHEN LOWER(Order_Status) = 'cancelled'
                 THEN 1 ELSE 0 END
        ) / COUNT(*), 2
    ) AS Cancellation_Rate_Percent
FROM food_delivery
GROUP BY Restaurant_Name
HAVING COUNT(*) >= 20
ORDER BY Cancellation_Rate_Percent DESC
LIMIT 10;

-- 12. Cuisine-wise performance
SELECT
    Cuisine_Type,
    COUNT(*) AS Total_Orders,
    SUM(CASE WHEN LOWER(Order_Status) = 'delivered'
             THEN 1 ELSE 0 END) AS Delivered_Orders,
    SUM(CASE WHEN LOWER(Order_Status) = 'cancelled'
             THEN 1 ELSE 0 END) AS Cancelled_Orders,
    ROUND(AVG(Delivery_Time_Min), 2) AS Average_Delivery_Minutes,
    ROUND(AVG(Restaurant_Rating), 2) AS Average_Restaurant_Rating,
    ROUND(AVG(Profit_Margin), 4) AS Average_Profit_Margin,
    SUM(Final_Amount) AS Recorded_Revenue
FROM food_delivery
GROUP BY Cuisine_Type
ORDER BY Recorded_Revenue DESC;

-- 13. Peak-hour demand
SELECT
    CASE
        WHEN Peak_Hour IN ('1', 'True', 'true') THEN 'Peak Hour'
        WHEN Peak_Hour IN ('0', 'False', 'false') THEN 'Non-Peak Hour'
        ELSE 'Unknown'
    END AS Peak_Category,
    COUNT(*) AS Total_Orders,
    SUM(CASE WHEN LOWER(Order_Status) = 'delivered'
             THEN 1 ELSE 0 END) AS Delivered_Orders,
    SUM(CASE WHEN LOWER(Order_Status) = 'cancelled'
             THEN 1 ELSE 0 END) AS Cancelled_Orders
FROM food_delivery
GROUP BY Peak_Category;

-- 14. Payment mode preferences
SELECT
    COALESCE(NULLIF(Payment_Mode, ''), 'Unknown') AS Payment_Mode,
    COUNT(*) AS Total_Orders,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(*) FROM food_delivery), 2
    ) AS Order_Percentage,
    SUM(Final_Amount) AS Recorded_Revenue
FROM food_delivery
GROUP BY COALESCE(NULLIF(Payment_Mode, ''), 'Unknown')
ORDER BY Total_Orders DESC;

-- 15. Cancellation reasons
SELECT
    COALESCE(NULLIF(Cancellation_Reason, ''), 'Unknown')
        AS Cancellation_Reason,
    COUNT(*) AS Cancelled_Orders,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM food_delivery
         WHERE LOWER(Order_Status) = 'cancelled'),
        2
    ) AS Percentage_Of_Cancellations
FROM food_delivery
WHERE LOWER(Order_Status) = 'cancelled'
GROUP BY COALESCE(NULLIF(Cancellation_Reason, ''), 'Unknown')
ORDER BY Cancelled_Orders DESC;