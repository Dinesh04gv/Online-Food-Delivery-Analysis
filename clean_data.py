import os
import pandas as pd
import numpy as np

# ============================================================
# 1. CONFIGURATION
# ============================================================

INPUT_FILE = "ONINE_FOOD_DELIVERY_ANALYSIS.csv"
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

CLEANED_FILE = os.path.join(
    OUTPUT_DIR, "cleaned_food_delivery.csv"
)
REPORT_FILE = os.path.join(
    OUTPUT_DIR, "cleaning_report.csv"
)
SUMMARY_FILE = os.path.join(
    OUTPUT_DIR, "cleaning_summary.txt"
)

print("=" * 65)
print("ONLINE FOOD DELIVERY - DATA CLEANING")
print("=" * 65)

# ============================================================
# 2. LOAD DATASET
# ============================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Dataset not found: {INPUT_FILE}\n"
        "Place the CSV file in the same folder as clean_data.py."
    )

df = pd.read_csv(INPUT_FILE)

original_rows = len(df)
original_columns = len(df.columns)

print("\nOriginal dataset loaded successfully!")
print("Rows:", original_rows)
print("Columns:", original_columns)

# Keep an original copy for the cleaning report.
original_df = df.copy()

# ============================================================
# 3. REMOVE DUPLICATES
# ============================================================

duplicate_rows = int(df.duplicated().sum())
duplicate_order_ids = int(df["Order_ID"].duplicated().sum())

print("\nDuplicate rows found:", duplicate_rows)
print("Duplicate Order IDs found:", duplicate_order_ids)

df = df.drop_duplicates()

# Order_ID should uniquely identify an order.
# Keep the first occurrence if duplicate IDs exist.
df = df.drop_duplicates(subset=["Order_ID"], keep="first")

# ============================================================
# 4. CLEAN TEXT COLUMNS
# ============================================================

text_columns = df.select_dtypes(
    include=["object", "str", "string"]
).columns.tolist()

for col in text_columns:
    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

# Standardize selected category columns.
title_columns = [
    "Customer_Gender",
    "City",
    "Cuisine_Type",
    "Payment_Mode",
    "Order_Status",
    "Order_Day"
]

for col in title_columns:
    if col in df.columns:
        df[col] = df[col].str.title()

# Standardize city spelling.
if "City" in df.columns:
    df["City"] = df["City"].replace({
        "Bengaluru": "Bangalore"
    })

# ============================================================
# 5. CLEAN DATE AND TIME
# ============================================================

# Parse dates without inventing dates for missing values.
df["Order_Date"] = pd.to_datetime(
    df["Order_Date"],
    errors="coerce"
)

# The source has values such as "0:00".
# Parse times but do not use them to invent peak-hour patterns.
raw_time = df["Order_Time"].astype("string").str.strip()

parsed_time = pd.to_datetime(
    raw_time,
    format="%H:%M",
    errors="coerce"
)

# Try additional common formats for values not parsed above.
for time_format in [
    "%H:%M:%S",
    "%I:%M %p",
    "%I:%M:%S %p"
]:
    missing_time = parsed_time.isna() & raw_time.notna()

    if missing_time.any():
        parsed_time.loc[missing_time] = pd.to_datetime(
            raw_time.loc[missing_time],
            format=time_format,
            errors="coerce"
        )

df["Order_Time"] = parsed_time.dt.strftime("%H:%M:%S")
df["Order_Time"] = df["Order_Time"].astype("string")

print("\nDate and time conversion completed.")

# ============================================================
# 6. CONVERT NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "Customer_Age",
    "Delivery_Time_Min",
    "Distance_km",
    "Order_Value",
    "Discount_Applied",
    "Final_Amount",
    "Delivery_Rating",
    "Restaurant_Rating",
    "Profit_Margin"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

# ============================================================
# 7. HANDLE INVALID VALUES
# ============================================================

# Customer age must be between 18 and 100 for this dataset.
df.loc[
    ~df["Customer_Age"].between(18, 100),
    "Customer_Age"
] = np.nan

# Delivery and restaurant ratings must be between 1 and 5.
invalid_delivery_ratings = int(
    (~df["Delivery_Rating"].between(1, 5)).sum()
)

invalid_restaurant_ratings = int(
    (~df["Restaurant_Rating"].between(1, 5)).sum()
)

df.loc[
    ~df["Delivery_Rating"].between(1, 5),
    "Delivery_Rating"
] = np.nan

df.loc[
    ~df["Restaurant_Rating"].between(1, 5),
    "Restaurant_Rating"
] = np.nan

print(
    "Invalid delivery ratings marked missing:",
    invalid_delivery_ratings
)
print(
    "Invalid restaurant ratings marked missing:",
    invalid_restaurant_ratings
)

# Negative operational values are invalid.
# Do not automatically remove negative profit margins:
# they can represent genuine business losses.
nonnegative_columns = [
    "Delivery_Time_Min",
    "Distance_km",
    "Order_Value",
    "Discount_Applied",
    "Final_Amount"
]

