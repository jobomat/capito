#!/bin/bash

# Define the threshold for exceptionally long runtime in seconds
threshold=30 

# Get the list of Python processes along with their start times
python_processes_info=$(ps -eo pid,etimes,cmd | grep -E '[ ]*python[ ]*')

# Loop through the processes
while read -r line; do
    pid=$(echo $line | awk '{print $1}')
    elapsed_time=$(echo $line | awk '{print $2}')

    # Check if the process has been running longer than the threshold
    if [ $elapsed_time -gt $threshold ]; then
        # echo "Terminating Python process $pid with exceptionally long runtime ($elapsed_time seconds)..."
        
        # Terminate the Python process
        kill $pid
        
        # echo "Python process $pid terminated."
    fi
done <<< "$python_processes_info"

# echo "Script finished."