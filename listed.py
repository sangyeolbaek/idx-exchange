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
date_cols = ["CloseDate", "PurchaseContractDate", "ListingContractDate", "ContractStatusChangeDate"]
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
print(f"Shape of LISTED: {df.shape}")
df = df.drop(list(df.filter(regex='.1$')), axis=1)
df = df.drop_duplicates(subset="ListingKey", keep="last")
df = df.drop("ListingKeyNumeric", axis=1) # ListingKey is already "numeric"
print(f"Deleted duplicate rows and columns. New shape: {df.shape}")

# Validate rows for date consistencies (e.g. ListingContractDate < PurchaseContractDate < CloseDate)
df["list_after_close_flag"] = df["CloseDate"] < df["ListingContractDate"]
df["purchase_after_close_flag"] = df["PurchaseContractDate"] < df["ListingContractDate"]
df["negative_time_flag"] = df["list_after_close_flag"] & df["purchase_after_close_flag"]

# check for invalid data
print(f"Properties with invalid Closing price records: {df[df["ClosePrice"] <= 0.0].shape[0]}") # 0
print(f"Properties with invalid Living Area records: {df[df["LivingArea"] <= 0.0].shape[0]}") # 357
print(f"Properties with invalid Days on Market records: {df[df["DaysOnMarket"] <= 0.0].shape[0]}") # 28917
print(f"Properties with invalid Bathrooms records: {df[df["BathroomsTotalInteger"] < 0].shape[0]}") # 0
print(f"Properties with invalid Bedrooms records: {df[df["BedroomsTotal"] < 0].shape[0]}") # 0

# check for invalid numeric values
num_cols = ["ClosePrice", "OriginalListPrice", "LivingArea", "DaysOnMarket", "BedroomsTotal", "BathroomsTotalInteger"]
print("Checking for invalid numeric data values...")
for col in num_cols:
    if col in ["BathroomsTotalInteger", "BedroomsTotal"]:
        print(f"Invalid values for {col}: {df[df[col] < 0].shape[0]}")
    else:
        print(f"Invalid values for {col}: {df[df[col] <= 0].shape[0]}")

# drop some rows with invalid values for Week 6
df = df[(df["ClosePrice"] > 0) & (df["LivingArea"] > 0) & df["OriginalListPrice"]]


# check geographic data
print(f"Checking data for invalid geographic data... ")
coord_null = (df["Latitude"].isnull() | df["Longitude"].isnull())
coord_zero = (df["Latitude"] == 0) | (df["Longitude"] == 0)
coord_out_of_range = (df["Longitude"] > 0) | (df["Latitude"] < 0)
coord_invalid = (abs(df["Longitude"]) > 180) | (abs(df["Latitude"]) > 90)

geo_quality_report = pd.DataFrame({
    "Missing": int(coord_null.sum()),
    "Zero": int(coord_zero.sum()),
    "OutOfRange": int(coord_out_of_range.sum()),
    "Invalid": int(coord_invalid.sum())
}, index=[0])
print(f"Invalid geographic data report:\n"
      f"{geo_quality_report.to_string()}")

df["coord_missing"] = coord_null | coord_zero
df["coord_invalid"] = df["coord_missing"] | coord_out_of_range | coord_invalid


#####   WEEK 6   #####
# Create new features via feat. engineering
df["PriceRatio"] = df["ClosePrice"] / df["ListPrice"]
df["PricePerSqft"] = df["ClosePrice"] * df["LivingArea"]
df["YearMonth"] = df["CloseDate"].dt.to_period("M")
df["CloseOrigRatio"] = df["ClosePrice"] / df["OriginalListPrice"]
df["ListContractDays"] = df["PurchaseContractDate"].dt.day - df["ListingContractDate"].dt.day
df["ContractCloseDays"] = df["CloseDate"].dt.day - df["PurchaseContractDate"].dt.day

key_metrics = ["PriceRatio", "PricePerSqft", "DaysOnMarket", "YearMonth",
               "ListContractDays", "ContractCloseDays"]
print(df[key_metrics].head().to_string())

# summary for each segment
segment = ["PropertySubType", "CountyOrParish", "ListOfficeName"]
for seg in segment:
    print(df.groupby(seg)[key_metrics].describe().to_string())


#####   FINAL DATASET   #####
df.to_csv("listed_final.csv", index=False)
print(f"Final listing shape: {df.shape}")
