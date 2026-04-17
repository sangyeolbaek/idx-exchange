import pandas as pd

# Convert to dataframes
listed = pd.read_csv("listed_final.csv", low_memory=False)
sold = pd.read_csv("sold_final.csv", low_memory=False)

# Data cleaning
date_cols = [col for col in sold.columns if "date" in col.lower()]
for col in date_cols:
    listed[col] = pd.to_datetime(listed[col], errors="coerce")
    sold[col] = pd.to_datetime(sold[col], errors="coerce")

# Null values check
def report_null_tbl(df):
    missing = df.isnull().sum()
    missing_pct = round(missing / df.shape[0] * 100, 2)
    high_null = missing_pct > 90.0
    null_tbl = pd.DataFrame({
        "Missing": missing,
        "NullPct": missing_pct,
        "HighNull": high_null
    })
    return null_tbl.sort_values(by="NullPct", ascending=False)

listed_null = report_null_tbl(listed)
print(f"Columns with missing values (LISTED):\n"
      f"{listed_null[listed_null["NullPct"]>0].to_string()}")

sold_null = report_null_tbl(sold)
print(f"Columns with missing values (SOLD):\n"
      f"{sold_null[sold_null['NullPct']>0].to_string()}")

# Filter out non-main fields with high missing count
main_fields = ["ListingKey", "ListingContractDate", "ListPrice", "ClosePrice",
               "PurchaseContractDate", "CloseDate", "LivingArea", "BedroomsTotal",
               "BathroomsToInteger", "Latitude", "Longitude", "UnparsedAddress"]

for col in listed_null[listed_null["HighNull"]].index:
    if col not in main_fields:
        listed = listed.drop(col, axis=1)
for col in sold_null[sold_null["HighNull"]].index:
    if col not in main_fields:
        sold = sold.drop(col, axis=1)
print(f"Shape of listed: {listed.shape}")
print(f"Shape of sold: {sold.shape}")


# # Numeric overview
# numeric_fields = ["ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
#                   "LotSizeAcres", "BedroomsTotal", "BathroomsToInteger", "DaysOnMarket",
#                   "YearBuilt"]
#
# # What percentage of properties are Residential?
# is_res = sold["PropertyType"] == "Residential"
# print(f"Percentage of Residential properties: {sold[is_res].shape[0] / sold.shape[0] * 100:.2f}%")


# Statistical summaries of ClosePrice, LivingArea, and DaysOnMarket
print("Statistical summaries for ClosePrice, LivingArea, DaysOnMarket:")
print(f"LISTING:\n"
      f"{listed[["ClosePrice", "LivingArea", "DaysOnMarket"]].describe().to_string()}")
print(f"SOLD:\n"
      f"{sold[["ClosePrice", "LivingArea", "DaysOnMarket"]].describe().to_string()}")

