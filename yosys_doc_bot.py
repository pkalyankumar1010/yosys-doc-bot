import os
import glob
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh.highlight import UppercaseFormatter

INDEX_DIR = "whoosh_index"

# Define schema for Whoosh
schema = Schema(
    path=ID(stored=True),
    section=TEXT(stored=True),
    content=TEXT(stored=True)
)

def build_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not index.exists_in(INDEX_DIR):
        ix = index.create_in(INDEX_DIR, schema)
    else:
        ix = index.open_dir(INDEX_DIR)
    writer = ix.writer()
    html_files = glob.glob('docs_html/**/*.html', recursive=True)
    print(f'Indexing {len(html_files)} HTML files with Whoosh...')
    for file in tqdm(html_files, desc='Indexing'):
        with open(file, encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            main = soup.find('article') or soup.find('body') or soup
            for header in main.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                section = header.get_text(strip=True)
                texts = []
                for sib in header.next_siblings:
                    if sib.name and sib.name.startswith('h') and len(sib.name) == 2:
                        break
                    if hasattr(sib, 'get_text'):
                        texts.append(sib.get_text(" ", strip=True))
                    elif isinstance(sib, str):
                        texts.append(sib.strip())
                text = ' '.join(texts).strip()
                if text:
                    writer.add_document(path=file, section=section, content=text)
    writer.commit()
    print(f'Whoosh index built with {len(html_files)} files.')

def search_whoosh(query, topn=3):
    ix = index.open_dir(INDEX_DIR)
    qp = MultifieldParser(["section", "content"], schema=ix.schema)
    q = qp.parse(query)
    results = []
    with ix.searcher() as searcher:
        hits = searcher.search(q, limit=topn)
        hits.formatter = UppercaseFormatter()
        for hit in hits:
            snippet = hit.highlights("content", top=2, minscore=1) or hit["content"][:1000]
            results.append({
                "path": hit["path"],
                "section": hit["section"],
                "score": hit.score,
                "snippet": snippet
            })
    return results

if __name__ == '__main__':
    if not os.path.exists(INDEX_DIR) or not index.exists_in(INDEX_DIR):
        build_index()
    else:
        print("Whoosh index found. Skipping indexing.")
    print('Yosys Documentation Bot (Whoosh Search)')
    print('Type your question or error message (or "exit" to quit):')
    while True:
        query = input('> ').strip()
        if query.lower() in ('exit', 'quit'):
            break
        results = search_whoosh(query)
        if not results:
            print('No relevant documentation found.')
        else:
            for r in results:
                print(f'---\nFile: {r["path"]}\nSection: {r["section"]}\nScore: {r["score"]:.2f}\n{r["snippet"]}\n') 