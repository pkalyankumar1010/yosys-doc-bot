import os
import glob
import numpy as np
import pickle
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import requests
import gradio as gr

EMBEDDINGS_FILE = 'semantic_doc_embeddings.pkl'
FAISS_INDEX_FILE = 'semantic_doc_faiss.index'
MODEL_NAME = 'all-MiniLM-L6-v2'
OLLAMA_MODEL = 'mistral'

# Load index and chunks
index = faiss.read_index(FAISS_INDEX_FILE)
with open(EMBEDDINGS_FILE, 'rb') as f:
    data = pickle.load(f)
    chunks = data['chunks']
model = SentenceTransformer(MODEL_NAME)

def ask_ollama(question, context, model=OLLAMA_MODEL):
    prompt = f"""You are a helpful assistant for Yosys documentation.\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            }, timeout=120
        )
        return response.json().get('response', '').strip()
    except Exception as e:
        return f"[LLM ERROR] {e}"

def semantic_llm_chat(user_message, history=None):
    # Semantic search
    q_emb = model.encode([user_message])
    D, I = index.search(np.array(q_emb), k=3)
    top_chunks = []
    for idx in I[0]:
        text, file, section = chunks[idx]
        top_chunks.append(f"Section: {section}\nFile: {file}\n{text}")
    context = '\n\n'.join(top_chunks)
    # LLM answer
    answer = ask_ollama(user_message, context)
    return answer

description = "Yosys LLM Doc Bot: Ask any Yosys/VLSI/EDA question! (Requires Ollama running locally)"
iface = gr.ChatInterface(
    fn=semantic_llm_chat,
    title="Yosys LLM Documentation Chatbot",
    description=description,
    examples=[
        ["How do I use the read_verilog command?"],
        ["What is clock gating?"],
        ["How to debug synthesis errors?"]
    ]
)

if __name__ == "__main__":
    iface.launch() 