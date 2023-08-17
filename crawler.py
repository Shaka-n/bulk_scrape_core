"""
The core crawler module. Key entrypoint is crawl/2. Given a URL, will return a dataframe
containing page text grouped by local urls.

Options:
    - shallow: single page mode. only scrapes the given URL, does not crawl further
    - persist: save scraped text to txt files. for debugging
"""
import requests
import re
import urllib.request
import os
import hashlib
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
import pandas as pd
from urllib.parse import urlparse, quote
from tabulate import tabulate

HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'

class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hyperlinks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a" and "href" in attrs:
            self.hyperlinks.append(attrs["href"]) 

def get_hyperlinks(url):
    try:
        with urllib.request.urlopen(url) as response:
            if not response.info().get('Content-Type').startswith("text/html"):
                return []
            html = response.read().decode('utf-8')
    except Exception as e:
        print(e)
        return []
    parser = HyperlinkParser()
    parser.feed(html)

    return parser.hyperlinks

def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None

        if re.search(HTTP_URL_PATTERN, link):
            # check if the link is within the local domain or goes off-site
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link

        else:
            if link.startswith("/"):
                link = link[1:]
            elif (
                link.startswith("#")
                or link.startswith("mailto:")
                or link.startswith("tel:")
            ):
                continue
            clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)

    return list(set(clean_links))

def crawl(url, **opts):
    local_domain = urlparse(url).netloc
    queue = deque([url])
    seen = set([url])
    persist = opts.get('persist', None)

    if persist:
        if not os.path.exists("text/"):
                os.mkdir("text/")

        if not os.path.exists("text/"+local_domain+"/"):
                os.mkdir("text/"+local_domain+"/")

        if not os.path.exists("processed"):
                os.mkdir("processed")

    df = pd.DataFrame(columns = ['fname', 'text'])
    while queue:
        url = queue.pop()
        print(url)
        fname = 'text/'+local_domain+'/'+url[8:].replace("/", "_") + ".txt"
        # hash url to fit in filename constraints
        if len(fname) > 254:
            fname = shorten_url_to_filename(local_domain, url)
        try:
            request = requests.get(url, timeout=10.000)
            print(request.status_code)
            soup = BeautifulSoup(request.text, "html.parser")
            text = soup.get_text()
        except Exception as e:
            print(e)
            text=f'{e}'

            # Attempt to failsafe if page requires javascript. Might not always work
            if ("You need to enable JavaScript to run this app." in text):
                print("Unable to parse page " + url + " due to JavaScript being required")
        # Append to dataframe
        new_row=pd.DataFrame({'fname': [fname], 'text': [text]}, index=[1])
        df = pd.concat([df, new_row], ignore_index=True)
        if persist:
            with open(fname, "w", encoding="UTF-8") as f:
                f.write(text) 

        # Get the hyperlinks within the current page and add them to the queue
        for link in get_domain_hyperlinks(local_domain, url):
            if link not in seen:
                queue.append(link)
                seen.add(link)
    df['text'] = remove_newlines(df.text)
    if persist:
        df.to_csv('processed/scraped.csv')
    df.head()
    print(tabulate(df, headers='keys'))
    return df

def shorten_url_to_filename(local_domain, url, max_length=50):
    path = url.split("//")[-1].split("/", 1)[-1]
    sha = hashlib.sha256()
    sha.update(url.encode())
    short_hash = sha.hexdigest()[:10]
    
    # Combine domain, a portion of the path, and hash
    filename = 'text/' + local_domain + '/' + path.replace('/', '_')[:20] + '_' + short_hash + ".txt"
    
    # Replace or remove any other characters that might be invalid in filenames
    filename = filename.replace('?', '_').replace('&', '_').replace('=', '_')
    # Enforce the maximum length
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename

def remove_newlines(serie):
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie
