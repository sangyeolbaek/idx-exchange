import pandas as pd
import glob as gl

#####   WEEK 1   #####
listed_files = sorted(gl.glob("datasets/CRMLSListing*.csv"))

# Concatenate dataframes
df = pd.DataFrame()
rows = 0
for file in listed_files:
    list_df = pd.read_csv(file, low_memory=False)
    rows += list_df.shape[0]
    print(f"Loaded {list_df.shape[0]} rows from {file}, Total: {rows}")
    df = pd.concat([df, list_df], ignore_index=True)

print(f"{len(listed_files)} files loaded.")
print(f"Shape of dataframe: {df.shape}")
df = pd.DataFrame(df) # to stop PyCharm's future weird DataFrame warnings

# Filter to RESIDENTAL properties
df = df[df["PropertyType"] == "Residential"]
print(f"Residental Properties found: {df.shape[0]}")


#####   WEEK 2   #####
date_cols = [col for col in df.columns if "date" in col.lower()]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# Report missingness of dataset
missing = df.isnull().sum()
missing_pct = round(missing / df.shape[0] * 100, 2)
high_null = missing_pct > 90.0
null_tbl = pd.DataFrame({
    "Missing": missing,
    "NullPct": missing_pct,
    "HighNull": high_null
})
null_tbl = null_tbl.sort_values(by="NullPct", ascending=False)
print(f"Columns with missing values for LISTED:\n"
      f"{null_tbl[null_tbl["NullPct"] > 0].to_string()}")

# Filter out non-main fields with high missing count
main_fields = ["ListingKey", "ListingContractDate", "ListPrice", "ClosePrice",
               "PurchaseContractDate", "CloseDate", "LivingArea", "BedroomsTotal",
               "BathroomsTotalInteger", "Latitude", "Longitude", "UnparsedAddress"]

for col in null_tbl[null_tbl["HighNull"]].index:
    if col not in main_fields:
        df = df.drop(col, axis=1)
print(f"New shape of LISTED: {df.shape}")

# Statistical summaries of ClosePrice, LivingArea, and DaysOnMarket
perc = [0.1, 0.25, 0.5, 0.75, 0.9]
print(f"Statistical summaries for ClosePrice, LivingArea, DaysOnMarket:\n"
      f"{df[["ClosePrice", "LivingArea", "DaysOnMarket"]].describe(percentiles=perc).to_string()}")


#####   WEEK 3   #####
# Fetch mortgage data from FRED
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
mortgage = pd.read_csv(url, parse_dates=["observation_date"])
mortgage.columns = ["date", "rate_30yr_fixed"]

# Resample weekly rates to monthly averages
mortgage["year_month"] = mortgage["date"].dt.to_period("M")
mortgage_monthly = (
    mortgage.groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .reset_index()
)

# Create a matching year_month key on the MLS datasets
df["year_month"] = df["ListingContractDate"].dt.to_period("M")
df = df.merge(mortgage_monthly, on="year_month", how="left")

# Merge and validate
print(df["rate_30yr_fixed"].isnull().sum())
print(df[["ListingContractDate", "year_month", "ListPrice", "rate_30yr_fixed"]].head())


#####   WEEKS 4-5   #####
# drop duplicate rows and columns
df = df.drop(list(df.filter(regex='.1$')), axis=1)
df = df.drop_duplicates(subset="ListingKey", keep="last")
df = df.drop("ListingKeyNumeric", axis=1) # ListingKey is already "numeric"

# Validate rows for date consistencies (e.g. ListingContractDate < PurchaseContractDate < CloseDate)
#df["list_after_close_flag"] = df["CloseDate"] < df["ListingContractDate"]
#df["purchase_after_close_flag"] = df["PurchaseContractDate"] < df["ListingContractDate"]
#df["negative_time_flag"] = df["list_after_close_flag"] & df["purchase_after_close_flag"]

# check for invalid data
print(f"Properties with invalid Closing price records: {df[df["ClosePrice"] <= 0.0].shape[0]}") # 0
print(f"Properties with invalid Living Area records: {df[df["LivingArea"] <= 0.0].shape[0]}") # 357
print(f"Properties with invalid Days on Market records: {df[df["DaysOnMarket"] <= 0.0].shape[0]}") # 28917
print(f"Properties with invalid Bathrooms records: {df[df["BathroomsTotalInteger"] < 0].shape[0]}") # 0
print(f"Properties with invalid Bedrooms records: {df[df["BedroomsTotal"] < 0].shape[0]}") # 0

# check for invalid numeric values
num_cols = ["ClosePrice", "LivingArea", "DaysOnMarket", "BedroomsTotal", "BathroomsTotalInteger"]
print("Checking for invalid numeric data values...")
for col in num_cols:
    if col in ["BathroomsTotalInteger", "BedroomsTotal"]:
        print(f"Invalid values for {col}: {df[df[col] < 0].shape[0]}")
    else:
        print(f"Invalid values for {col}: {df[df[col] <= 0].shape[0]}")
# ClosePrice: 1, LivingArea: 144, DaysOnMarket: 15825, BathroomsTotalInteger: 0, BedroomsTotal: 0


#####   FINAL DATASET   #####
df.to_csv("listed_final.csv", index=False)
print(f"Final listing shape: {df.shape}")
