import csv
import random
import datetime

# Define CSV file path
csv_file = "smart_home_energy_data.csv"

# Define appliances
appliances = ["Air Conditioner", "Refrigerator", "Water Geyser", "Lighting & Ventilation"]

# Generate random dataset
rows = []
for i in range(24):  # 24 hours
    timestamp = datetime.datetime(2026, 5, 20, i, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "Timestamp": timestamp,
        "Air Conditioner": round(random.uniform(0.5, 2.5), 2),   # kWh
        "Refrigerator": round(random.uniform(0.1, 0.3), 2),
        "Water Geyser": round(random.uniform(0.0, 2.0), 2),
        "Lighting & Ventilation": round(random.uniform(0.05, 0.5), 2)
    }
    rows.append(row)

# Write to CSV
with open(csv_file, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["Timestamp"] + appliances)
    writer.writeheader()
    writer.writerows(rows)

print(f"Random dataset generated and saved to {csv_file}")