invalid_counts = {}

for col in nonnegative_columns:
    invalid_mask = df[col] < 0
    invalid_counts[col] = int(invalid_mask.sum())
    df.loc[invalid_mask, col] = np.nan

for col, count in invalid_counts.items():
    print(f"Invalid negative {col} values: {count}")

# ============================================================
# 8. HANDLE MISSING CATEGORICAL VALUES
# ============================================================

categorical_columns = [
    "Customer_Gender",
    "City",
    "Area",
    "Cuisine_Type",
    "Payment_Mode"
]

for col in categorical_columns:
    df[col] = df[col].fillna("Unknown")

# ============================================================
# 9. HANDLE MISSING NUMERIC VALUES
# ============================================================

# Fill age using the median.
df["Customer_Age"] = df["Customer_Age"].fillna(
    df["Customer_Age"].median()
)

# Use delivered orders to estimate missing delivery times
# and distances, then fall back to the full-column median.
delivered_mask = df["Order_Status"].eq("Delivered")

for col in ["Delivery_Time_Min", "Distance_km"]:
    delivered_median = df.loc[
        delivered_mask, col
    ].median()

    overall_median = df[col].median()

    fill_value = (
        delivered_median
        if pd.notna(delivered_median)
        else overall_median
    )

    if pd.notna(fill_value):
        df[col] = df[col].fillna(fill_value)

# Fill missing order values using the median within each
# order-status group, then use the overall median.
overall_order_median = df["Order_Value"].median()

status_medians = df.groupby(
    "Order_Status"
)["Order_Value"].transform("median")

df["Order_Value"] = df["Order_Value"].fillna(
    status_medians
)

df["Order_Value"] = df["Order_Value"].fillna(
    overall_order_median
)

# Fill missing discounts with the median.
discount_median = df["Discount_Applied"].median()

if pd.notna(discount_median):
    df["Discount_Applied"] = df[
        "Discount_Applied"
    ].fillna(discount_median)

# IMPORTANT:
# Do not fill Final_Amount with zero or calculate it blindly.
# Missing amounts are retained until their business meaning
# and calculation rules are verified.

# ============================================================
# 10. CLEAN CANCELLATION REASONS
# ============================================================

cancelled_mask = df["Order_Status"].eq("Cancelled")
delivered_mask = df["Order_Status"].eq("Delivered")

# A missing reason for a cancelled order is unknown,
# not proof of any particular cancellation reason.
df.loc[
    cancelled_mask & df["Cancellation_Reason"].isna(),
    "Cancellation_Reason"
] = "Unknown"

# Delivered orders should not have a cancellation reason.
df.loc[
    delivered_mask,
    "Cancellation_Reason"
] = pd.NA

# ============================================================
# 11. PRESERVE ORIGINAL PEAK_HOUR VALUES
# ============================================================

# The source contains only "0:00" for recorded order times.
# Therefore, do not derive Peak_Hour from Order_Time.
# Preserve the source flags instead.

peak = (
    original_df["Peak_Hour"]
    .astype("string")
    .str.strip()
    .str.lower()
)

# Align the original peak-hour values to the retained rows.
# This mapping is safe because Order_ID uniquely identifies
# each original order after duplicate IDs are resolved.
peak_lookup = pd.DataFrame({
    "Order_ID": original_df["Order_ID"],
    "_Original_Peak_Hour": peak
}).drop_duplicates(
    subset=["Order_ID"], keep="first"
)

peak_lookup["_Original_Peak_Hour"] = (
    peak_lookup["_Original_Peak_Hour"].map({
        "true": True,
        "false": False
    }).astype("boolean")
)

df = df.drop(columns=["Peak_Hour"], errors="ignore")

df = df.merge(
    peak_lookup,
    on="Order_ID",
    how="left",
    validate="one_to_one"
)

df = df.rename(columns={
    "_Original_Peak_Hour": "Peak_Hour"
})

# ============================================================
# 12. RECALCULATE ORDER DAY FROM VALID DATES
# ============================================================

# Keep the original value if the date is missing.
# Recalculate only where Order_Date is available.
valid_date_mask = df["Order_Date"].notna()

df.loc[valid_date_mask, "Order_Day"] = np.where(
    df.loc[valid_date_mask, "Order_Date"].dt.dayofweek >= 5,
    "Weekend",
    "Weekday"
)

# ============================================================
# 13. ADD ANALYSIS COLUMNS
# ============================================================

# Age groups.
age_bins = [17, 25, 35, 45, 55, 100]
age_labels = [
    "18-25",
    "26-35",
    "36-45",
    "46-55",
    "56+"
]

df["Age_Group"] = pd.cut(
    df["Customer_Age"],
    bins=age_bins,
    labels=age_labels
).astype("string")

