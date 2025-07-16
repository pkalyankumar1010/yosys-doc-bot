# Yosys LLM Documentation Bot

A local, open-source chatbot for Yosys, VLSI, and EDA documentation! Combines semantic search (using Sentence Transformers + FAISS) with LLM-powered answers (via Ollama) and offers both CLI and web-based chat interfaces.

---

## Features

- **Semantic search** over all Yosys and related EDA documentation (local HTML dump)
- **LLM-powered answers** using a local model (e.g., Mistral, Llama) via [Ollama](https://ollama.com/)
- **Fast, context-aware results** thanks to vector search (FAISS)
- **Two interfaces:**
  - Command-line (CLI)
  - Web-based chat (Gradio)
- **Fully local & private** (no cloud APIs required)

---

## Requirements

- Python 3.8+
- pip
- [Ollama](https://ollama.com/) (for local LLM)

**Python packages:**

- `sentence-transformers`
- `faiss-cpu`
- `tqdm`
- `beautifulsoup4`
- `requests`
- `gradio`

Install all requirements:

```bash
pip install -r requirements.txt
```

---

## Setup

### 1. Download Yosys Documentation

- Use the provided script to recursively download all Yosys and related docs as HTML into `docs_html/`.

### 2. Build Semantic Index

- The first run of the bot will parse, chunk, and embed the docs, building a FAISS index for fast search.
- This step may take several minutes, but only runs once (unless docs change).

### 3. Set Up Ollama

- [Download and install Ollama](https://ollama.com/download)
- Pull a model (e.g., Mistral):
  ```bash
  ollama pull mistral
  ollama serve
  ```

---

## Usage

### Command-Line Interface

```bash
python semantic_yosys_doc_bot.py
```

- Type your Yosys/EDA question or error message.
- The bot will show relevant doc chunks and an LLM-generated answer.

### Web Chat Interface

```bash
python yosys_doc_webui.py
```

- Open the local URL (usually http://127.0.0.1:7860) in your browser.
- Chat with the bot in a modern web UI!

---

## Troubleshooting

- **Ollama connection errors:**
  - Make sure `ollama serve` is running and a model is pulled.
  - Test with: `curl http://localhost:11434`
- **Slow startup:**
  - The first run parses and embeds all docs. Subsequent runs are instant.
- **No results:**
  - Try rephrasing your question or check that the docs were downloaded correctly.

---

## Customization

- Change the LLM model by editing the `OLLAMA_MODEL` variable in the scripts.
- Add more documentation by placing additional HTML files in `docs_html/` and deleting the index/embeddings files to force a rebuild.

---

## Credits

- [YosysHQ](https://yosyshq.readthedocs.io/) for the documentation
- [Ollama](https://ollama.com/) for local LLM serving
- [Gradio](https://gradio.app/) for the web UI
- [Sentence Transformers](https://www.sbert.net/) and [FAISS](https://faiss.ai/) for semantic search

---

## License

This project is open source and provided as-is for educational and research purposes.
