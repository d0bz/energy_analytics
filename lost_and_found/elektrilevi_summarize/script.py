import pandas as pd
from datetime import timedelta

# Read the data
df = pd.read_csv('elektrilevi.csv', sep=';')  # Adjust separator

# Remove summary rows
df = df[df['hour'] != 'Kokku']

# Convert 'hour' column to integer
df['hour'] = df['hour'].astype(int)

# Adjust rows where hour == 24
mask = df['hour'] == 24
df.loc[mask, 'hour'] = 0  # Set hour to 0
df.loc[mask, 'date'] = pd.to_datetime(df.loc[mask, 'date'], dayfirst=True) + timedelta(days=1)
df['date'] = pd.to_datetime(df['date'], dayfirst=True)

# Create 'datetime' column
df['datetime'] = df['date'] + pd.to_timedelta(df['hour'], unit='h')

# Drop old columns if desired
df = df.drop(columns=['date', 'hour'])

# Reorder columns
df = df[['datetime', 'total_consumption']]

# Save to new CSV
df.to_csv('cleaned_data.csv', index=False)

print(df.head())
