import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Parameters
total_annual_consumption_kWh = 28800
year = 2024

# Create a datetime index for each hour of the year
start_time = datetime(year, 1, 1)
end_time = datetime(year + 1, 1, 1)
# Fixing the issue by using the correct parameter `inclusive` instead of the deprecated `closed`

# Create a datetime index for each hour of the year using the correct parameter
datetime_index = pd.date_range(start=start_time, end=end_time, freq='H', inclusive='left')

# Create a basic daily load profile (normalized to 1)
# Pattern: night (low), morning peak, daytime low, evening peak
hourly_factors = np.array([
    0.2, 0.2, 0.2, 0.2, 0.2, 0.3,  # 00-05
    0.6, 0.8, 1.0,                # 06-08
    0.5, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5,  # 09-15
    1.2, 1.5, 1.8, 1.5, 1.2,      # 16-20
    0.8, 0.6, 0.4                 # 21-23
])
hourly_factors = hourly_factors / hourly_factors.sum()  # normalize to 1 per day


# Repeat pattern for each day of the year
days_in_year = (end_time - start_time).days
daily_profile = np.tile(hourly_factors, days_in_year)

# Adjust for leap year (2024 has 366 days)
if len(datetime_index) > len(daily_profile):
    daily_profile = np.append(daily_profile, hourly_factors)

# Normalize the full year profile to total annual consumption
yearly_profile = (daily_profile / daily_profile.sum()) * total_annual_consumption_kWh

# Create DataFrame
load_profile_df = pd.DataFrame({
    "timestamp": datetime_index,
    "load_kWh": yearly_profile
})

# Save to CSV
csv_path = "output/estonian_apartment_load_profile_2024.csv"
load_profile_df.to_csv(csv_path, index=False)
