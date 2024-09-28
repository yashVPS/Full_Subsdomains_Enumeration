#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <domain> <output_filename>"
    exit 1
fi

domain="$1"
output_file="$2"
page=1

# Clear the output file if it already exists
> "$output_file"

while true; do
    # Set a timeout of 30 seconds to avoid hanging
    response=$(curl -s --max-time 30 "https://otx.alienvault.com/api/v1/indicator/domain/$domain/url_list?limit=500&page=$page")
    
    # Extract the url_list and check if it's empty
    url_list=$(echo "$response" | jq -r '.url_list')

    if [[ "$url_list" == "[]" ]]; then
        echo "No more hostnames found on page $page. Exiting."
        break
    fi

    # Extract hostnames and save them to the output file
    echo "$url_list" | jq -r '.[].hostname' >> "$output_file"
    
    # Log progress
    total_hostnames=$(echo "$url_list" | jq length)
    echo "Page $page fetched with $total_hostnames hostnames. Saving to $output_file."
    
    page=$((page + 1))
    
    # Sleep for 5 seconds between requests to avoid potential rate limiting
    sleep 5
done

echo "All hostnames have been saved to $output_file."
