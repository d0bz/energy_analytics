import pandas as pd
import numpy as np


# Määrame ajavahemiku
date_range = pd.date_range(start="2024-01-01", end="2024-12-31 23:00:00", freq="H")

# Loome uue tarbimisjaotuse, võttes arvesse erinevaid inimeste päevakavasid ja nädalavahetuse kõrgemat tarbimist

# Parameetrid
total_daily_consumption = 84  # kWh päevane tarbimine kogu kortermaja kohta
workday_schedule_early = [7, 8, 9, 17, 18, 19, 20]  # Need, kes lahkuvad kell 7 ja tulevad 15-16
workday_schedule_late = [9, 10, 11, 19, 20, 21]  # Need, kes lahkuvad 9 ja tulevad 17-18

# Tööpäevade ja nädalavahetuse tegurid
weekday_factors = np.array([
    0.01, 0.01, 0.005, 0.005, 0.005, 0.01, 0.02, 0.04, 0.08, 0.07, 0.06, 0.05,  # Hommik
    0.04, 0.03, 0.02, 0.05, 0.06, 0.08, 0.1, 0.12, 0.1, 0.08, 0.05, 0.02  # Õhtu
])
weekend_factors = np.array([
    0.02, 0.02, 0.015, 0.015, 0.015, 0.02, 0.03, 0.06, 0.08, 0.08, 0.07, 0.06,  # Hommik
    0.06, 0.05, 0.04, 0.06, 0.08, 0.09, 0.1, 0.1, 0.09, 0.07, 0.05, 0.03  # Õhtu
])

# Normaliseerime jaotused
weekday_factors /= weekday_factors.sum()
weekend_factors /= weekend_factors.sum()


# Loome uue andmeraami
consumption_data = pd.DataFrame(index=date_range, columns=["consumption_kW"])

# Genereerime tunnise tarbimise
for timestamp in date_range:
    hour = timestamp.hour
    weekday = timestamp.weekday()
    if weekday < 5:  # Esmaspäev-reede (tööpäev)
        factor = weekday_factors[hour]
        if hour in workday_schedule_early:
            factor *= 1.2  # Tõstame tarbimist neile, kes tulevad varem koju
        if hour in workday_schedule_late:
            factor *= 1.1  # Kergelt tõstame hiljem saabujate tarbimist
    else:  # Laupäev-pühapäev (nädalavahetus)
        factor = weekend_factors[hour] * 1.2  # Suurendame nädalavahetuse tarbimist

    # Arvutame selle tunni tarbimise
    hourly_consumption = total_daily_consumption * factor

    consumption_data.loc[timestamp, "consumption_kW"] = hourly_consumption



# Seadistame juhuslikkuse vahemiku (-10% kuni +10%)
random_variation = np.random.uniform(-0.1, 0.1, size=len(consumption_data))

# Rakendame juhuslikkuse tarbimisele
consumption_data["consumption_kW"] = consumption_data["consumption_kW"] * (1 + random_variation)



# Salvestame faili
consumption_data.to_csv("consumption_data.csv")
