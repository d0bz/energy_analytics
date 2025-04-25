import json
import matplotlib.pyplot as plt
from datetime import datetime

# Load the JSON data
with open('weather.json', 'r') as f:
    data = json.load(f)

# Prepare lists to hold the data
timestamps = []
windspeeds = []
solarenergy = []

# Extract hourly data
for hour in data['days'][0]['hours']:
    # Convert datetime to a readable format
    time = datetime.fromtimestamp(hour['datetimeEpoch'])
    timestamps.append(time)
    windspeeds.append(hour['windspeed'])
    solarenergy.append(hour['solarenergy'])

# Plot windspeed
plt.figure(figsize=(10, 5))
plt.plot(timestamps, windspeeds, marker='o')
plt.title('Windspeed Over Time')
plt.xlabel('Time')
plt.ylabel('Windspeed (km/h)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(True)
plt.show()

# Plot solar energy
plt.figure(figsize=(10, 5))
plt.plot(timestamps, solarenergy, marker='o')
plt.title('Solar Energy Over Time')
plt.xlabel('Time')
plt.ylabel('Solar Energy (kWh/m²)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(True)
plt.show()

