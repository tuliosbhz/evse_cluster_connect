import os
import pandas as pd
import re
import json
import time

# Function to extract data from file name
def extract_data_from_filename(filename):
    match = re.match(r'(\d+\.\d+\.\d+\.\d+)_(\d+)\.txt', filename)
    #match = re.match(r'(\d+)_(\d+)\.txt', filename)
    if match:
        ip = match.group(1)
        port = int(match.group(2))
        return ip, port
    else:
        return None

# Function to read data from files and create DataFrame
def create_dataframe_from_files(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r') as file:
                for line in file:
                    try:
                        analysis_data = json.loads(line.strip())  # Assuming each line is a valid JSON string
                        ip, port = extract_data_from_filename(filename)
                        if ip and port:
                            analysis_data.update({'Node Address': f"{ip}:{port}"})
                            data.append(analysis_data)
                    except Exception as e:
                        print(f"Error parsing file {filename}: {e}")
    df = pd.DataFrame(data)
    return df

# Main function to run the script
def main():
    directory = "results/"
    df = create_dataframe_from_files(directory)
    if not df.empty:
        time_str = str(time.time())
        csv_filename = "performance_analysis_" + time_str + ".csv"
        df.to_csv(csv_filename, index=False)
        print("CSV file successfully created.")
    else:
        print("No data found in files.")

if __name__ == "__main__":
    main()
