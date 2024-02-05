#!/bin/bash

folder_path=$1
search_string=$2

# Iterate through each text file
for file in $folder_path/*.sh; do
    if [ -f "$file" ]; then
        # Use grep to search for the string in the file
        if grep -F "$search_string" "$file"; then
            echo "String found in file: $file"
            exit 0  # Exit if found in the first occurrence
        fi
    fi
done

echo "String not found in any file in the folder."
exit 1