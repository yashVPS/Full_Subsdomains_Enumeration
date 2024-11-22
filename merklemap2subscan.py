import requests
import argparse
import time
import random

def fetch_subdomains(domain):
    base_url = "https://api.merklemap.com/search"
    page = 0
    subdomains = []
    
    while True:
        params = {"query": f"*.{domain}", "page": page}
        try:
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                print(f"[Error] Failed to fetch page {page} for domain {domain}. HTTP Status Code: {response.status_code}")
                break
            
            data = response.json()
            results = data.get("results", [])
            if not results:  # Break if results are empty (end of data)
                break
            
            for entry in results:
                subdomain = entry.get("domain")
                if subdomain:
                    subdomains.append(subdomain)
            
            print(f"[Info] Fetched page {page} for domain {domain}. Subdomains count: {len(subdomains)}")
            page += 1
            
            # Random delay between 15 to 17 seconds
            delay = random.randint(15, 17)
            print(f"[Info] Waiting for {delay} seconds before the next request...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"[Error] Exception occurred: {e}")
            break
    
    return subdomains

def main():
    parser = argparse.ArgumentParser(description="MerkleMap Subdomain Extractor")
    parser.add_argument("-d", "--domains", type=str, required=True, help="Comma-separated list of domains to fetch subdomains for")
    parser.add_argument("-o", "--output", type=str, default="subdomains_output.txt", help="Output file name (default: subdomains_output.txt)")
    args = parser.parse_args()

    domains = args.domains.split(",")
    all_subdomains = []

    for domain in domains:
        domain = domain.strip()
        if not domain:
            continue
        print(f"[Info] Fetching subdomains for: {domain}")
        subdomains = fetch_subdomains(domain)
        all_subdomains.extend(subdomains)  # Flattening the list of subdomains

    # Save subdomains to specified output file
    with open(args.output, "w") as f:
        for subdomain in all_subdomains:
            f.write(f"{subdomain}\n")  # Write each subdomain on a new line

    print(f"[Info] Subdomains saved to {args.output}")

if __name__ == "__main__":
    main()
