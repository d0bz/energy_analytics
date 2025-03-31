import pandas as pd

# Input and output file paths
input_file = "production_kw_per_kw_panel.csv"
output_file = "output_2024.csv"

# Read the CSV file
df = pd.read_csv(input_file, sep=';', parse_dates=["time"])

# Replace the year 2023 with 2024 in the 'time' column
df["time"] = df["time"].apply(lambda ts: ts.replace(year=2024))

# Save the updated DataFrame to a new file
df.to_csv(output_file, index=False)

print(f"Updated file saved as: {output_file}")
