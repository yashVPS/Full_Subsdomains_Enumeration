import requests
import duckdb
import io
import argparse
import re
from tqdm import tqdm

def get_parquet_urls():
    base_url = "https://openintel.nl"
    headers = {'Cookie': 'openintel-data-agreement-accepted=true'}
    
    response = requests.get(f"{base_url}/download/forward-dns/basis%3Dtoplist/source%3Dumbrella/", headers=headers)
    year_urls = re.findall(r"/download/forward-dns/basis=toplist/source=umbrella/year=\d+", response.text)
    
    parquet_urls = []
    
    for year_url in set(year_urls):
        response = requests.get(base_url + year_url, headers=headers)
        month_urls = re.findall(r"/download/forward-dns/basis=toplist/source=umbrella/year=\d+/month=\d+", response.text)
        
        for month_url in set(month_urls):
            response = requests.get(base_url + month_url, headers=headers)
            day_urls = re.findall(r"/download/forward-dns/basis=toplist/source=umbrella/year=\d+/month=\d+/day=\d+", response.text)
            
            for day_url in set(day_urls):
                response = requests.get(base_url + day_url, headers=headers)
                parquet_links = re.findall(r"https://o.*?\.parquet", response.text)
                parquet_urls.extend(parquet_links)
    
    return sorted(parquet_urls, reverse=True)

def download_parquet(url):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('Content-Length', 0))
    file_data = io.BytesIO()
    
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading Parquet") as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            file_data.write(chunk)
            pbar.update(len(chunk))
    
    file_data.seek(0)
    return file_data

def query_parquet(file_data, domains):
    domain_filters = " OR ".join([f"query_name LIKE '%{domain}'" for domain in domains])
    query = f"""
    SELECT DISTINCT(query_name)
    FROM read_parquet(file_data)
    WHERE {domain_filters};
    """
    
    result = duckdb.query(query).fetchall()
    return [row[0].rstrip('.') for row in result]

def main():
    parser = argparse.ArgumentParser(description="Query OpenIntel Parquet Data for Subdomains")
    parser.add_argument("-d", "--domains", required=True, help="Comma-separated list of target domains to search for")
    parser.add_argument("-p", "--parquet", default=None, help="Specific Parquet URL (if not provided, the latest will be used)")
    args = parser.parse_args()
    
    domains = [d.strip() for d in args.domains.split(",")]
    
    if args.parquet:
        parquet_url = args.parquet
    else:
        print("Fetching latest available Parquet file...")
        parquet_urls = get_parquet_urls()
        if not parquet_urls:
            print("No Parquet files found!")
            return
        parquet_url = parquet_urls[0]
        print(f"Using latest Parquet file: {parquet_url}")
    
    parquet_data = download_parquet(parquet_url)
    subdomains = query_parquet(parquet_data, domains)
    
    print("\nExtracted Subdomains:")
    for sub in subdomains:
        print(sub)
    
if __name__ == "__main__":
    main()
