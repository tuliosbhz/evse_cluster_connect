#!/bin/bash

# Define the list of input files
input_files=("nds_addr_exp_two_nodes.txt" "nds_addr_exp_three_nodes.txt" "nds_addr_exp_four_nodes.txt" "nds_addr_exp_five_nodes.txt" "nds_addr_exp_six_nodes.txt")

# Loop through each input file
for file in "${input_files[@]}"; do
    echo "Executing experiment with input file: $file"
    
    # Execute the Python script with the current input file in the background
    python3 benchmark_kpi.py all_nodes_exp "$file" &
    
    # Capture the process ID of the background process
    pid=$!
    
    # Wait for the background process to finish
    wait $pid
    
    # Add a pause or sleep between experiments if needed
    sleep 5
done

echo "All experiments completed"
