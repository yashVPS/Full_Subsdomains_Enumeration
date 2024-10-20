import requests
import argparse
import json
import threading
from queue import Queue
import time
import random  # For generating a random delay

# Function to check subdomains for a single domain
def check_domain(domain, all_domains, quiet, output_lock, max_retries=3):
    if not quiet:
        print(f"\nSearching for domains related to: {domain}")
    page = 1
    domain_query = f"*.{domain}"

    while True:
        if not quiet:
            print(f"Scanning page {page} for domain: {domain}")

        for attempt in range(max_retries):
            try:
                # Perform the API request for the given domain and page
                url = 'https://api.merklemap.com/search'
                params = {'query': domain_query, 'page': page}
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise an error for bad responses
                break  # Exit retry loop if the request was successful
            except requests.RequestException as e:
                print(f"Error fetching data for {domain} on page {page}: {e}")
                if attempt < max_retries - 1:  # If not the last attempt, wait before retrying
                    time.sleep(1)  # Wait 1 second before retrying
                else:
                    return  # Exit if all retries failed

        # Parse the JSON response
        data = response.json()

        # Check if there are results in the current page
        if not data.get("results"):
            if not quiet:
                print(f"No more results found for {domain} on page {page}.")
            break

        # Extract the domain from each result
        for result in data["results"]:
            domain_value = result.get("domain")
            if domain_value:
                with output_lock:
                    all_domains.append(domain_value)
                if not quiet:
                    print(domain_value)

        # Move to the next page
        page += 1

        # Add a random delay between 5 to 8 seconds before fetching the next page
        delay = random.uniform(5, 8)
        if not quiet:
            print(f"Waiting for {delay:.2f} seconds before the next request...")
        time.sleep(delay)

# Thread worker function
def worker(queue, all_domains, quiet, output_lock):
    while True:
        domain = queue.get()
        if domain is None:
            break
        check_domain(domain, all_domains, quiet, output_lock)
        queue.task_done()

def check_domains(domains, output_file=None, quiet=False, num_threads=1):
    all_domains = []
    output_lock = threading.Lock()  # Lock to synchronize access to shared resources
    queue = Queue()

    # Start thread workers
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(queue, all_domains, quiet, output_lock))
        thread.start()
        threads.append(thread)

    # Enqueue domains
    for domain in domains:
        queue.put(domain)

    # Wait for all domains to be processed
    queue.join()

    # Stop workers
    for _ in range(num_threads):
        queue.put(None)
    for thread in threads:
        thread.join()

    # If output file is provided, save the results to the file
    if output_file:
        with open(output_file, 'w') as f:
            for domain in all_domains:
                f.write(domain + "\n")
        print(f"\nDomains saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract domains using Merklemap API with threading support.")
    parser.add_argument("-d", "--domain", help="Comma-separated list of domains (e.g., example.com,example.org)", required=True)
    parser.add_argument("-o", "--output", help="Output file to save domains in .txt format (e.g., domains.txt)", required=False)
    parser.add_argument("-q", "--quiet", help="Suppress real-time domain discovery output (only works with -o)", action="store_true")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads to use for faster processing", default=1)
    
    args = parser.parse_args()

    # Ensure that -q can only be used if -o is provided
    if args.quiet and not args.output:
        parser.error("The -q option requires -o (output file) to be used.")

    # Split the input domains by comma and remove any extra spaces
    domain_list = [domain.strip() for domain in args.domain.split(',')]

    # Run the script with the provided domains, output file, quiet flag, and threads
    check_domains(domain_list, args.output, args.quiet, args.threads)
