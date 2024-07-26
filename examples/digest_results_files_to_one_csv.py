import os
import pandas as pd

# Define the folder path containing CSV files
folder_path = '.'

# List to hold dataframes
dataframes = []

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        # Read CSV file
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)
        dataframes.append(df)

# Concatenate all dataframes into one
concatenated_df = pd.concat(dataframes, ignore_index=True)

# Define the output file path
output_csv_path = os.path.join(folder_path, 'concatenated_file.csv')
output_excel_path = os.path.join(folder_path, 'concatenated_file.xlsx')

# Save the concatenated dataframe to a CSV file
concatenated_df.to_csv(output_csv_path, index=False)

# Save the concatenated dataframe to an Excel file
concatenated_df.to_excel(output_excel_path, index=False, engine='openpyxl')

print(f'CSV file saved to {output_csv_path}')
print(f'Excel file saved to {output_excel_path}')
