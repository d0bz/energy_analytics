import csv
from datetime import datetime
from collections import defaultdict

# Simulation configuration
#max_soc = 0.9
#min_soc = 0.1
charge_hours_per_day = 5
discharge_hours_per_day = 4
max_cycles_per_day = 2

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def parse_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            try:
                timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%S")

            solar = safe_float(row["solar_generation"])
            wind = safe_float(row["wind_generation"]) if row.get("wind_generation") else 0.0
            price = safe_float(row["price"])

            data.append({
                "timestamp": timestamp,
                "date": timestamp.date(),
                "solar_generation": solar,
                "wind_generation": wind,
                "price": price,
            })
        return data

def write_csv(filename, data):
    fieldnames = list(data[0].keys())
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(data)

def simulate_energy_flow(data):
    soc = battery_capacity_kWh * min_soc
    usable_capacity = (max_soc - min_soc) * battery_capacity_kWh
    max_daily_throughput = battery_capacity_kWh * 3

    # Group rows by day
    by_day = defaultdict(list)
    for row in data:
        by_day[row["date"]].append(row)

    for day, rows in by_day.items():
        # Pre-sum generation and calculate grid need
        total_daily_gen = sum(r["solar_generation"] + r["wind_generation"] for r in rows)
        total_from_renewables = total_daily_gen * charge_efficiency
        daily_needed_energy = (max_soc - min_soc) * battery_capacity_kWh
        grid_energy_needed = max(daily_needed_energy - total_from_renewables, 0)

        # Get cheapest hours and assign planned grid charge
        sorted_cheap = sorted(rows, key=lambda r: r["price"])[:charge_hours_per_day]
        grid_charge_plan = {}
        energy_remaining = grid_energy_needed
        for r in sorted_cheap:
            charge = min(inverter_power, energy_remaining)
            grid_charge_plan[r["timestamp"]] = charge
            energy_remaining -= charge
            if energy_remaining <= 0:
                break

        # Get discharge hours
        #expensive_hours = set(r["timestamp"] for r in sorted(rows, key=lambda r: r["price"], reverse=True)[:discharge_hours_per_day])


        # Battery discharge need (kWh)
        total_discharge_needed = (max_soc - min_soc) * battery_capacity_kWh

        # Filter rows where inverter is not already full from solar/wind
        available_for_discharge = [
            r for r in rows
            if (r["solar_generation"] + r["wind_generation"]) < inverter_power * 0.9  # leave some headroom
        ]

        # Sort these rows by price, descending
        available_for_discharge.sort(key=lambda r: r["price"], reverse=True)

        # Select enough hours to discharge the needed energy (limited by inverter power per hour)
        selected_hours = []
        remaining_discharge = total_discharge_needed

        for r in available_for_discharge:
            if remaining_discharge <= 0:
                break
            discharge_this_hour = min(inverter_power, remaining_discharge)
            remaining_discharge -= discharge_this_hour
            selected_hours.append(r["timestamp"])

        expensive_hours = set(selected_hours)


        energy_moved_today = 0
        cycles_today = 0
        for row in rows:
            timestamp = row["timestamp"]
            solar_gen = row["solar_generation"]
            wind_gen = row["wind_generation"]
            total_gen = solar_gen + wind_gen
            grid_export = 0

            row.update({
                "soc": soc,
                "battery_charge": 0.0,
                "battery_charge_renewable": 0.0,
                "battery_discharge": 0.0,
                "grid_import": 0.0,
                "grid_import_price": 0.0,
                "grid_export": 0.0,
                "grid_export_revenue": 0.0,
                "temp": 0.0,
            })

            # Charge from renewables
            charge_limit = battery_capacity_kWh * max_soc
            if total_gen > 0 and soc < charge_limit and energy_moved_today < max_daily_throughput:
                max_charge_possible = min(charge_limit - soc, total_gen * charge_efficiency)
                remaining_throughput = max_daily_throughput - energy_moved_today
                actual_charge = min(max_charge_possible, remaining_throughput)
                battery_charge = actual_charge
                soc += battery_charge
                total_gen -= battery_charge / charge_efficiency
                energy_moved_today += actual_charge
                row["battery_charge"] += battery_charge
                row["battery_charge_renewable"] += battery_charge

            # Export excess renewable generation
            if total_gen > 0:
                grid_export = min(total_gen, inverter_power)
                row["grid_export"] += grid_export
                row["grid_export_revenue"] += grid_export * (row["price"] / 1000)

            # Grid charging if in planned hours
            if timestamp in grid_charge_plan and soc < charge_limit and energy_moved_today < max_daily_throughput:
                planned = grid_charge_plan[timestamp]
                actual_charge = min(planned, charge_limit - soc, max_daily_throughput - energy_moved_today)
                grid_energy = actual_charge / charge_efficiency
                soc += actual_charge
                energy_moved_today += actual_charge
                row["battery_charge"] += actual_charge
                row["grid_import"] = grid_energy
                row["grid_import_price"] = grid_energy * (row["price"] / 1000)

            # Discharge if in expensive hours
            discharge_limit = battery_capacity_kWh * min_soc
            if timestamp in expensive_hours and soc > discharge_limit and energy_moved_today < max_daily_throughput:
                available_discharge = soc - discharge_limit
                actual_discharge = min(inverter_power - grid_export, available_discharge, inverter_power, max_daily_throughput - energy_moved_today)
                grid_export = actual_discharge * discharge_efficiency
                soc -= actual_discharge
                energy_moved_today += actual_discharge
                row["battery_discharge"] = actual_discharge
                row["grid_export"] += grid_export
                row["grid_export_revenue"] += grid_export * (row["price"] / 1000)

            row["soc"] = soc

    return data

if __name__ == '__main__':
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Energy Analytics Simulation')
    parser.add_argument('input_file', help='Input CSV file')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--inverter', type=int, default=200, help='Inverter power in kW')
    parser.add_argument('--battery', type=int, default=400, help='Battery capacity in kWh')
    parser.add_argument('--efficiency', type=float, default=0.94, help='Battery round-trip efficiency (0-1)')
    parser.add_argument('--reserve', type=float, default=0.95, help='Battery reserve percentage (0-1)')

    args = parser.parse_args()
    
    # Update global variables based on arguments
    global inverter_power, battery_capacity_kWh, charge_efficiency, discharge_efficiency, max_soc, min_soc
    inverter_power = args.inverter
    battery_capacity_kWh = args.battery

    max_soc = args.reserve
    min_soc = 1 - args.reserve

    # Calculate charge/discharge efficiency as square root of round-trip efficiency
    efficiency_per_cycle = args.efficiency ** 0.5
    charge_efficiency = efficiency_per_cycle
    discharge_efficiency = efficiency_per_cycle
    
    # Read the CSV file
    all_data = parse_csv(args.input_file)

    # Apply date filtering if dates are provided
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
        all_data = [row for row in all_data if start_date <= row["date"] <= end_date]

    result = simulate_energy_flow(all_data)
    write_csv("simulation_output.csv", result)
    print("Simulation complete. Output saved to simulation_output.csv")
