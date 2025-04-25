import pandas as pd

# Create a flexible simulation function for battery usage and grid interaction

inverter_power = 200
battery_capacity_kWh = 600.0
max_soc = 0.9
min_soc = 0.1

def simulate_energy_flow(
    df,
    max_cycles_per_day=2,
    charge_efficiency=0.95,
    discharge_efficiency=0.95,
    charge_hours_per_day=3,
    discharge_hours_per_day=3
):
    df = df.copy()
    
    # Ensure timestamp column is properly parsed
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Initialize state columns
    df["soc"] = 0.0
    df["grid_import"] = 0.0
    df["grid_export"] = 0.0
    df["battery_charge"] = 0.0
    df["battery_discharge"] = 0.0
    df["local_use"] = 0.0
    df["grid_import_price"] = 0.0
    df["grid_export_revenue"] = 0.0
    
    # If wind_generation column doesn't exist, initialize it with zeros
    if "wind_generation" not in df.columns:
        df["wind_generation"] = 0.0

    soc = battery_capacity_kWh * min_soc
    usable_capacity = (max_soc - min_soc) * battery_capacity_kWh
    max_daily_throughput = battery_capacity_kWh * max_cycles_per_day

    df["date"] = df["timestamp"].dt.date

    # Precompute cheapest and most expensive hours for each day
    charge_hours = {}
    discharge_hours = {}
    for day in df['timestamp'].dt.date.unique():
        if pd.isna(day):
            continue

        daily_data = df[df['timestamp'].dt.date == day]
        total_daily_gen = (daily_data["solar_generation"].sum() + daily_data["wind_generation"].sum())

        # Calculate how much renewable energy can be stored in the battery
        daily_needed_energy = (max_soc - min_soc) * battery_capacity_kWh

        total_from_renewables = total_daily_gen * charge_efficiency
        grid_energy_needed = max(daily_needed_energy - total_from_renewables, 0)

        # Plan charging only if needed
        daily_charge_plan = {}
        if grid_energy_needed > 0:
            # Pick cheapest hours and distribute needed charge among them
            sorted_cheap = daily_data.nsmallest(charge_hours_per_day, 'price')

            energy_remaining = grid_energy_needed
            for idx, row in sorted_cheap.iterrows():
                charge_this_hour = min(inverter_power, energy_remaining)
                daily_charge_plan[idx] = charge_this_hour
                energy_remaining -= charge_this_hour
                if energy_remaining <= 0:
                    break

        charge_hours[day] = daily_charge_plan

        expensive_idxs = daily_data.nlargest(discharge_hours_per_day, 'price').index
        discharge_hours[day] = set(expensive_idxs)

    last_day = None
    energy_moved_today = 0.0

    for i, row in df.iterrows():
        timestamp = row["timestamp"]
        day = row["date"]
        if day != last_day:
            energy_moved_today = 0.0
            last_day = day

        solar_gen = row["solar_generation"]
        wind_gen = row["wind_generation"] if pd.notna(row["wind_generation"]) else 0.0
        total_gen = solar_gen + wind_gen
        cons = 0.0  # Zero consumption as per new goal

        # First priority: Charge battery from renewable sources
        charge_limit = battery_capacity_kWh * max_soc
        if total_gen > 0:
            if soc < charge_limit and energy_moved_today < max_daily_throughput:
                # Calculate how much we can charge
                max_charge_possible = min(charge_limit - soc, total_gen * charge_efficiency)
                remaining_throughput = max_daily_throughput - energy_moved_today
                actual_charge = min(max_charge_possible, remaining_throughput)
                battery_charge = actual_charge * charge_efficiency

                # Apply the charging
                soc += battery_charge
                total_gen -= battery_charge
                df.at[i, "battery_charge"] += battery_charge
                energy_moved_today += actual_charge
            
            # If there's any excess solar (either battery is full or we hit daily limit)
            if total_gen > 0:
                df.at[i, "grid_export"] += total_gen
                df.at[i, "grid_export_revenue"] += total_gen * (row["price"]/1000)
            
        # Charge from grid during cheapest hours
        if i-1 in charge_hours.get(day, set()) and soc < charge_limit and energy_moved_today < max_daily_throughput:
            max_grid_charge = min(charge_limit - soc, (usable_capacity / charge_efficiency))
            remaining_throughput = max_daily_throughput - energy_moved_today
            actual_charge = min(inverter_power, charge_limit-soc)
            actual_charge = min(actual_charge, remaining_throughput)
            df.at[i, "grid_import"] = actual_charge
            df.at[i, "grid_import_price"] = actual_charge * (row["price"]/1000)
            soc += actual_charge * charge_efficiency
            energy_moved_today += actual_charge

        # Discharge battery during expensive hours and export to grid
        discharge_limit = battery_capacity_kWh * min_soc
        if i-1 in discharge_hours.get(day, set()) and soc > discharge_limit and energy_moved_today < max_daily_throughput:
            available_discharge = soc - discharge_limit
            max_discharge_possible = min(available_discharge, inverter_power)
            remaining_throughput = max_daily_throughput - energy_moved_today
            actual_discharge = min(max_discharge_possible, remaining_throughput)
            grid_export = actual_discharge * discharge_efficiency
            df.at[i, "grid_export"] = grid_export
            df.at[i, "battery_discharge"] = actual_discharge
            df.at[i, "grid_export_revenue"] += grid_export * (row["price"]/1000)
            soc -= actual_discharge
            energy_moved_today += actual_discharge

        df.at[i, "soc"] = soc

    return df





# Ready for loading user data and applying this simulation
"Simulation functions are ready. Please upload your CSV file with columns: timestamp, price, solar_generation, wind_generation, and consumption."


if __name__ == '__main__':
    import sys
    
    # Check arguments
    if len(sys.argv) not in [2, 4]:
        print("Usage: python simulation_grid_battery.py <input_csv> [start_date end_date]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # Read the CSV file
    df = pd.read_csv(input_file, parse_dates=["timestamp"])
    
    # Apply date filtering if dates are provided
    if len(sys.argv) == 4:
        start_date = pd.to_datetime(sys.argv[2])
        end_date = pd.to_datetime(sys.argv[3])
        mask = (df["timestamp"].dt.date >= start_date.date()) & (df["timestamp"].dt.date <= end_date.date())
        df = df[mask]

    # Run simulation
    result_df = simulate_energy_flow(df)
    
    # Save results
    output_file = "simulation_output.csv"
    result_df.to_csv(output_file, index=False)
    
    print(f"Updated file saved as: {output_file}")
