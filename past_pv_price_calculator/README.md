# Analytics for PVGIS and Elering Electricity Prices

This script fetches and stores:
- **Solar PV generation data** from the [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/) API.
- **Electricity market prices** for Estonia (`ee`) from [Elering's dashboard](https://dashboard.elering.ee).

Data is downloaded and stored as CSV files in the `data/` folder.

Result of monthly and yearly revenues are stored in `result/` folder.

---

## 📦 Requirements

- Python 3.7+
- `requests` (install with `pip install requests`)

---

## 🚀 Usage

```bash
python data_loader.py [--lat LAT(default 58.547)] [--lon LON(default 23.076)] [--power_kw POWER(default 200)]  [--reload]

