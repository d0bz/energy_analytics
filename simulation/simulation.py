import matplotlib.pyplot as plt
import pandas as pd

# Create a flexible simulation function for battery usage and grid interaction

solar_park_power = 30
battery_capacity_kWh = 70.0

def simulate_energy_flow(
    df,  # DataFrame with columns: 'timestamp', 'price', 'solar_generation', 'consumption'
    max_cycles_per_day=2,
    min_soc=0.1,
    max_soc=0.9,
    charge_efficiency=0.95,
    discharge_efficiency=0.95
):
    df = df.copy()
    df["soc"] = 0.0  # state of charge in kWh
    df["grid_import"] = 0.0  # energy bought from grid
    df["grid_export"] = 0.0  # excess solar to grid
    df["battery_charge"] = 0.0
    df["battery_discharge"] = 0.0
    df["local_use"] = 0.0

    soc = battery_capacity_kWh * max_soc
    usable_capacity = (max_soc - min_soc) * battery_capacity_kWh
    max_daily_throughput = usable_capacity * max_cycles_per_day

    last_day = None
    energy_moved_today = 0.0

    for i, row in df.iterrows():
        timestamp = row["timestamp"]
        day = timestamp.date()
        if day != last_day:
            energy_moved_today = 0.0
            last_day = day

        gen = row["solar_generation"] * solar_park_power
        cons = row["consumption"]

        # Local solar usage
        local_use = min(gen, cons)
        cons -= local_use
        gen -= local_use

        # Battery charging from solar
        max_energy = battery_capacity_kWh * max_soc
        charge_limit = max_energy
        if soc < charge_limit and energy_moved_today < max_daily_throughput:
            max_charge_possible = min(charge_limit - soc, gen * charge_efficiency)
            remaining_throughput = max_daily_throughput - energy_moved_today
            actual_charge = min(max_charge_possible, remaining_throughput)
            energy_needed = actual_charge / charge_efficiency

            soc += actual_charge
            gen -= energy_needed
            df.at[i, "battery_charge"] = actual_charge
            energy_moved_today += actual_charge

        # Battery discharging to meet consumption
        discharge_limit = battery_capacity_kWh * min_soc
        if soc > discharge_limit and energy_moved_today < max_daily_throughput:
            available_discharge = soc - discharge_limit
            needed_discharge = cons / discharge_efficiency
            max_discharge_possible = min(available_discharge, needed_discharge)
            remaining_throughput = max_daily_throughput - energy_moved_today
            actual_discharge = min(max_discharge_possible, remaining_throughput)
            usable_energy = actual_discharge * discharge_efficiency

            soc -= actual_discharge
            cons -= usable_energy
            df.at[i, "battery_discharge"] = usable_energy
            energy_moved_today += actual_discharge

        # Remaining demand from grid
        df.at[i, "grid_import"] = max(cons, 0)
        # Remaining solar to grid
        df.at[i, "grid_export"] = max(gen, 0)
        df.at[i, "local_use"] = local_use
        df.at[i, "soc"] = soc

    return df

# Sample structure to demonstrate how to plot and evaluate
def plot_energy_analysis(df):
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Left Y-axis: Energy flows
    ax1.plot(df["timestamp"], df["grid_import"], label="Grid Import (kWh)", alpha=0.7)
    ax1.plot(df["timestamp"], df["solar_generation"]*solar_park_power, label="Solar Generation (kWh)", alpha=0.7)
    #ax1.plot(df["timestamp"], df["consumption"], label="Consumption (kWh)", alpha=0.7)
    #ax1.plot(df["timestamp"], df["battery_charge"], label="Battery Charge (kWh)", alpha=0.7)
    #ax1.plot(df["timestamp"], df["battery_discharge"], label="Battery Discharge (kWh)", alpha=0.7)

    ax1.set_xlabel("Time")
    ax1.set_ylabel("Energy (kWh)")
    ax1.legend(loc="upper left")
    ax1.grid(True)

    # Right Y-axis: SoC
    ax2 = ax1.twinx()
    ax2.plot(df["timestamp"], df["soc"], label="Battery SoC (kWh)", color="black", linestyle='--', linewidth=1.5)
    ax2.set_ylabel("Battery SoC (kWh)")
    ax2.legend(loc="upper right")
    ax2.set_ylim(bottom=0)

    plt.title("Energy Flow and Battery SoC Over Time. " + str(solar_park_power) + "kW park and " + str(battery_capacity_kWh) + " kWh battery")
    fig.tight_layout()
    plt.show()

# Ready for loading user data and applying this simulation
"Simulation functions are ready. Please upload your CSV file with columns: timestamp, price, solar_generation, and consumption."


# Read the CSV file
df = pd.read_csv("scripts/simulation_data.csv", sep=';', parse_dates=["timestamp"])
#july_df = df[df["timestamp"].dt.month == 7]

start_date = pd.to_datetime("2024-03-01")
end_date = pd.to_datetime("2024-04-30 23:59:59")
july_df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]

result_df = simulate_energy_flow(july_df)
plot_energy_analysis(result_df)

# Save the updated DataFrame to a new file
#output_file = "simulation_output.csv"
#result_df.to_csv(output_file, index=False)

#print(f"Updated file saved as: {output_file}")
