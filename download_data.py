import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def download_file(url):
    filename = url.split("/")[-1]
    folder = "pre_mri"

    if not os.path.exists(folder):
        os.mkdir(folder)

    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"{filename} already exists. Skipping download.")
        return

    while True:  # Keep trying indefinitely
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {filename}")
                break  # Exit the while loop once downloaded
            elif response.status_code == 429:
                print(f"Rate limit exceeded. Retrying {filename}...")
            else:
                print(f"Failed to download {filename}. Retrying...")
                
            time.sleep(5)  # Waiting 5 seconds before retrying
        except Exception as e:
            print(f"An error occurred while downloading {filename}: {e}. Retrying...")

def fetch_urls(page_url):
    raw_data_urls = []
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # You mentioned the class name can be up to 5 columns, so the range is 1 to 6.
    for i in range(1, 6):
        column_class = f"col{i}-preproc"  # Adjust based on the actual class names in your HTML.
        for input_tag in soup.find_all('input', {'class': column_class, 'type': 'checkbox'}):
            url = input_tag.get('value')
            if url:
                raw_data_urls.append(url)
            
    return raw_data_urls

if __name__ == "__main__":
    page_url = "http://fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON/downloads/download_MRI.html"  # Replace with the actual URL of the page containing MRI data

    raw_data_urls = fetch_urls(page_url)

    # Use tqdm to display a progress bar
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(tqdm(executor.map(download_file, raw_data_urls), total=len(raw_data_urls)))
