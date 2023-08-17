import argparse
import hashlib
from crawler import crawl

def main():
    parser = argparse.ArgumentParser(description="Bulk Scrape CLI")
    parser.add_argument('--url', type=str, help='Target URL to be crawled')
    parser.add_argument('--shallow', type=str, help='Crawl only the target page')
    parser.add_argument('--persist', type=str, help='Save raw text as .txt files')
    print("*==Bulk Scrape 0.1.0.==*")
    args = parser.parse_args()
    if args.shallow:
        print("Shallow Mode Activated")
    if args.persist:
        print("Persisting Raw Text Files")
    if args.url:
        print(f'Target URL:{args.url}')
    else:
        url = input("Enter your target URL:")
        print(url)
    prompt = input("Enter your target search as a short list of terms. \n (e.g. 'financial advisor Boston MA') ")
    print(prompt)

    df = crawl(url)

if __name__ == '__main__':
    main()