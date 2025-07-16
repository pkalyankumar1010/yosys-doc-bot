import os
import glob
import numpy as np
from tqdm import tqdm
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import requests

EMBEDDINGS_FILE = 'semantic_doc_embeddings.pkl'
FAISS_INDEX_FILE = 'semantic_doc_faiss.index'
MODEL_NAME = 'all-MiniLM-L6-v2'
OLLAMA_MODEL = 'mistral'  # Change to your preferred model if needed

# Only parse and chunk docs if embeddings/index do not exist
if not os.path.exists(EMBEDDINGS_FILE) or not os.path.exists(FAISS_INDEX_FILE):
    print('Parsing and chunking documentation...')
    chunks = []  # List of (chunk_text, file, section)
    html_files = glob.glob('docs_html/**/*.html', recursive=True)
    for file in tqdm(html_files, desc='Chunking'):
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
                    chunks.append((text, file, section))
    print(f'Total chunks: {len(chunks)}')
    print('Generating embeddings and building FAISS index...')
    model = SentenceTransformer(MODEL_NAME)
    texts = [c[0] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    faiss.write_index(index, FAISS_INDEX_FILE)
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump({'chunks': chunks}, f)
    print('Embeddings and index saved.')
else:
    print('Loading existing embeddings and FAISS index...')
    index = faiss.read_index(FAISS_INDEX_FILE)
    with open(EMBEDDINGS_FILE, 'rb') as f:
        data = pickle.load(f)
        chunks = data['chunks']

# LLM answer generation with Ollama
def ask_ollama(question, context, model=OLLAMA_MODEL):
    prompt = f"""You are a helpful assistant for Yosys documentation.\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"""
    print("[DEBUG] Sending prompt to Ollama:")
    print(prompt[:1000] + ("..." if len(prompt) > 1000 else ""))
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            }, timeout=120
        )
        print(f"[DEBUG] Ollama raw response: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")
        return response.json().get('response', '').strip()
    except Exception as e:
        print(f"[DEBUG] LLM Exception: {e}")
        return f"[LLM ERROR] {e}"

# Query interface
model = SentenceTransformer(MODEL_NAME)
print('Semantic Yosys Documentation Bot + LLM')
print('Type your question or error message (or "exit" to quit):')
while True:
    query = input('> ').strip()
    if query.lower() in ('exit', 'quit'):
        break
    q_emb = model.encode([query])
    D, I = index.search(np.array(q_emb), k=3)
    top_chunks = []
    for idx in I[0]:
        text, file, section = chunks[idx]
        print(f'---\nFile: {file}\nSection: {section}\n{text[:500]}...\n')
        top_chunks.append(f"Section: {section}\nFile: {file}\n{text}")
    context = '\n\n'.join(top_chunks)
    print("[LLM Answer]")
    answer = ask_ollama(query, context)
    print(answer) 