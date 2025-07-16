import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

base_url = 'https://yosyshq.readthedocs.io/en/latest/'
start_pages = [
    'index.html',
    'install.html',
    'licensing.html',
    'tools.html',
    'appnotes.html',
]
download_dir = 'docs_html'
os.makedirs(download_dir, exist_ok=True)

visited = set()

# Map documentation root URLs to local subfolders
root_map = {
    'https://yosyshq.readthedocs.io/en/latest/': '',
}

def get_local_path(url, root_url):
    parsed = urlparse(url)
    rel_path = parsed.path.lstrip('/')
    if rel_path == '' or rel_path.endswith('/'):
        rel_path += 'index.html'
    subfolder = root_map[root_url]
    return os.path.join(download_dir, subfolder, rel_path)

def download_page(url, root_url):
    if url in visited:
        return
    visited.add(url)
    local_path = get_local_path(url, root_url)
    local_folder = os.path.dirname(local_path)
    os.makedirs(local_folder, exist_ok=True)
    print(f'Downloading {url} -> {local_path}')
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Failed to download {url}')
        return
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Internal relative links
        if href.endswith('.html') and not href.startswith('http'):
            next_url = urljoin(url, href)
            download_page(next_url, root_url)
        # External documentation links
        elif href.startswith('http') and 'readthedocs.io' in href:
            # Only follow documentation links (not blogs, etc.)
            if href.endswith('.html') or href.endswith('/'):
                # Determine the root for this doc set
                parsed = urlparse(href)
                doc_root = href.split(parsed.path)[0] + parsed.path.split('/')[1] + '/'
                # Use the first two path segments as the root (e.g., /en/latest/)
                if 'readthedocs.io/projects/' in href:
                    # e.g., https://yosyshq.readthedocs.io/projects/sby/en/latest/
                    parts = href.split('/')
                    idx = parts.index('projects')
                    doc_root = '/'.join(parts[:idx+3]) + '/'
                    subfolder = parts[idx+1]
                else:
                    # e.g., https://yosys.readthedocs.io/en/latest/
                    parts = href.split('/')
                    idx = parts.index('en') if 'en' in parts else -1
                    doc_root = '/'.join(parts[:idx+2]) + '/' if idx != -1 else href
                    subfolder = urlparse(href).netloc.split('.')[0]
                if doc_root not in root_map:
                    root_map[doc_root] = subfolder
                # Recursively download from this new root
                download_page(href, doc_root)

# Start crawling from the main YosysHQ docs
for page in start_pages:
    url = urljoin(base_url, page)
    download_page(url, base_url) 