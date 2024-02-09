import os
import pandas as pd
import re
import time

# Function to extract data from file name
def extract_data_from_filename(filename):
    match = re.match(r'(\d+\.\d+\.\d+\.\d+)_(\d+)_nodes_(\d+).txt', filename)
    if match:
        ip = match.group(1)
        port = int(match.group(2))
        num_nodes = int(match.group(3))
        return ip, port, num_nodes
    else:
        return None

# Function to read data from files and create DataFrame
def create_dataframe_from_files(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r') as file:
                content = file.read()
                try:
                    analysis_data = eval(content)  # Assuming content is a valid dictionary
                    ip, port, num_nodes = extract_data_from_filename(filename)
                    if ip and port and num_nodes:
                        analysis_data.update({'IP': ip, 'Port': port, 'Num Nodes': num_nodes})
                        data.append(analysis_data)
                except Exception as e:
                    print(f"Error parsing file {filename}: {e}")
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by="Num Nodes")
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
