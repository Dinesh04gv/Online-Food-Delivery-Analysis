import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from datetime import date

st.set_page_config(
    page_title="Online Food Delivery Analytics",
    page_icon="🍔",
    layout="wide"
)

st.title("🍔 Online Food Delivery Analytics Dashboard")
st.caption("Business insights from MySQL | 100,000-order dataset")

# ---------------- DATABASE CONNECTION ----------------

st.sidebar.header("MySQL Connection")

host = st.sidebar.text_input("Host", "localhost")
user = st.sidebar.text_input("MySQL Username", "root")
password = st.sidebar.text_input("MySQL Password", type="password")
database = st.sidebar.text_input("Database", "food_delivery_db")

@st.cache_data(ttl=300, show_spinner="Loading data from MySQL...")
def load_data(host, user, password, database):
    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    try:
        df = pd.read_sql("SELECT * FROM food_delivery", conn)
    finally:
        conn.close()

    df.columns = df.columns.str.strip()
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")

    numeric_columns = [
        "Customer_Age", "Delivery_Time_Min", "Distance_km",
        "Order_Value", "Discount_Applied", "Final_Amount",
        "Delivery_Rating", "Restaurant_Rating", "Profit_Margin"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


if not password:
    st.info("Enter your MySQL password in the sidebar to connect to your database.")
    st.stop()

try:
    df = load_data(host, user, password, database)
except Exception as e:
    st.error(f"Could not connect to MySQL: {e}")
    st.info("Check your MySQL password, database name, and table name.")
    st.stop()

if df.empty:
    st.warning("No records found in the food_delivery table.")
    st.stop()

# ---------------- SIDEBAR FILTERS ----------------

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

def options_for(column):
    return sorted(df[column].dropna().astype(str).unique().tolist())

cities = options_for("City")
cuisines = options_for("Cuisine_Type")
statuses = options_for("Order_Status")

selected_cities = st.sidebar.multiselect(
    "City", cities, default=cities
)
selected_cuisines = st.sidebar.multiselect(
    "Cuisine", cuisines, default=cuisines
)
selected_statuses = st.sidebar.multiselect(
    "Order Status", statuses, default=statuses
)

valid_dates = df["Order_Date"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

filtered = df[
    df["City"].astype(str).isin(selected_cities)
    & df["Cuisine_Type"].astype(str).isin(selected_cuisines)
    & df["Order_Status"].astype(str).isin(selected_statuses)
].copy()

if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["Order_Date"].isna()
        | (
            (filtered["Order_Date"].dt.date >= start_date)
            & (filtered["Order_Date"].dt.date <= end_date)
        )
    ]

if filtered.empty:
    st.warning("No orders match the selected filters.")
    st.stop()

# ---------------- HELPER FUNCTIONS ----------------

def money(value):
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.2f}"

