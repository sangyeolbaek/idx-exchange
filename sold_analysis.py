
import pandas as pd
import glob as gl

sold_files = sorted(gl.glob("CRMLSSold*.csv"))

# CONCATENATE DATAFRAMES
df = pd.DataFrame()
rows = 0
for file in sold_files:
    sold_df = pd.read_csv(file, low_memory=False)
    rows += sold_df.shape[0]
    print(f"Loaded {sold_df.shape[0]} rows from {file}, Total: {rows}")
    df = pd.concat([df, sold_df], ignore_index=True)

print(f"{len(sold_files)} files loaded.")
print(f"Shape of dataframe: {df.shape}")

# DATA CLEANING
date_cols = [col for col in df.columns if "date" in col.lower()]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

num_cols = ["ListPrice", "ClosePrice", "LivingArea", "BedroomsTotal", "BathroomsTotalInteger", "Latitude", "Longitude"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# FILTER TO RESIDENTAL PROPERTIES
df_residental = df[df["PropertyType"] == "Residental"]
print(f"Number of Residental Properties: {df_residental.shape[0]}")

# CHECK NULL COUNT
df_null_cnt = (df_residental.isnull().sum() / df_residental.shape[0]).reset_index()
df_null_cnt.columns = ["PropertyType", "NullPct"]
df_null_cnt["isSparse"] = df_null_cnt["NullPct"] >= 90.0
df_null_cnt.to_csv("sold_null_count.csv", index=False)

# SAVE NEW CSV
df_residental.to_csv("sold_final.csv", index=False)
print(f"Final sold shape: {df_residental.shape}")

