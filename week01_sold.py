import pandas as pd
import glob as gl

sold_files = sorted(gl.glob("datasets/CRMLSSold*.csv"))

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

df = df.drop_duplicates(subset="ListingKey", keep="last")

# FILTER TO RESIDENTAL PROPERTIES
df_res = df[df["PropertyType"] == "Residential"]
print(f"Residental Properties found: {df_res.shape[0]}")

# SAVE NEW CSV
df_res.to_csv("sold_final.csv", index=False)
print(f"Final sold shape: {df_res.shape}")

