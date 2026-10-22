🍔 Online Food Delivery Analysis

📌 Project Overview

The Online Food Delivery Analysis project analyzes food delivery order data to identify business trends, customer preferences, restaurant performance, delivery efficiency, and cancellation patterns.

The project uses Python for data cleaning, MySQL for data storage and SQL analysis, and Streamlit with Plotly for an interactive dashboard.

🎯 Project Objectives

- Clean and prepare the food delivery dataset.
- Store the cleaned data in a MySQL database.
- Perform 15 SQL business analysis queries.
- Build an interactive dashboard to monitor key performance indicators (KPIs).
- Identify trends and provide data-driven business recommendations.

🛠️ Technologies Used

- Python — Data cleaning and analysis
- Pandas — Data manipulation
- MySQL — Database management and SQL queries
- Streamlit — Interactive dashboard
- Plotly — Data visualization

📂 Project Files

File| Description
"app.py"| Streamlit dashboard application
"requirements.txt"| Required Python libraries
"analysis_queries.sql"| SQL queries for business analysis
"clean_data.py"| Data cleaning script
"README.md"| Project documentation

🧹 Data Cleaning

The dataset was checked and cleaned to improve data quality.

Key cleaning activities included:

- Checking for duplicate orders.
- Handling missing customer ages using median imputation.
- Handling missing categorical values.
- Identifying invalid restaurant ratings.
- Converting invalid negative final amounts to missing values.
- Preserving negative profit margins because they can represent business losses.
- Creating derived features such as "Age_Group", "Delivery_Performance", and "Amount_Check".

Missing revenue amounts and ratings were not arbitrarily filled with invented values.

🗄️ Database Details

- Database: "food_delivery_db"
- Table: "food_delivery"
- Records: 100,000 orders
- Columns: 28

The table contains customer, restaurant, cuisine, order, delivery, payment, rating, cancellation, and profit-related information.

📊 Key Performance Indicators (KPIs)

The dashboard includes:

1. Total Orders
2. Total Revenue (recorded final amounts)
3. Average Order Value
4. Average Delivery Time
5. Cancellation Rate
6. Average Delivery Rating
7. Profit Margin %

🔍 SQL Analysis — 15 Business Questions

1. Identify the top-spending customers.
2. Analyze age group versus order value.
3. Compare weekend and weekday order patterns.
4. Analyze monthly revenue trends.
5. Evaluate the relationship between discounts and profit.
6. Identify high-revenue cities and cuisines.
7. Calculate average delivery time by city.
8. Analyze delivery distance versus delivery time.
9. Examine delivery ratings versus delivery time.
10. Identify top-rated restaurants.
11. Calculate cancellation rates by restaurant.
12. Compare cuisine-wise performance.
13. Analyze peak-hour demand.
14. Identify customer payment mode preferences.
15. Analyze cancellation reasons.

📈 Dashboard Features

- Interactive city, cuisine, date range, and order status filters.
- KPI cards for key business metrics.
- Revenue trend charts.
- Customer and age-group analysis.
- City and cuisine performance comparisons.
- Delivery time and distance analysis.
- Restaurant rating analysis.
- Cancellation and payment mode visualizations.
- Filtered data preview and CSV export.

🚀 How to Run the Dashboard Locally

1. Clone the repository

git clone https://github.com/YOUR-USERNAME/Online-Food-Delivery-Analysis.git

Replace "YOUR-USERNAME" with your GitHub username.

2. Open the project folder

cd Online-Food-Delivery-Analysis

3. Install dependencies

python -m pip install -r requirements.txt

4. Configure MySQL

Ensure MySQL Server is running and the database "food_delivery_db" contains the "food_delivery" table.

The application currently requests MySQL connection details through the Streamlit sidebar. Never publish your database password in this repository.

5. Start Streamlit

python -m streamlit run app.py

Open the local URL displayed in your terminal, usually "http://localhost:8501".

⚠️ Data Notes

- Revenue calculations use available "Final_Amount" values because some amounts are missing.
- Average ratings use available valid ratings.
- Missing or unknown categories should be interpreted carefully.
- Negative profit margins are retained to reflect potential losses.
- The current dashboard requires an accessible MySQL database. A hosted deployment needs a securely accessible database or another configured data source.

💡 Expected Business Benefits

This analysis can help businesses:

- Understand customer spending patterns.
- Monitor revenue performance.
- Identify restaurants with high cancellation rates.
- Evaluate delivery efficiency.
- Understand cuisine and payment preferences.
- Investigate factors associated with customer ratings.
- Make informed operational and customer-retention decisions.

👩‍💻 Project Type

Data Analytics | SQL | Python | Streamlit Dashboard

---

Note: Update this README if the project files, database setup, or deployment method changes.