# Delivery performance groups.
df["Delivery_Performance"] = np.select(
    [
        df["Delivery_Time_Min"] <= 30,
        df["Delivery_Time_Min"].between(
            30, 60, inclusive="right"
        ),
        df["Delivery_Time_Min"] > 60
    ],
    [
        "Fast",
        "Moderate",
        "Slow"
    ],
    default="Unknown"
)

# Validate final amount only when sufficient values exist.
# This is a review flag, not a claim that all other records
# have been financially verified.
amount_check = pd.Series(
    "Review",
    index=df.index,
    dtype="string"
)

valid_amount_mask = (
    df["Final_Amount"].notna()
    & df["Order_Value"].notna()
    & df["Discount_Applied"].notna()
    & (df["Final_Amount"] >= 0)
    & (df["Final_Amount"] <= df["Order_Value"])
)

amount_check.loc[valid_amount_mask] = "Pass"

df["Amount_Check"] = amount_check

# ============================================================
# 14. PREPARE CLEANING REPORT
# ============================================================

original_missing = original_df.isna().sum()
cleaned_missing = df.isna().sum()

all_columns = sorted(
    set(original_df.columns).union(df.columns)
)

report_rows = []

for col in all_columns:
    report_rows.append({
        "Column": col,
        "Original_Missing": int(
            original_missing.get(col, 0)
        ),
        "Cleaned_Missing": int(
            cleaned_missing.get(col, 0)
        ),
        "Original_Dtype": str(
            original_df[col].dtype
            if col in original_df.columns
            else "New column"
        ),
        "Cleaned_Dtype": str(
            df[col].dtype
            if col in df.columns
            else "Removed"
        )
    })

cleaning_report = pd.DataFrame(report_rows)

# ============================================================
# 15. SAVE OUTPUT FILES
# ============================================================

# Save dates and times in consistent text formats.
df["Order_Date"] = df["Order_Date"].dt.strftime(
    "%Y-%m-%d"
)

df.to_csv(
    CLEANED_FILE,
    index=False,
    na_rep=""
)

cleaning_report.to_csv(
    REPORT_FILE,
    index=False
)

summary_lines = [
    "ONLINE FOOD DELIVERY - CLEANING SUMMARY",
    "=" * 45,
    f"Original rows: {original_rows}",
    f"Final rows: {len(df)}",
    f"Original columns: {original_columns}",
    f"Final columns: {len(df.columns)}",
    f"Duplicate rows found: {duplicate_rows}",
    f"Duplicate Order IDs found: {duplicate_order_ids}",
    f"Invalid delivery ratings: {invalid_delivery_ratings}",
    f"Invalid restaurant ratings: {invalid_restaurant_ratings}",
    f"Missing order dates: {int(df['Order_Date'].isna().sum())}",
    f"Missing order times: {int(df['Order_Time'].isna().sum())}",
    f"Missing final amounts: {int(df['Final_Amount'].isna().sum())}",
    f"Negative profit margins preserved: {int((df['Profit_Margin'] < 0).sum())}",
    f"Amount checks requiring review: {int(df['Amount_Check'].eq('Review').sum())}",
    "",
    "Missing values by column:",
    df.isna().sum().to_string(),
    "",
    "Files created:",
    CLEANED_FILE,
    REPORT_FILE,
    SUMMARY_FILE
]

with open(
    SUMMARY_FILE,
    "w",
    encoding="utf-8"
) as file:
    file.write("\n".join(summary_lines))

# ============================================================
# 16. DISPLAY FINAL RESULTS
# ============================================================

print("\n" + "=" * 65)
print("CLEANING COMPLETED SUCCESSFULLY")
print("=" * 65)

print(f"Original_Rows: {original_rows}")
print(f"Final_Rows: {len(df)}")
print(f"Original_Columns: {original_columns}")
print(f"Final_Columns: {len(df.columns)}")
print(f"Duplicate_Rows_Found: {duplicate_rows}")
print(f"Duplicate_Order_IDs_Found: {duplicate_order_ids}")
print(f"Invalid_Restaurant_Ratings: {invalid_restaurant_ratings}")
print(f"Invalid_Delivery_Ratings: {invalid_delivery_ratings}")
print(f"Missing_Order_Dates: {df['Order_Date'].isna().sum()}")
print(f"Missing_Order_Times: {df['Order_Time'].isna().sum()}")
print(f"Missing_Final_Amounts: {df['Final_Amount'].isna().sum()}")
print(
    "Negative_Profit_Margins_Preserved:",
    int((df["Profit_Margin"] < 0).sum())
)
print(
    "Amount_Check_Review:",
    int(df["Amount_Check"].eq("Review").sum())
)

print("\nRemaining missing values:")
print(df.isna().sum().to_string())

print("\nFiles created:")
print(CLEANED_FILE)
print(REPORT_FILE)
print(SUMMARY_FILE)

print("\nCleaned dataset preview:")
print(df.head().to_string(index=False))

print("\nCleaning report saved successfully.")