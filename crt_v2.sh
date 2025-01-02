#!/bin/bash

# Function: CleanResults
# Filters results to include only the requested domain and its subdomains.
CleanResults() {
    local domain=$1
    sed 's/\\n/\n/g' | \
    sed 's/\*.//g' | \
    grep -E "(\.|^)${domain}$" | \
    sort | uniq
}

# Function: ProcessSingleDomain
ProcessSingleDomain() {
    local req=$1
    local retries=3
    local response=""
    
    for ((i=1; i<=retries; i++)); do
        # Perform the search request to crt.sh
        response=$(curl -s "https://crt.sh/?q=${req}&output=json")
        
        # Validate if the response is valid JSON
        if echo "$response" | jq empty > /dev/null 2>&1; then
            # Process the response and filter for the requested domain
            echo "$response" | jq -r ".[].common_name,.[].name_value" | CleanResults "$req"
            return
        fi

        # If the response is not valid JSON, wait and retry
        sleep 2
    done

    # If no valid response after retries, output a warning
    echo "Warning: Failed to retrieve valid response for $req after $retries attempts" >&2
}

# Function: Domain
Domain() {
    # Split the input into comma-separated values
    IFS=',' read -ra DOMAINS <<< "$req"
    
    # Consolidated results
    consolidated_results=""
    
    # Iterate over each domain and process it
    for domain in "${DOMAINS[@]}"; do
        results=$(ProcessSingleDomain "$domain")
        consolidated_results+="$results"$'\n'
    done
    
    # Remove duplicates, trim extra lines, and print final results
    echo "$consolidated_results" | sed '/^\s*$/d' | sort | uniq
}

# Main Script Logic

if [ -z "$1" ]; then
    echo "Usage:"
    echo "-d    Search Domain Names (comma-separated) | Example: ./crtsh_v2.sh -d example.com,example2.com"
    exit
fi

while getopts "d:" option; do
    case $option in
        d) # Search for domains
            req=$OPTARG
            Domain
            ;;
        *) # Invalid option
            echo "Usage:"
            echo "-d    Search Domain Names (comma-separated) | Example: ./crtsh_v2.sh -d example.com,example2.com"
            exit
            ;;
    esac
done
