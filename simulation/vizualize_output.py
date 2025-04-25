import matplotlib.pyplot as plt
import pandas as pd

solar_park_power = 200
battery_capacity_kWh = 600.0

# Sample structure to demonstrate how to plot and evaluate
def plot_energy_analysis(df):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Left Y-axis: Energy flows
    ax1.plot(df["timestamp"], df["grid_import"], label="Grid Import (kWh)", alpha=1, color="red")
    ax1.plot(df["timestamp"], df["grid_export"], label="Grid Export (kWh)", alpha=1, color="green")

    ax1.plot(df["timestamp"], df["solar_generation"], label="Solar Generation (kWh)", alpha=0.5)
    #ax1.plot(df["timestamp"], df["consumption"], label="Consumption (kWh)", alpha=0.5)
    #ax1.plot(df["timestamp"], df["battery_charge"], label="Battery Charge (kWh)", alpha=0.7)
    #ax1.plot(df["timestamp"], df["battery_discharge"], label="Battery Discharge (kWh)", alpha=0.7)

    ax1.set_xlabel("Time")
    ax1.set_ylabel("Energy (kWh)")
    ax1.legend(loc="upper left")
    ax1.grid(True)

    # Right Y-axis: SoC
    ax2 = ax1.twinx()
    ax2.plot(df["timestamp"], df["soc"], label="Battery SoC (kWh)", color="black", linestyle='--', linewidth=1.5)

    # Grid Price (scaled for visibility)
    price_max = df["price"].max()
    soc_max = battery_capacity_kWh
    price_scale = soc_max / price_max  # Scale to plot on same axis

    ax2.plot(df["timestamp"], df["price"] * price_scale, label="Grid Price (scaled)", color="red", linestyle='dotted', linewidth=1)


    ax2.set_ylabel("Battery SoC (kWh) / Scaled Grid Price")
    ax2.legend(loc="upper right")
    ax2.set_ylim(bottom=0)

    plt.title("Energy Flow and Battery SoC Over Time")
    fig.tight_layout()
    plt.show()

# Read the CSV file
df = pd.read_csv("simulation_output.csv", parse_dates=["timestamp"])
#july_df = df[df["timestamp"].dt.month == 7]

#start_date = pd.to_datetime("2024-07-01")
#end_date = pd.to_datetime("2024-07-02 23:59:59")
#df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]

plot_energy_analysis(df)

