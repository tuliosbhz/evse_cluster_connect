import pandas as pd
import time

# Read data from file
file_path = "results/max_rps_backup.txt"
with open(file_path, 'r') as file:
    data = eval(file.read())  # Assuming data is in Python list format

# Create DataFrame
df = pd.DataFrame(data, columns=["Request Size", "Num Nodes", "Max RPS"])

# Export to CSV
csv_filename = f"max_rps_result_{int(time.time())}.csv"
df.to_csv(csv_filename, index=False)

print(f"Data exported to {csv_filename}")
