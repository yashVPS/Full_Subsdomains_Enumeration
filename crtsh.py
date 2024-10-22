#!/usr/bin/env python3
import sys, argparse, requests, json

BASE_URL = "https://crt.sh/?q={}&output=json"
subdomains = set()
wildcardsubdomains = set()

def parser_error(errmsg):
    print("Usage: python3 " + sys.argv[0] + " [Options] use -h for help")
    print("Error: " + errmsg)
    sys.exit()

def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython3 ' + sys.argv[0] + " -d google.com,example.com")
    parser.error = parser_error
    parser._optionals.title = "OPTIONS"
    parser.add_argument('-d', '--domain', help='Specify Target Domain(s) to get subdomains from crt.sh (comma-separated for multiple domains)', required=True)
    parser.add_argument('-r', '--recursive', help='Do recursive search for subdomains', action='store_true', required=False)
    parser.add_argument('-w', '--wildcard', help='Include wildcard in output', action='store_true', required=False)
    return parser.parse_args()

def crtsh(domain):
    try:
        print(f"Fetching subdomains for {domain}...")
        response = requests.get(BASE_URL.format(domain), timeout=25)
        if response.ok:
            content = response.content.decode('UTF-8')
            if content.strip():
                jsondata = json.loads(content)
                for i in range(len(jsondata)):
                    name_value = jsondata[i]['name_value']
                    if '\n' in name_value:
                        subname_values = name_value.split('\n')
                        for subname_value in subname_values:
                            if '*' in subname_value:
                                wildcardsubdomains.add(subname_value.strip())
                            else:
                                subdomains.add(subname_value.strip())
                    else:
                        if '*' in name_value:
                            wildcardsubdomains.add(name_value.strip())
                        else:
                            subdomains.add(name_value.strip())
            else:
                print(f"No subdomains found for {domain}.")
        else:
            print(f"Error: Received a non-OK response for {domain}. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching subdomains for {domain}: {e}")

if __name__ == "__main__":
    args = parse_args()
    
    # Handle multiple domains separated by commas
    domains = args.domain.split(',')
    for domain in domains:
        domain = domain.strip()  # Remove any extra spaces
        crtsh(domain)

    # Print subdomains
    if subdomains:
        print("Subdomains found:")
        for subdomain in subdomains:
            print(subdomain)

    # Print wildcard subdomains
    if args.wildcard and wildcardsubdomains:
        print("Wildcard Subdomains found:")
        for wildcardsubdomain in wildcardsubdomains:
            print(wildcardsubdomain)

    # Perform recursive search for wildcard subdomains if enabled
    if args.recursive:
        for wildcardsubdomain in wildcardsubdomains.copy():
            wildcardsubdomain = wildcardsubdomain.replace('*.', '%25.')
            crtsh(wildcardsubdomain)
