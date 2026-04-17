import pandas as pd
import glob as gl

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

# Drop the ".1" columns (CloseDate.1, Latitude.1, etc.)
dot1_cols = [col for col in df.columns if ".1" in col]
df = df.drop(dot1_cols, axis=1)
df = df.drop_duplicates(subset="ListingKey", keep="last")

# Filter to RESIDENTAL properties
df_res = df[df["PropertyType"] == "Residential"]
print(f"Residental Properties found: {df_res.shape[0]}")

# Save new CSV
df_res.to_csv("listed_final.csv", index=False)
print(f"Final listing shape: {df_res.shape}")

