#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <domains_comma_separated> <output_filename>"
    exit 1
fi

# Read input arguments
domains="$1"
output_file="$2"

# Split the domains by commas into an array
IFS=',' read -r -a domain_array <<< "$domains"

# Clear the output file if it already exists
> "$output_file"

# Loop through each domain in the array
for domain in "${domain_array[@]}"; do
    echo "Processing domain: $domain"
    page=1

    while true; do
        # Set a timeout of 30 seconds to avoid hanging
        response=$(curl -s --max-time 30 "https://otx.alienvault.com/api/v1/indicator/domain/$domain/url_list?limit=500&page=$page")
        
        # Extract the url_list and check if it's empty
        url_list=$(echo "$response" | jq -r '.url_list')

        if [[ "$url_list" == "[]" ]]; then
            echo "No more hostnames found for $domain on page $page. Moving to the next domain."
            break
        fi

        # Extract hostnames and save them to the output file
        echo "$url_list" | jq -r '.[].hostname' >> "$output_file"
        
        # Log progress
        total_hostnames=$(echo "$url_list" | jq length)
        echo "Page $page for $domain fetched with $total_hostnames hostnames. Saving to $output_file."
        
        page=$((page + 1))
        
        # Sleep for 5 seconds between requests to avoid potential rate limiting
        sleep 1
    done
done

echo "All hostnames have been saved to $output_file."
