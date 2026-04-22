import pandas as pd
import glob as gl

#####   WEEK 1   #####
sold_files = sorted(gl.glob("datasets/CRMLSSold*.csv"))

# Concatenate dataframes
df = pd.DataFrame()
rows = 0
for file in sold_files:
    sold_df = pd.read_csv(file, low_memory=False)
    rows += sold_df.shape[0]
    print(f"Loaded {sold_df.shape[0]} rows from {file}, Total: {rows}")
    df = pd.concat([df, sold_df], ignore_index=True)

print(f"{len(sold_files)} files loaded.")
print(f"Shape of dataframe: {df.shape}")
df = pd.DataFrame(df) # to stop PyCharm's future weird DataFrame warnings

# Drop duplicate rows and columns (CloseDate.1, Latitude.1, etc.)
df = df.drop(list(df.filter(regex='.1$')), axis=1)
df = df.drop_duplicates(subset="ListingKey", keep="last")

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
print(f"Columns with missing values for SOLD:\n"
      f"{null_tbl[null_tbl["NullPct"] > 0].to_string()}")

# Filter out non-main fields with high missing count
main_fields = ["ListingKey", "ListingContractDate", "ListPrice", "ClosePrice",
               "PurchaseContractDate", "CloseDate", "LivingArea", "BedroomsTotal",
               "BathroomsTotalInteger", "Latitude", "Longitude", "UnparsedAddress"]

for col in null_tbl[null_tbl["HighNull"]].index:
    if col not in main_fields:
        df = df.drop(col, axis=1)
print(f"New shape of SOLD: {df.shape}")

# Drop rows with date inconsistencies (e.g. CloseDate < ListingContractDate)
date_err = df.query("CloseDate < ListingContractDate | CloseDate < PurchaseContractDate")
df = df.drop(date_err.index)
print(f"SOLD new shape: {df.shape}")

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
df["year_month"] = df["CloseDate"].dt.to_period("M")
df = df.merge(mortgage_monthly, on="year_month", how="left")

# Merge and validate
print(df["rate_30yr_fixed"].isnull().sum())
print(df[["CloseDate", "year_month", "ClosePrice", "rate_30yr_fixed"]].head())


#####   FINAL DATASET   #####
df.to_csv("sold_final.csv", index=False)
print(f"Final sold shape: {df.shape}")
