import os
import csv
import requests
import tempfile
from datetime import datetime
import argparse
import pandas as pd
from io import StringIO


priceFile = "data/electricity_prices_ee.csv"
pvGISFile = "data/pvgis.csv"

class PVGISData:
    def __init__(self, lat, lon, output_dir="data"):
        self.lat = lat
        self.lon = lon
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filename = pvGISFile

    def fetch(self):
        print(f"Fetching PVGIS data for lat={self.lat}, lon={self.lon}...")
        base_url = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
        params = {
            "lat": self.lat,
            "lon": self.lon,
            "raddatabase": "PVGIS-SARAH3",
            "browser": "1",
            "outputformat": "csv",
            "userhorizon": "",
            "usehorizon": "1",
            "angle": "45",
            "aspect": "0",
            "startyear": "2013",
            "endyear": "2023",
            "mountingplace": "",
            "optimalinclination": "0",
            "optimalangles": "0",
            "js": "1",
            "select_database_hourly": "PVGIS-SARAH3",
            "hstartyear": "2013",
            "hendyear": "2023",
            "trackingtype": "0",
            "hourlyangle": "45",
            "hourlyaspect": "0"
        }

        # Make the request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an error for bad status

        # Step 1: Get the lines and clean out metadata
        lines = response.text.splitlines()
        filtered_lines = lines[8:-10]  # Skip first 8, remove last 10

        # Step 2: Join into string and read with pandas
        data_str = "\n".join(filtered_lines)
        df = pd.read_csv(StringIO(data_str))

        # Step 3: Parse first column as datetime in UTC
        first_col = df.columns[0]
        df[first_col] = df[first_col].astype(str).str.strip()
        df[first_col] = pd.to_datetime(df[first_col], format="%Y%m%d:%H%M", errors="raise", utc=True)

        # Step 4: Round to the next full hour
        df[first_col] = df[first_col].dt.floor("H")

        # Step 5: Convert to Europe/Tallinn timezone
        df[first_col] = df[first_col].dt.tz_convert("Europe/Tallinn")

        # Step 6: Format nicely
        df[first_col] = df[first_col].dt.strftime("%Y-%m-%d %H:%M:%S")


        # Salvestame CSV-faili
        df.to_csv(self.filename, index=False)

    def load_or_fetch(self, reload=False):
        if reload or not os.path.exists(self.filename):
            self.fetch()
        else:
            print(f"Using cached PVGIS data from {self.filename}")


class ElectricityPriceData:
    def __init__(self, output_file=priceFile):
        self.output_file = output_file
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

    def fetch_year(self, year):
        start = f"{year}-01-01T00:00:00.000Z"
        end = f"{year}-12-31T23:59:59.999Z"
        url = f"https://dashboard.elering.ee/api/nps/price?start={start}&end={end}"
        print(f"Fetching electricity prices for {year}...")

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("ee", [])

    def fetch_all(self):
        current_year = datetime.utcnow().year
        all_data = []

        for year in range(2013, current_year + 1):
            year_data = self.fetch_year(year)
            all_data.extend(year_data)

        with open(self.output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "datetime", "price_EUR_per_MWh"])
            for entry in all_data:
                ts = entry["timestamp"]
                dt = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([ts, dt, entry["price"]])
        print(f"Saved electricity prices to {self.output_file}")

    def load_or_fetch(self, reload=False):
        if reload or not os.path.exists(self.output_file):
            self.fetch_all()
        else:
            print(f"Using cached electricity price data from {self.output_file}")


class DataManager:
    def __init__(self, lat, lon, reload=False):
        self.pvgis = PVGISData(lat, lon)
        self.electricity = ElectricityPriceData()

        self.reload = reload

    def run(self):
        self.pvgis.load_or_fetch(reload=self.reload)
        self.electricity.load_or_fetch(reload=self.reload)

class Analytic:
    def create_folder_if_not_exists(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Folder created: {folder_path}")
        else:
            print(f"Folder already exists: {folder_path}")

    def __init__(self, power):
        # Load PV production data
        pvsol = pd.read_csv(pvGISFile, parse_dates=["time"])
        pvsol.rename(columns={"G(i)": "production_Wh_per_kW"}, inplace=True)

        # Convert 'time' column to datetime
        pvsol["time"] = pd.to_datetime(pvsol["time"])

        # Load price data
        prices = pd.read_csv(priceFile, parse_dates=["datetime"])
        prices.rename(columns={"price_EUR_per_MWh": "price"}, inplace=True)

        # Convert 'timestamp' column to datetime
        prices["timestamp"] = pd.to_datetime(prices["datetime"])

        # Merge on datetime (inner join to keep only matching timestamps)
        merged = pd.merge(pvsol, prices, left_on="time", right_on="timestamp", how="inner")

        # --- CALCULATIONS ---
        # Actual production (Wh) = 1kW production × power
        merged["actual_production_Wh"] = merged["production_Wh_per_kW"] * power

        # Convert Wh → MWh
        merged["actual_production_MWh"] = merged["actual_production_Wh"] / 1_000_000

        # Calculate revenue = production * price
        merged["revenue_EUR"] = merged["actual_production_MWh"] * merged["price"]

        # Add month and year columns
        merged["month"] = merged["time"].dt.to_period("M")
        merged["year"] = merged["time"].dt.year

        # --- MONTHLY PROFIT ---
        monthly_profit = merged.groupby("month")["revenue_EUR"].sum().reset_index()
        monthly_profit["revenue_EUR"] = monthly_profit["revenue_EUR"].round(2)

        # --- YEARLY PROFIT ---
        yearly_profit = merged.groupby("year")["revenue_EUR"].sum().reset_index()
        yearly_profit["revenue_EUR"] = yearly_profit["revenue_EUR"].round(2)

        # --- SAVE OUTPUTS ---

        self.create_folder_if_not_exists("result")
        monthly_profit.to_csv("result/monthly_profit.csv", index=False)
        yearly_profit.to_csv("result/yearly_profit.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load PV and electricity price data.")
    parser.add_argument("--lat", type=float, default=58.547, help="Latitude for PVGIS")
    parser.add_argument("--lon", type=float, default=23.076, help="Longitude for PVGIS")
    parser.add_argument("--reload", action="store_true", help="Force re-download of all data")
    parser.add_argument("--power_kw", type=float, default=200, help="Solar park power in kW")

    args = parser.parse_args()

    manager = DataManager(lat=args.lat, lon=args.lon, reload=args.reload)
    manager.run()

    analytic = Analytic(power=args.power_kw)

