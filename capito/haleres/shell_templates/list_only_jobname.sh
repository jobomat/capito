find logs/* -type f -printf "%f\n" | awk -F "." '{print $1}'
