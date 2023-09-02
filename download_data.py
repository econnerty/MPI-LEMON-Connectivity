import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def download_file(url, pbar):
    filename = url.split("/")[-1]

    folder = "pre_mri"
    max_retries = 20
    retries = 0

    if not os.path.exists(folder):
        os.mkdir(folder)

    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"{filename} already exists. Skipping download.")
        pbar.update(1)
        return

    while retries < max_retries:  # Limited retry mechanism
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    print(f"Writing to {filepath}",flush=True)
                    f.write(response.content)
                    print(f"Written to {filepath}")
                pbar.update(1)
                break
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying {filename}...")
            else:
                print(f"Failed to download {filename}. Retrying...")
                
            time.sleep(60)  # Waiting 5 seconds before retrying
        except Exception as e:
            print(f"An error occurred while downloading {filename}: {e}. Retrying...")
        retries += 1
        if retries >= max_retries:
            print(f"Failed to download {filename} after {max_retries} retries.")
            pbar.update(1)

def fetch_urls(page_url):
    raw_data_urls = []
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for i in range(1, 6):
        column_class = f"col{i}-raw"
        for input_tag in soup.find_all('input', {'class': column_class, 'type': 'checkbox'}):
            url = input_tag.get('value')
            if url:
                raw_data_urls.append(url)

    return raw_data_urls

if __name__ == "__main__":
    page_url = "http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON/downloads/download_MRI.html"

    raw_data_urls = fetch_urls(page_url)

    pbar = tqdm(total=len(raw_data_urls))

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.map(lambda url: download_file(url, pbar), raw_data_urls)