def profit_percent(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    avg = values.mean()
    # Values stored as fractions such as 0.1498 represent 14.98%.
    if values.abs().max() <= 1:
        avg *= 100
    return avg

def show_chart(fig):
    st.plotly_chart(fig, use_container_width=True)

def section_title(number, title):
    st.subheader(f"{number}. {title}")

# ---------------- KPI CALCULATIONS ----------------

total_orders = len(filtered)

recorded_revenue = filtered["Final_Amount"].sum(min_count=1)

average_order_value = filtered["Final_Amount"].mean()

average_delivery_time = filtered["Delivery_Time_Min"].mean()

cancelled_count = (
    filtered["Order_Status"].astype(str).str.strip().str.lower()
    .eq("cancelled").sum()
)

cancellation_rate = (
    cancelled_count / total_orders * 100 if total_orders else 0
)

average_delivery_rating = filtered["Delivery_Rating"].mean()

avg_profit_margin = profit_percent(filtered["Profit_Margin"])

st.caption(
    f"Showing {total_orders:,} orders matching your filters. "
    "Revenue includes recorded Final_Amount values only."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Orders", f"{total_orders:,}")
k2.metric("Recorded Revenue", money(recorded_revenue))
k3.metric("Average Order Value", money(average_order_value))
k4.metric(
    "Average Delivery Time",
    f"{average_delivery_time:.2f} min"
    if pd.notna(average_delivery_time) else "N/A"
)

k5, k6, k7 = st.columns(3)
k5.metric("Cancellation Rate", f"{cancellation_rate:.2f}%")
k6.metric(
    "Average Delivery Rating",
    f"{average_delivery_rating:.2f} / 5"
    if pd.notna(average_delivery_rating) else "N/A"
)
k7.metric(
    "Average Profit Margin",
    f"{avg_profit_margin:.2f}%"
    if avg_profit_margin is not None else "N/A"
)

st.divider()

# ---------------- 15 ANALYSIS QUERIES ----------------

tabs = st.tabs([
    "Customers",
    "Orders & Revenue",
    "Delivery",
    "Restaurants & Cuisine",
    "Cancellations & Payments"
])

# TAB 1: CUSTOMERS

with tabs[0]:
    section_title(1, "Top-Spending Customers")

    customer_data = (
        filtered.dropna(subset=["Customer_ID"])
        .groupby("Customer_ID")
        .agg(
            Total_Orders=("Order_ID", "nunique"),
            Recorded_Spending=("Final_Amount", "sum")
        )
        .sort_values("Recorded_Spending", ascending=False)
        .head(10)
        .reset_index()
    )

    st.dataframe(customer_data, use_container_width=True, hide_index=True)

    section_title(2, "Age Group vs Order Value")

    age_data = filtered.dropna(subset=["Age_Group", "Order_Value"])
    if not age_data.empty:
        age_summary = (
            age_data.groupby("Age_Group", as_index=False)
            .agg(
                Orders=("Order_ID", "nunique"),
                Average_Order_Value=("Order_Value", "mean")
            )
            .sort_values("Average_Order_Value", ascending=False)
        )
        show_chart(px.bar(
            age_summary, x="Age_Group", y="Average_Order_Value",
            color="Age_Group", title="Average Order Value by Age Group"
        ))
        st.dataframe(age_summary, use_container_width=True, hide_index=True)
    else:
        st.info("No age-group/order-value data available.")

    section_title(3, "Weekend vs Weekday Order Patterns")

    if "Order_Day" in filtered.columns:
        day = filtered["Order_Day"].astype(str).str.strip().str.lower()
        weekend_days = ["saturday", "sunday"]
        weekend_summary = filtered.assign(
            Day_Type=day.map(
                lambda x: "Weekend" if x in weekend_days
                else "Weekday" if x in [
                    "monday", "tuesday", "wednesday",
                    "thursday", "friday"
                ] else "Unknown"
            )
        )
        weekend_summary = (
            weekend_summary.groupby("Day_Type", as_index=False)
            .agg(Orders=("Order_ID", "nunique"))
        )
        show_chart(px.bar(
            weekend_summary, x="Day_Type", y="Orders",
            color="Day_Type", title="Weekend vs Weekday Orders"
        ))
        st.dataframe(weekend_summary, use_container_width=True, hide_index=True)

# TAB 2: ORDERS & REVENUE

with tabs[1]:
    section_title(4, "Monthly Revenue Trends")

    monthly = filtered.dropna(subset=["Order_Date"]).copy()
    monthly["Month"] = monthly["Order_Date"].dt.to_period("M").astype(str)
    monthly_summary = (
        monthly.groupby("Month", as_index=False)
        .agg(Recorded_Revenue=("Final_Amount", "sum"))
    )

    if not monthly_summary.empty:
        show_chart(px.line(
            monthly_summary, x="Month", y="Recorded_Revenue",
            markers=True, title="Monthly Recorded Revenue"
        ))
        st.dataframe(monthly_summary, use_container_width=True, hide_index=True)

    section_title(5, "Discount Impact on Profit")

    discount_data = filtered.dropna(
        subset=["Discount_Applied", "Profit_Margin"]
    )
    if not discount_data.empty:
        discount_summary = (
            discount_data.groupby("Discount_Applied", as_index=False)
            .agg(
                Orders=("Order_ID", "nunique"),
                Average_Profit_Margin=("Profit_Margin", "mean")
            )
        )
        show_chart(px.scatter(
            discount_data, x="Discount_Applied", y="Profit_Margin",
            title="Discount Applied vs Profit Margin",
            opacity=0.45
        ))
        st.dataframe(discount_summary, use_container_width=True, hide_index=True)

    section_title(6, "High-Revenue Cities and Cuisines")

    c1, c2 = st.columns(2)

    with c1:
        city_revenue = (
            filtered.groupby("City", as_index=False)
            .agg(Recorded_Revenue=("Final_Amount", "sum"))
            .sort_values("Recorded_Revenue", ascending=False)
            .head(10)
        )
        show_chart(px.bar(
            city_revenue, x="Recorded_Revenue", y="City",
            orientation="h", title="Top 10 Cities by Recorded Revenue"
        ))

    with c2:
        cuisine_revenue = (
            filtered[filtered["Cuisine_Type"].astype(str).str.lower() != "unknown"]
            .groupby("Cuisine_Type", as_index=False)
            .agg(Recorded_Revenue=("Final_Amount", "sum"))
            .sort_values("Recorded_Revenue", ascending=False)
            .head(10)
        )
        show_chart(px.bar(
            cuisine_revenue, x="Recorded_Revenue", y="Cuisine_Type",
            orientation="h", title="Top 10 Cuisines by Recorded Revenue"
        ))

# TAB 3: DELIVERY

with tabs[2]:
    section_title(7, "Average Delivery Time by City")

    city_delivery = (
        filtered.groupby("City", as_index=False)
        .agg(
            Average_Delivery_Minutes=("Delivery_Time_Min", "mean"),
            Orders=("Order_ID", "nunique")
        )
        .sort_values("Average_Delivery_Minutes", ascending=False)
        .head(15)
    )
    show_chart(px.bar(
        city_delivery, x="City", y="Average_Delivery_Minutes",
        title="Average Delivery Time by City"
    ))
    st.dataframe(city_delivery, use_container_width=True, hide_index=True)

    section_title(8, "Distance vs Delivery Time")

    distance_data = filtered.dropna(
        subset=["Distance_km", "Delivery_Time_Min"]
    )
    if not distance_data.empty:
        show_chart(px.scatter(
            distance_data, x="Distance_km", y="Delivery_Time_Min",
            title="Delivery Distance vs Delivery Time",
            opacity=0.4, trendline="ols"
        ))
        st.caption(
            "Delivery time is used as a proxy for delay because the table "
            "does not contain a promised delivery time."
        )

    section_title(9, "Delivery Rating vs Delivery Time")

    rating_data = filtered.dropna(
        subset=["Delivery_Rating", "Delivery_Time_Min"]
    )
    if not rating_data.empty:
        rating_summary = (
            rating_data.groupby("Delivery_Rating", as_index=False)
            .agg(
                Average_Delivery_Time=("Delivery_Time_Min", "mean"),
                Rating_Count=("Order_ID", "nunique")
            )
        )
        show_chart(px.scatter(
            rating_summary, x="Delivery_Rating",
            y="Average_Delivery_Time", size="Rating_Count",
            title="Delivery Rating vs Average Delivery Time"
        ))
        st.dataframe(rating_summary, use_container_width=True, hide_index=True)

# TAB 4: RESTAURANTS & CUISINE

with tabs[3]:
    section_title(10, "Top-Rated Restaurants")

    restaurant_ratings = filtered.dropna(
        subset=["Restaurant_Name", "Restaurant_Rating"]
    )
    if not restaurant_ratings.empty:
        top_restaurants = (
            restaurant_ratings.groupby("Restaurant_Name", as_index=False)
            .agg(
                Average_Rating=("Restaurant_Rating", "mean"),
                Rating_Count=("Restaurant_Rating", "count")
            )
        )
        top_restaurants = top_restaurants[
            top_restaurants["Rating_Count"] >= 20
        ].sort_values("Average_Rating", ascending=False).head(10)

        show_chart(px.bar(
            top_restaurants, x="Average_Rating", y="Restaurant_Name",
            orientation="h", title="Top-Rated Restaurants (Minimum 20 Ratings)"
        ))
        st.dataframe(top_restaurants, use_container_width=True, hide_index=True)
    else:
        st.info("No valid restaurant ratings available.")

    section_title(11, "Cancellation Rate by Restaurant")

    restaurant_cancel = filtered.copy()
    restaurant_cancel["Is_Cancelled"] = (
        restaurant_cancel["Order_Status"].astype(str).str.strip().str.lower()
        == "cancelled"
    )
    cancellation_by_restaurant = (
        restaurant_cancel.groupby("Restaurant_Name", dropna=False)
        .agg(
            Total_Orders=("Order_ID", "nunique"),
            Cancelled_Orders=("Is_Cancelled", "sum")
        )
        .reset_index()
    )
    cancellation_by_restaurant = cancellation_by_restaurant[
        cancellation_by_restaurant["Total_Orders"] >= 20
    ]
    cancellation_by_restaurant["Cancellation_Rate_Percent"] = (
        cancellation_by_restaurant["Cancelled_Orders"]
        / cancellation_by_restaurant["Total_Orders"] * 100
    )
    cancellation_by_restaurant = cancellation_by_restaurant.sort_values(
        "Cancellation_Rate_Percent", ascending=False
    ).head(10)

    show_chart(px.bar(
        cancellation_by_restaurant, x="Cancellation_Rate_Percent",
        y="Restaurant_Name", orientation="h",
        title="Highest Restaurant Cancellation Rates (Minimum 20 Orders)"
    ))
    st.dataframe(
        cancellation_by_restaurant,
        use_container_width=True, hide_index=True
    )

    section_title(12, "Cuisine-Wise Performance")

    cuisine_data = filtered[
        filtered["Cuisine_Type"].astype(str).str.lower() != "unknown"
    ]
    cuisine_summary = (
        cuisine_data.groupby("Cuisine_Type", as_index=False)
        .agg(
            Total_Orders=("Order_ID", "nunique"),
            Average_Delivery_Time=("Delivery_Time_Min", "mean"),
            Average_Restaurant_Rating=("Restaurant_Rating", "mean"),
            Recorded_Revenue=("Final_Amount", "sum")
        )
    )

    cuisine_profit = cuisine_data.groupby("Cuisine_Type")["Profit_Margin"].mean()
    cuisine_summary["Average_Profit_Margin"] = (
        cuisine_summary["Cuisine_Type"].map(cuisine_profit)
    )
    st.dataframe(cuisine_summary, use_container_width=True, hide_index=True)

    show_chart(px.bar(
        cuisine_summary.sort_values("Recorded_Revenue", ascending=False).head(10),
        x="Cuisine_Type", y="Recorded_Revenue",
        title="Cuisine-Wise Recorded Revenue"
    ))

# TAB 5: CANCELLATIONS & PAYMENTS

with tabs[4]:
    section_title(13, "Peak-Hour Demand")

    peak_data = filtered.copy()
    peak_data["Peak_Hour_Label"] = (
        peak_data["Peak_Hour"].fillna("Unknown").astype(str).str.strip()
        .replace({"1": "Peak Hour", "0": "Non-Peak Hour",
                  "True": "Peak Hour", "False": "Non-Peak Hour"})
    )
    peak_summary = (
        peak_data.groupby("Peak_Hour_Label", as_index=False)
        .agg(Orders=("Order_ID", "nunique"))
    )

    show_chart(px.bar(
        peak_summary, x="Peak_Hour_Label", y="Orders",
        color="Peak_Hour_Label", title="Orders by Peak-Hour Classification"
    ))
    st.dataframe(peak_summary, use_container_width=True, hide_index=True)

    section_title(14, "Payment Mode Preferences")

    payment_summary = (
        filtered.assign(
            Payment_Mode=filtered["Payment_Mode"].fillna("Unknown")
        )
        .groupby("Payment_Mode", as_index=False)
        .agg(
            Orders=("Order_ID", "nunique"),
            Recorded_Revenue=("Final_Amount", "sum")
        )
    )
    payment_summary["Order_Percentage"] = (
        payment_summary["Orders"] / total_orders * 100
    )

    c1, c2 = st.columns(2)
    with c1:
        show_chart(px.pie(
            payment_summary, names="Payment_Mode", values="Orders",
            title="Payment Mode Share"
        ))
    with c2:
        show_chart(px.bar(
            payment_summary, x="Payment_Mode", y="Recorded_Revenue",
            title="Recorded Revenue by Payment Mode"
        ))
    st.dataframe(payment_summary, use_container_width=True, hide_index=True)

    section_title(15, "Cancellation Reason Analysis")

    cancelled = filtered[
        filtered["Order_Status"].astype(str).str.strip().str.lower()
        == "cancelled"
    ].copy()

    if not cancelled.empty:
        cancelled["Cancellation_Reason"] = (
            cancelled["Cancellation_Reason"].fillna("Unknown")
        )
        reasons = (
            cancelled.groupby("Cancellation_Reason", as_index=False)
            .agg(Cancelled_Orders=("Order_ID", "nunique"))
            .sort_values("Cancelled_Orders", ascending=False)
        )
        reasons["Percentage_of_Cancellations"] = (
            reasons["Cancelled_Orders"] / len(cancelled) * 100
        )

        show_chart(px.bar(
            reasons, x="Cancellation_Reason", y="Cancelled_Orders",
            title="Cancellation Reasons"
        ))
        st.dataframe(reasons, use_container_width=True, hide_index=True)
    else:
        st.info("No cancelled orders match the selected filters.")

# ---------------- DATA PREVIEW & DOWNLOAD ----------------

st.divider()
with st.expander("View filtered dataset"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.download_button(
    "Download Filtered Data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="food_delivery_filtered.csv",
    mime="text/csv"
)

st.caption("Data source: MySQL food_delivery_db.food_delivery")