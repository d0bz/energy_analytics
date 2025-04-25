#https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/58.547%2C%2023.076/2025-03-01/2025-03-31?unitGroup=metric&key=QMPQ9QYCK5PC3WR6TAP4FRDT3&contentType=json


import pandas as pd

# Input and output file paths
input_file = 'input.csv'
output_file = 'output.csv'

# Read the input CSV with semicolon separator
df = pd.read_csv(input_file, delimiter=';')

# Combine date and time into a single datetime column
df['datetime'] = pd.to_datetime(df[['Aasta', 'Kuu', 'Päev']].astype(str).agg('-'.join, axis=1) + ' ' + df['Kell (UTC)'])

# 🔥 Filter only for the year 2020
df = df[df['datetime'].dt.year == 2020]

# Select the required columns
#df_out = df[['datetime', 'wind_speed']]

# Extract month, day, and hour
df['month'] = df['datetime'].dt.month
df['day'] = df['datetime'].dt.day
df['hour'] = df['datetime'].dt.hour

# Group by month, day, and hour, then calculate mean wind speed
grouped = df.groupby(['month', 'day', 'hour'])['wind_speed'].mean().reset_index()

# Optional: round for cleaner output
grouped['wind_speed'] = grouped['wind_speed'].round(2)

# Combine into a proper datetime (using a reference year, e.g., 2000 for consistency)
grouped['datetime'] = pd.to_datetime({
    'year': 2000,  # reference year
    'month': grouped['month'],
    'day': grouped['day'],
    'hour': grouped['hour']
}, errors='coerce')

# Drop rows with invalid dates (like February 30, April 31, etc.)
grouped = grouped.dropna(subset=['datetime'])

# Select desired columns
final = grouped[['datetime', 'wind_speed']]

# https://wind-data.ch/tools/profile.php?h=10&v=1&z0=0.1&abfrage=Refresh
final['wind_speed'] = final['wind_speed'] * 1.15

# Power curve dictionary
power_curve = {
    3: 0,
    4: 0.267,
    5: 0.933,
    6: 1.7,
    7: 2.7,
    8: 3.867,
    9: 5.333,
    10: 7.2,
    11: 8.267,
    12: 8.6
}
# Round wind speeds to nearest integer to map to power curve
final['wind_speed_rounded'] = final['wind_speed'].fillna(0).round().astype(int)


# Map wind speed to power output (kW)
final['power_output_kW'] = final['wind_speed_rounded'].map(power_curve).fillna(0)

# Since each row represents one hour, energy (kWh) is power_output_kW * 1h
final['energy_kWh'] = final['power_output_kW']  # multiply by 1 hour

# Sum total energy production
total_energy = final['energy_kWh'].sum()

print(f"Total estimated annual energy production: {total_energy:.2f} kWh")

# Optional: Export to CSV to see the full hourly production profile
final.to_csv(output_file, sep=';', index=False)

print(f"Hourly production profile saved to {output_file}")
